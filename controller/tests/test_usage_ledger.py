import io
import json
from pathlib import Path
import sys
import tempfile
import time
import socketserver
import threading
import unittest
from unittest import mock
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'bridge'))
from usage_meter import UsageLedger, plus, zero, normalize_notification, rate_for, estimate
from service import Broker
import service
from stdio_relay import Relay
import meter_client

MODEL = 'gpt-6.1-sol'
BOOK = {'currency': 'USD', 'models': {MODEL: {'input': .36, 'cached_input': .018, 'output': 1.8, 'cache_write': None},
    'other-model': {'input': 2, 'cached_input': .2, 'output': 8, 'cache_write': None}}}

def tokens(i=1000, cached=200, o=300, reasoning=100):
    return dict(inputTokens=i, cachedInputTokens=cached, cacheWriteInputTokens=0,
                outputTokens=o, reasoningOutputTokens=reasoning, totalTokens=i+o)

def value(total=None, last=None, thread='thread', turn='turn'):
    return {'thread': thread, 'turn': turn, 'total': total or tokens(), 'last': last or tokens(), 'context_window': 475000}

def event(kind, **fields):
    return {'kind':kind,'relay':'relay','sessions':['thread','background'],'thread':'thread',**fields}

class LedgerTests(unittest.TestCase):
    def test_replay_recovers_a_missed_final_delta_but_never_twice(self):
        m=UsageLedger();m.observe(value(),MODEL)
        b=tokens(500,100,100,30)
        update=value(plus(tokens(),b),b)
        self.assertTrue(m.observe(update,MODEL,baseline_only=True))
        self.assertFalse(m.observe(update,MODEL,baseline_only=True))
        self.assertEqual(m.aggregate(m.groups),plus(tokens(),b))

    def test_resume_snapshot_only_establishes_baseline(self):
        m=UsageLedger();m.observe(value(),MODEL,baseline_only=True)
        self.assertEqual(m.aggregate(m.groups),zero())
        self.assertFalse(m.observe(value(),MODEL))
        b=tokens(500,100,100,30)
        m.observe(value(plus(tokens(),b),b),MODEL)
        self.assertEqual(m.aggregate(m.groups),b)

    def test_cache_write_replaces_ordinary_input_price(self):
        t=tokens(100,40,10,0);t['cacheWriteInputTokens']=60
        rates={'input':2,'cached_input':.2,'output':8,'cache_write':1}
        self.assertAlmostEqual(estimate(t,rates),(40*.2+60*1+10*8)/1e6)

    def test_multithread_interleaving_preserves_each_baseline(self):
        m=UsageLedger();m.observe(value(thread='a'),MODEL)
        m.observe(value(thread='b'),'other-model');m.observe(value(thread='a'),MODEL)
        self.assertEqual(m.aggregate(m.groups),plus(tokens(),tokens()))

    def test_first_event_is_not_entire_old_history(self):
        m=UsageLedger();m.observe(value(tokens(100000,50000,20000),tokens()),MODEL)
        self.assertEqual(m.view('thread','turn',MODEL,BOOK)['usage']['total'],tokens())

    def test_same_turn_sums_multiple_responses_and_duplicates_once(self):
        m=UsageLedger();m.observe(value(),MODEL)
        second=tokens(500,100,100,30);total=plus(tokens(),second)
        m.observe(value(total,second),MODEL);self.assertFalse(m.observe(value(total,second),MODEL))
        view=m.view('thread','turn',MODEL,BOOK)
        self.assertEqual(view['usage']['last'],total)
        expected=((1500-300)*.36+300*.018+400*1.8)/1e6
        self.assertAlmostEqual(view['cost']['last'],expected)

    def test_new_turn_zero_then_counts_only_new_response(self):
        m=UsageLedger();m.observe(value(),MODEL);m.begin_turn('thread','two')
        self.assertEqual(m.view('thread','two',MODEL,BOOK)['usage']['last'],zero())
        second=tokens(500,100,100,30);m.observe(value(plus(tokens(),second),second,turn='two'),MODEL)
        self.assertEqual(m.view('thread','two',MODEL,BOOK)['usage']['last'],second)

    def test_reset_replay_and_restart_keep_baseline(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'meter.json';m=UsageLedger(p);m.observe(value(),MODEL)
            old=m.reset_id;self.assertTrue(m.clear(old));self.assertFalse(m.clear(old))
            m=UsageLedger(p);self.assertFalse(m.observe(value(),MODEL))
            self.assertEqual(m.view('thread','turn',MODEL,BOOK)['usage']['total'],zero())
            second=tokens(500,100,100,30);m.observe(value(plus(tokens(),second),second),MODEL)
            self.assertEqual(m.view('thread','turn',MODEL,BOOK)['usage']['total'],second)
            self.assertEqual(p.stat().st_mode & 0o777,0o600)

    def test_mixed_models_are_not_repriced_with_latest_model(self):
        m=UsageLedger();m.observe(value(),MODEL);b=tokens(500,100,100,30)
        m.observe(value(plus(tokens(),b),b), 'other-model')
        view=m.view('thread','turn','other-model',BOOK)
        first=((1000-200)*.36+200*.018+300*1.8)/1e6
        second=((500-100)*2+100*.2+100*8)/1e6
        self.assertAlmostEqual(view['cost']['total'],first+second)

    def test_out_of_order_event_does_not_move_baseline_backwards(self):
        m=UsageLedger();m.observe(value(),MODEL);b=tokens(500,100,100,30)
        m.observe(value(plus(tokens(),b),b),MODEL);self.assertFalse(m.observe(value(),MODEL))
        self.assertEqual(m.view('thread','turn',MODEL,BOOK)['usage']['total'],plus(tokens(),b))

    def test_missing_model_prices_and_cache_write_are_explicit(self):
        m=UsageLedger();m.observe(value(),'unknown')
        self.assertEqual(m.view('thread','turn','unknown',BOOK)['cost']['status'],'model_rate_missing')
        m=UsageLedger();a=tokens();a['cacheWriteInputTokens']=20;m.observe(value(a,a),MODEL)
        self.assertEqual(m.view('thread','turn',MODEL,BOOK)['cost']['status'],'cache_write_rate_missing')

    def test_corrupt_ledger_is_not_silently_overwritten(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'meter.json';p.write_text('broken');m=UsageLedger(p)
            self.assertFalse(m.observe(value(),MODEL));self.assertEqual(p.read_text(),'broken')

    def test_persistence_failure_does_not_confirm_reset(self):
        m=UsageLedger();m.observe(value(),MODEL);old=m.reset_id
        with mock.patch.object(m,'save',return_value=False):self.assertFalse(m.clear(old))
        self.assertEqual(m.reset_id,old);self.assertEqual(m.aggregate(m.groups),tokens())

    def test_counterless_context_fill_is_not_spend(self):
        bad=tokens();bad['totalTokens']=475000
        self.assertIsNone(normalize_notification({'threadId':'thread','turnId':'turn','tokenUsage':{'last':bad,'total':bad}}))

    def test_no_fuzzy_model_price_substitution(self):
        self.assertIsNone(rate_for(BOOK,MODEL+'-fast'))
        self.assertEqual(rate_for(BOOK,' GPT-6.1-SOL '),BOOK['models'][MODEL])

class BrokerMeterTests(unittest.TestCase):
    def test_local_ipc_status_and_reset_survive_real_transport(self):
        b=Broker();b.meter.observe(value(),MODEL)
        class Handler(socketserver.StreamRequestHandler):
            def handle(self):
                message=json.loads(self.rfile.readline())
                response=b.status() if message['type']=='status' else b.clear_meter(message)
                self.wfile.write(json.dumps(response).encode()+b'\n')
        with tempfile.TemporaryDirectory(dir='/private/tmp') as directory:
            path=Path(directory)/'meter.sock'
            with socketserver.UnixStreamServer(str(path),Handler) as server:
                thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
                try:
                    with mock.patch.object(meter_client,'check_directory',return_value=path):
                        status=meter_client.request({'type':'status'})
                        result=meter_client.request({'type':'meter_reset',
                            'meter_id':status['metering']['usage']['meter_id']})
                        self.assertTrue(result['cleared'])
                        self.assertEqual(meter_client.request({'type':'status'})['metering']['usage']['total'],zero())
                finally:server.shutdown();thread.join()

    def test_periodic_replay_carries_numeric_baseline_only(self):
        class Child:stdin=io.BytesIO()
        relay=Relay(Child(),io.BytesIO(),io.BytesIO());relay.sessions.add('thread')
        relay.models['thread']=MODEL
        relay.latest_usage['thread']={'kind':'token_usage','thread':'thread','turn':'turn',
            'usage':{'total':tokens(),'last':tokens()},'model':MODEL}
        sent=[]
        def ipc(message):
            sent.append(message)
            if message.get('kind')=='token_usage':relay.stopping.set()
            return {}
        relay.ipc=ipc;relay.event({'kind':'heartbeat'});relay.event_worker()
        usage=next(x for x in sent if x.get('kind')=='token_usage')
        self.assertIs(usage['baseline_only'],True)

    def test_replayed_usage_model_does_not_undo_newer_selection(self):
        b=Broker();b.desktop_event(event('model_update',model='other-model'))
        b.desktop_event(event('token_usage',turn='turn',model=MODEL,
            usage={'last':tokens(),'total':tokens()}))
        self.assertEqual(b.active_model,'other-model')
        self.assertIn(MODEL,b.meter.groups)

    def test_rates_hot_reload_and_precise_waiting_status(self):
        with tempfile.TemporaryDirectory() as d,mock.patch.object(service,'ROOT',Path(d)):
            p=Path(d)/'private';p.mkdir();(p/'token_rates.json').write_text(json.dumps(BOOK))
            b=Broker();b.desktop_event(event('model_update',model=MODEL))
            s=b.snapshot();self.assertTrue(s['token_cost']['priced'])
            self.assertEqual(s['token_cost']['status'],'waiting_usage')
            b.desktop_event(event('token_usage',turn='turn',model=MODEL,
                usage={'last':tokens(),'total':tokens()}))
            before=b.snapshot()['token_cost']['last'];self.assertIsNotNone(before)
            book=json.loads(json.dumps(BOOK));book['models'][MODEL]['output']=3.0
            (p/'token_rates.json').write_text(json.dumps(book))
            self.assertGreater(b.snapshot()['token_cost']['last'],before)

    def test_background_model_does_not_steal_active_chat(self):
        b=Broker();b.desktop_event(event('turn/started',turn='turn',model=MODEL))
        b.desktop_event(event('model_update',thread='background',model='other-model'))
        self.assertEqual(b.active_session,'thread');self.assertEqual(b.active_model,MODEL)

    def test_hardware_reset_requires_matching_live_boot_epoch_and_version(self):
        b=Broker();b.boot='boot';b.last_seen=time.monotonic();b.meter.observe(value(),MODEL)
        message={'boot':'boot','epoch':b.epoch,'meter_id':b.meter.reset_id}
        self.assertFalse(b.clear_meter(dict(message,boot='old'),True)['cleared'])
        self.assertTrue(b.clear_meter(message,True)['cleared'])
        self.assertFalse(b.clear_meter(message,True)['cleared'])

    def test_thread_resume_model_is_read_from_official_top_level(self):
        class Child:stdin=io.BytesIO()
        relay=Relay(Child(),io.BytesIO(),io.BytesIO());relay.client_calls['1']={'method':'thread/resume'}
        line=json.dumps({'id':1,'result':{'thread':{'id':'thread'},'model':MODEL}}).encode()+b'\n'
        relay.server_line(line);self.assertEqual(relay.models['thread'],MODEL)

    def test_usage_before_resume_reply_is_not_dropped(self):
        class Child:stdin=io.BytesIO()
        relay=Relay(Child(),io.BytesIO(),io.BytesIO())
        relay.server_line(json.dumps({'method':'thread/tokenUsage/updated','params':{
            'threadId':'thread','turnId':'turn','tokenUsage':{'total':tokens(),'last':tokens()}}}).encode()+b'\n')
        self.assertIn('thread',relay.sessions)
        self.assertIn('thread',relay.latest_usage)

if __name__=='__main__':unittest.main()
