import json
import os
import tempfile
import time
import unittest
from unittest import mock
from pathlib import Path
from types import SimpleNamespace
import sys
sys.path.insert(0, str(Path(__file__).parents[1] / 'bridge'))
from usage_meter import breakdown, estimate, load_rates, normalize_notification
from service import Broker


class UsageMeterTests(unittest.TestCase):
    def usage(self):
        return {'inputTokens': 1000, 'cachedInputTokens': 200,
                'cacheWriteInputTokens': 0, 'outputTokens': 300,
                'reasoningOutputTokens': 100, 'totalTokens': 1300}

    def test_breakdown_and_math(self):
        rates = {'input': 2.0, 'cached_input': .2, 'output': 8.0, 'cache_write': 1.0}
        self.assertEqual(estimate(self.usage(), rates), .00404)
        bad = self.usage(); bad['cachedInputTokens'] = 1001
        self.assertIsNone(breakdown(bad))
        bad = self.usage(); bad['totalTokens'] = 2
        self.assertIsNone(breakdown(bad))

    def test_cache_write_needs_explicit_price(self):
        value = self.usage(); value['cacheWriteInputTokens'] = 40
        self.assertIsNone(estimate(value, {'input': 1, 'cached_input': 1, 'output': 1}))

    def test_missing_rate_file_is_empty_and_nonleaking(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(load_rates(Path(d) / 'missing'), {'currency': '', 'models': {}})
            p = Path(d) / 'rates.json'
            p.write_text(json.dumps({'currency': 'CNY', 'models': {
                'gpt-6-astra': {'input': 2.28, 'cached_input': .228, 'output': 11.4}}}))
            rates = load_rates(p)
        self.assertEqual(set(rates['models']), {'gpt-6-astra'})

    def test_relay_usage_binds_thread_model_and_snapshot(self):
        b = Broker(); b.provider_info = {'id': 'custom', 'name': 'Relay', 'model': 'configured', 'billing': 'token'}
        b.active_session = 'thread-1'
        usage = {'last': self.usage(), 'total': self.usage(), 'modelContextWindow': 10000}
        b.desktop_event({'kind': 'token_usage', 'relay': 'relay-1', 'sessions': ['thread-1'],
                         'thread': 'thread-1', 'turn': 'turn-1', 'usage': usage, 'model': 'gpt-6-astra'})
        snap = b.snapshot()
        self.assertEqual(snap['token_usage']['model'], 'gpt-6-astra')
        self.assertTrue(snap['token_usage']['updated'])
        b.active_session = 'other-thread'
        self.assertFalse(b.snapshot()['token_usage']['updated'])

    def test_active_model_update_supersedes_config_default(self):
        b = Broker(); b.provider_info = {'id':'custom','name':'Relay','model':'gpt-6-luna','billing':'token'}
        b.desktop_event({'kind':'model_update','relay':'r','sessions':['t'],'thread':'t','model':'gpt-6.1-sol'})
        snap=b.snapshot()
        self.assertEqual(snap['provider']['active_model'],'gpt-6.1-sol')
        self.assertEqual(snap['token_usage']['model'],'gpt-6.1-sol')

    def test_empty_model_on_same_session_keeps_last_confirmed_model(self):
        b=Broker();b.provider_info={'id':'custom','name':'Relay','model':'gpt-6-luna','billing':'token'}
        b.active_session='t';b.active_model='gpt-6.1-sol'
        b.desktop_event({'kind':'turn/started','relay':'r','sessions':['t'],'thread':'t','model':''})
        self.assertEqual(b.snapshot()['provider']['active_model'],'gpt-6.1-sol')
        self.assertEqual(b.snapshot()['token_usage']['model'],'gpt-6.1-sol')

    def test_new_session_does_not_inherit_previous_session_model(self):
        b=Broker();b.provider_info={'id':'custom','name':'Relay','model':'gpt-6-luna','billing':'token'}
        b.active_session='old';b.active_model='gpt-6.1-sol';b.session_models['old']='gpt-6.1-sol'
        b.desktop_event({'kind':'turn/started','relay':'r','sessions':['new'],'thread':'new','model':''})
        self.assertEqual(b.snapshot()['provider']['active_model'],'')

    def test_turn_start_model_and_reroute_are_tracked(self):
        from stdio_relay import Relay
        import io
        class Child:
            stdin=io.BytesIO()
        relay=Relay(Child(),io.BytesIO(),io.BytesIO())
        relay.sessions.add('t')
        relay.client_calls['7']={'method':'turn/start','thread':'t','model':'gpt-6.1-sol'}
        relay.server_line(b'{"id":7,"result":{"turn":{"id":"turn-1"}}}\n')
        self.assertEqual(relay.models['t'],'gpt-6.1-sol')
        reroute={'method':'model/rerouted','params':{'threadId':'t','fromModel':'gpt-6.1-sol','toModel':'gpt-6.1-sol-fast'}}
        relay.server_line((json.dumps(reroute)+'\n').encode())
        self.assertEqual(relay.models['t'],'gpt-6.1-sol-fast')

    def test_thread_settings_model_change_is_forwarded(self):
        from stdio_relay import Relay
        import io
        class Child:
            stdin=io.BytesIO()
        relay=Relay(Child(),io.BytesIO(),io.BytesIO())
        relay.server_line(json.dumps({'method':'thread/settings/updated','params':
            {'threadId':'t','threadSettings':{'model':'gpt-5.5'}}}).encode()+b'\n')
        self.assertEqual(relay.models['t'],'gpt-5.5')
        self.assertEqual(relay.events.get_nowait()['kind'],'model_update')

    def test_gui_writer_keeps_rate_file_private(self):
        import token_rates_gui
        editor = token_rates_gui.RateEditor.__new__(token_rates_gui.RateEditor)
        editor.currency = SimpleNamespace(get=lambda: 'USD')
        editor.rates = {'gpt-6-astra': {'input': 2.28, 'cached_input': .228,
                                       'output': 11.4, 'cache_write': None}}
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'private' / 'token_rates.json'
            with mock.patch.object(token_rates_gui, 'RATE_FILE', path):
                editor._save_file()
            saved=json.loads(path.read_text())
            self.assertEqual(saved['models']['gpt-6-astra']['output'], 11.4)
            self.assertEqual(saved['currency'],'USD')
            self.assertEqual(os.stat(path).st_mode & 0o777, 0o600)


if __name__ == '__main__':
    unittest.main()
