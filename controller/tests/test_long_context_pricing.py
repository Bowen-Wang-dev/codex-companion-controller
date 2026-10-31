"""Synthetic requests exercise price boundaries, reconciliation and upgrades."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bridge'))
from usage_meter import UsageLedger,estimate,load_rates,plus
from test_usage_ledger import MODEL,tokens,value

CARD={'input':.36,'cached_input':.018,'output':1.8,'cache_write':.45,
 'long_context':{'above_input_tokens':272000,'input':.72,'cached_input':.036,'output':2.7,'cache_write':.90}}
BOOK={'currency':'USD','models':{MODEL:CARD}}


def record(name,usage,turn='turn'):
    return {'id':hashlib.sha256(name.encode()).hexdigest(),'thread':'thread','turn':turn,
            'model':MODEL,'usage':usage,'at':100}


class LongPricingTests(unittest.TestCase):
    def test_price_multiplier_is_once_and_defaults_to_one(self):
        value=tokens(1000,200,300,100)
        custom={'input':2,'cached_input':.2,'output':8,'cache_write':1,'multiplier':.5}
        parts=__import__('usage_meter').estimate_breakdown(value,custom)
        self.assertEqual(parts['uncached_input_tokens'],800)
        self.assertEqual(parts['visible_output_tokens'],200)
        self.assertEqual(parts['reasoning_tokens'],100)
        self.assertAlmostEqual(parts['uncached_input'],.0008)
        self.assertAlmostEqual(parts['cached_input'],.00002)
        self.assertAlmostEqual(parts['visible_output'],.0008)
        self.assertAlmostEqual(parts['reasoning'],.0004)
        self.assertAlmostEqual(parts['total'],.00202)
        self.assertAlmostEqual(__import__('usage_meter').estimate(value,{'input':2,'cached_input':.2,'output':8,'cache_write':1}),.00404)

    def test_openai_profile_preset_and_multiplier(self):
        import json
        from usage_meter import OPENAI_PRICES,load_rates
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'rates.json'
            p.write_text(json.dumps({'currency':'USD','models':{MODEL:{'rate_source':'openai','multiplier':.18}}}))
            rates=load_rates(p)['models'][MODEL]
        self.assertEqual(rates['input'],2.0);self.assertEqual(rates['long_context']['input'],4.0)
        self.assertEqual(rates['multiplier'],.18)
        self.assertEqual(rates['long_context']['output'],OPENAI_PRICES[MODEL]['long_context']['output'])
        normal=tokens(1000,200,300,100)
        long=tokens(300000,290000,300,100)
        self.assertAlmostEqual(__import__('usage_meter').estimate(normal,rates),
            ((800*2+200*.1+300*10)*.18)/1e6)
        self.assertAlmostEqual(__import__('usage_meter').estimate(long,rates),
            ((10000*4+290000*.2+300*rates['long_context']['output'])*.18)/1e6)

    def test_priced_components_sum_once_and_report_reasoning_separately(self):
        from usage_meter import UsageLedger
        value_=tokens(1000,200,300,100)
        groups={MODEL:value_}
        details,issue=UsageLedger.cost_details(groups,BOOK,MODEL)
        self.assertEqual(issue,'')
        self.assertEqual(details['uncached_input_tokens'],800)
        self.assertEqual(details['visible_output_tokens'],200)
        self.assertEqual(details['reasoning_tokens'],100)
        self.assertAlmostEqual(details['output_total'],details['visible_output']+details['reasoning'])
        self.assertAlmostEqual(details['total'],((800*.36)+(200*.018)+(200*1.8)+(100*1.8))/1e6)

    def test_exact_threshold_uses_normal_above_uses_long_for_whole_request(self):
        a=tokens(272000,200000,100,10);b=tokens(272001,200000,100,10)
        self.assertAlmostEqual(estimate(a,CARD),(72000*.36+200000*.018+100*1.8)/1e6)
        self.assertAlmostEqual(estimate(b,CARD),(72001*.72+200000*.036+100*2.7)/1e6)

    def test_output_does_not_choose_tier_and_reasoning_not_added_twice(self):
        a=tokens(271900,0,10000,9000)
        self.assertAlmostEqual(estimate(a,CARD),(271900*.36+10000*1.8)/1e6)

    def test_cache_alone_can_cross_threshold_and_writes_have_separate_rate(self):
        a=tokens(300000,295000,100,0);a['cacheWriteInputTokens']=5000
        self.assertAlmostEqual(estimate(a,CARD),(295000*.036+5000*.90+100*2.7)/1e6)

    def test_many_short_requests_are_not_repriced_as_one_long_request(self):
        a=tokens(160000,100000,100,0);m=UsageLedger();m.reset_at=0
        m.observe(value(a,a),MODEL);m.observe(value(plus(a,a),a),MODEL)
        self.assertAlmostEqual(m.view('thread','turn',MODEL,BOOK)['cost']['last'],2*estimate(a,CARD))

    def test_mixed_tiers_survive_restart_replay_reset_and_failed_reset(self):
        a=tokens(180000,170000,100,0);b=tokens(300000,290000,100,0)
        records=[record('a',a),record('b',b)]
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'ledger.json';m=UsageLedger(path);m.reset_at=0
            m.observe(value(a,a),MODEL)
            m.observe_responses(records);expected=estimate(a,CARD)+estimate(b,CARD)
            self.assertAlmostEqual(m.view('thread','turn',MODEL,BOOK)['cost']['total'],expected)
            m=UsageLedger(path);self.assertFalse(m.observe_responses(records))
            self.assertAlmostEqual(m.view('thread','turn',MODEL,BOOK)['cost']['last'],expected)
            with mock.patch.object(m,'save',return_value=False):self.assertFalse(m.clear(m.reset_id))
            self.assertAlmostEqual(m.view('thread','turn',MODEL,BOOK)['cost']['total'],expected)
            self.assertTrue(m.clear(m.reset_id));m.observe_responses(records)
            self.assertEqual(m.pricing_requests,{'app':{},'response':{},'provider':{}})
            self.assertEqual(m.view('thread','turn',MODEL,BOOK)['cost']['total'],0)

    def test_legacy_aggregate_is_unknown_until_numeric_response_replay_repairs_it(self):
        a=tokens(300000,290000,100,0);r=record('legacy',a)
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'ledger.json';m=UsageLedger(p);m.reset_at=0;m.observe_responses([r])
            saved=json.loads(p.read_text());saved.pop('pricing_requests');p.write_text(json.dumps(saved))
            m=UsageLedger(p);before=m.view('thread','turn',MODEL,BOOK)
            self.assertIsNone(before['cost']['total']);self.assertEqual(before['cost']['status'],'request_boundaries_missing')
            self.assertTrue(m.observe_responses([r]));after=m.view('thread','turn',MODEL,BOOK)
            self.assertEqual(after['usage']['total'],before['usage']['total'])
            self.assertAlmostEqual(after['cost']['total'],estimate(a,CARD))

    def test_missing_multiple_events_does_not_guess_a_single_context(self):
        a=tokens(100000,50000,100,0);m=UsageLedger();m.observe(value(a,a),MODEL)
        m.observe(value(plus(plus(a,a),a),a),MODEL)
        self.assertIsNone(m.view('thread','turn',MODEL,BOOK)['cost']['total'])

    def test_provider_supplement_then_late_local_record_is_not_double_priced(self):
        a=tokens(100000,50000,100,0);b=tokens(300000,290000,100,0)
        m=UsageLedger();m.reset_at=0;m.observe_responses([record('one',a)])
        m.reconcile_provider([record('provider',b)])
        expected=estimate(a,CARD)+estimate(b,CARD)
        self.assertAlmostEqual(m.view('thread','turn',MODEL,BOOK)['cost']['total'],expected)
        m.observe_responses([record('late',b)]);m.reconcile_provider([])
        self.assertAlmostEqual(m.view('thread','turn',MODEL,BOOK)['cost']['total'],expected)

    def test_invalid_tier_never_silently_falls_back_to_standard(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'rates.json'
            for invalid in ({},dict(CARD['long_context'],above_input_tokens=True),dict(CARD['long_context'],output=-1)):
                card=copy.deepcopy(CARD);card['long_context']=invalid
                p.write_text(json.dumps({'currency':'USD','models':{MODEL:card}}))
                self.assertNotIn(MODEL,load_rates(p)['models'])
            p.write_text(json.dumps(BOOK));loaded=load_rates(p)
            self.assertEqual(loaded['currency'],'USD');self.assertIn(MODEL,loaded['models'])
            self.assertEqual(loaded['models'][MODEL]['multiplier'],1.0)


if __name__=='__main__':unittest.main()
