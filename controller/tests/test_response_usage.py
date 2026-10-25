# Synthetic usage fixtures; no account or provider billing records.
import copy
import datetime
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'bridge'))
from response_usage import ResponseUsageReader
from usage_meter import UsageLedger, estimate, plus, zero
from test_usage_ledger import MODEL, BOOK, tokens, value

THREAD = '11111111-1111-1111-1111-111111111111'


def record(identifier, usage, at=2000, turn='turn'):
    return {'id': hashlib.sha256(identifier.encode()).hexdigest(), 'thread': THREAD,
            'turn': turn, 'model': MODEL, 'at': at, 'usage': usage}


class ReconciliationTests(unittest.TestCase):
    def test_compaction_missing_from_regular_event_is_counted_once(self):
        normal = tokens(12000, 8000, 500, 100)
        compact = tokens(6000, 4000, 200, 0)
        m = UsageLedger();m.reset_at = 1000
        m.observe(value(normal, normal, thread=THREAD), MODEL)
        records = [record('normal', normal), record('compaction', compact)]
        self.assertTrue(m.observe_responses(records))
        self.assertFalse(m.observe_responses(records))
        view = m.view(THREAD, 'turn', MODEL, BOOK)
        self.assertEqual(view['usage']['last'], plus(normal, compact))
        self.assertEqual(view['usage']['total'], plus(normal, compact))
        self.assertEqual(view['usage']['recovered_tokens'], 6200)
        self.assertAlmostEqual(view['cost']['total'], .003636)
        # A duplicate regular replay never adds the record total twice.
        m.observe(value(normal, normal, thread=THREAD), MODEL)
        self.assertEqual(m.view(THREAD, 'turn', MODEL, BOOK)['usage']['total'], plus(normal, compact))

    def test_lagging_record_file_never_rolls_back_live_notification(self):
        a=tokens();b=tokens(600,200,100,10);m=UsageLedger();m.reset_at=1000
        m.observe(value(plus(a,b),plus(a,b),thread=THREAD),MODEL)
        m.observe_responses([record('a',a)])
        self.assertEqual(m.view(THREAD,'turn',MODEL,BOOK)['usage']['last'],plus(a,b))
        m.observe_responses([record('b',b)])
        self.assertEqual(m.view(THREAD,'turn',MODEL,BOOK)['usage']['last'],plus(a,b))

    def test_clear_replay_and_restart_do_not_resurrect_old_records(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'ledger.json';m=UsageLedger(p);m.reset_at=1000
            m.observe_responses([record('a',tokens())]);m.save()
            m=UsageLedger(p)
            self.assertFalse(m.observe_responses([record('a',tokens())]))
            self.assertTrue(m.clear(m.reset_id))
            m.observe_responses([record('a',tokens()),record('new',tokens(),at=m.reset_at+1)])
            self.assertEqual(m.view(THREAD,'turn',MODEL,BOOK)['usage']['total'],tokens())
            m=UsageLedger(p)
            self.assertEqual(m.view(THREAD,'turn',MODEL,BOOK)['usage']['total'],tokens())

    def test_different_turns_models_and_background_threads_stay_separate(self):
        m=UsageLedger();m.reset_at=1000
        a=record('a',tokens());b=record('b',tokens(),turn='second');b['model']='other-model'
        m.observe_responses([a,b])
        view=m.view(THREAD,'second','other-model',BOOK)
        self.assertEqual(view['usage']['last'],tokens())
        self.assertAlmostEqual(view['cost']['total'],
            estimate(tokens(),BOOK['models'][MODEL])+estimate(tokens(),BOOK['models']['other-model']))

    def test_reset_boundary_excludes_earlier_completion(self):
        m=UsageLedger();m.reset_at=2000.5
        m.observe_responses([record('before',tokens(),2000.4),record('after',tokens(),2000.6)])
        self.assertEqual(m.view(THREAD,'turn',MODEL,BOOK)['usage']['total'],tokens())

    def test_missed_event_across_turn_boundary_is_not_counted_twice(self):
        a=tokens();b=tokens(600,200,100,10);c=tokens(800,400,90,20)
        m=UsageLedger();m.reset_at=1000
        m.observe(value(a,a,thread=THREAD),MODEL)
        # b was not delivered live. The next turn's cumulative delta includes b.
        m.observe(value(plus(plus(a,b),c),c,thread=THREAD,turn='second'),MODEL)
        m.observe_responses([record('a',a),record('b',b),record('c',c,turn='second')])
        self.assertEqual(m.view(THREAD,'second',MODEL,BOOK)['usage']['total'],plus(plus(a,b),c))
        self.assertEqual(m.view(THREAD,'turn',MODEL,BOOK)['usage']['last'],plus(a,b))

    def test_v1_ledger_is_read_without_modifying_existing_private_file(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'ledger.json';m=UsageLedger(p);m.observe(value(),MODEL)
            saved=json.loads(p.read_text());saved['version']=1
            saved.pop('response_turns');saved.pop('response_ids');p.write_text(json.dumps(saved))
            before=p.read_text();m=UsageLedger(p)
            self.assertFalse(m.blocked);self.assertEqual(m.aggregate(m.groups),tokens())
            self.assertEqual(p.read_text(),before)


class ReaderTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);directory=self.root/'2026/10/26';directory.mkdir(parents=True)
        self.path=directory/('rollout-2026-10-26T00-00-00-'+THREAD+'.jsonl')
        self.reader=ResponseUsageReader(self.root)
        self.append({'type':'session_meta','payload':{'id':THREAD}})
        self.append({'type':'turn_context','payload':{'turn_id':'turn','model':MODEL}})

    def append(self, value, newline=True):
        with self.path.open('a') as f:f.write(json.dumps(value)+('\n' if newline else ''))

    def usage(self, identifier='response'):
        return {'type':'token_usage_record','timestamp':'2026-10-26T00:00:00+11:00','payload':{
            'thread_id':THREAD,'turn_id':'turn','response_id':identifier,
            'usage':{'input_tokens':1000,'cached_input_tokens':200,'output_tokens':300,
                     'reasoning_output_tokens':100,'total_tokens':1300}}}

    def test_incremental_numeric_records_and_partial_append(self):
        self.append({'type':'response_item','payload':{'text':'private text is not returned'}})
        self.append(self.usage(),newline=False)
        self.assertEqual(self.reader.read([THREAD]),[])
        with self.path.open('a') as f:f.write('\n')
        records=self.reader.read([THREAD]);self.assertEqual(len(records),1)
        self.assertEqual(records[0]['usage'],tokens());self.assertEqual(records[0]['model'],MODEL)
        self.assertNotIn('private text',json.dumps(records))
        self.assertEqual(self.reader.read([THREAD]),[])

    def test_paths_identity_and_malformed_usage_are_rejected(self):
        self.assertEqual(self.reader.read(['../../secret']),[])
        bad=self.usage();bad['payload']['usage']['total_tokens']=999
        self.append(bad);self.assertEqual(self.reader.read([THREAD]),[])
        self.append({'type':'session_meta','payload':{'id':'different'}})
        self.append(self.usage());self.assertEqual(self.reader.read([THREAD]),[])

    def test_file_truncation_restarts_without_losing_model_context(self):
        self.append(self.usage());self.assertEqual(len(self.reader.read([THREAD])),1)
        self.path.write_text('')
        self.append({'type':'session_meta','payload':{'id':THREAD}})
        self.append(self.usage('b'))
        records=self.reader.read([THREAD]);self.assertEqual(records[0]['model'],'')


if __name__=='__main__':unittest.main()
