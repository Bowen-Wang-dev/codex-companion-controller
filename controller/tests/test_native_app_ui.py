"""Keep native App approval authoritative; never replace it with a window."""
import hashlib
import json
from pathlib import Path
import sys
import threading
import time
import unittest
from unittest import mock

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bridge'))
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from service import Broker
import mac_approval_gui
from test_desktop_relay import approval


class NativeAppUiTests(unittest.TestCase):
    def setUp(self):
        self.b=Broker();self.b.desktop_mode=True
        self.b.device_message({'type':'hello','boot':'boot','review_protocol':1},'wifi')
        self.event={'hook_event_name':'PermissionRequest','session_id':'thread','tool_use_id':'call',
                    'tool_name':'Bash','tool_input':{'command':'pwd'}}

    def test_hook_returns_no_decision_even_without_a_recent_relay(self):
        self.assertEqual(self.b.handle_hook(self.event),{})
        self.assertIsNone(self.b.request);self.assertFalse(self.b.hook_pending)

    def test_cached_hook_allow_cannot_bypass_native_app(self):
        digest=hashlib.sha256(json.dumps(self.event,sort_keys=True).encode()).hexdigest()
        self.b.hook_results[digest]=(time.monotonic()+120,{'hookSpecificOutput':{'decision':{'behavior':'allow'}}})
        self.assertEqual(self.b.handle_hook(self.event),{})

    def test_pre_permission_does_not_block_native_card_creation(self):
        self.b.prehook_review=True
        event=dict(self.event,hook_event_name='PreToolUse',passport_hook_version=3,
                   tool_name='request_permissions',tool_input={'permissions':{'network':{'enabled':True}}})
        self.assertEqual(self.b.handle_hook(event),{});self.assertIsNone(self.b.request)

    def test_retired_handoff_messages_leave_native_approval_pending(self):
        self.b.desktop_event({'relay':'relay','sessions':['desktop-thread'],'kind':'heartbeat'})
        a=approval();alive=threading.Event();alive.set();result=[]
        worker=threading.Thread(target=lambda:result.append(self.b.desktop_request(
            {'relay':'relay','method':a['method'],'native_id':a['id'],'params':a['params']},alive.is_set)))
        worker.start()
        try:
            end=time.monotonic()+1
            while self.b.request is None and time.monotonic()<end:time.sleep(.005)
            req=self.b.request;self.assertIsNotNone(req)
            binding={k:req[k] for k in ('boot','id','digest')};binding['epoch']=self.b.epoch
            before=self.b.snapshot()
            with mock.patch('subprocess.run') as run:
                for message in (dict(binding,id='wrong'),binding):
                    self.b.device_message(dict(message,type='mac_handoff'),'wifi')
                run.assert_not_called()
            self.assertIs(self.b.request,req);self.assertIsNone(req['choice'])
            self.assertFalse(req['cancelled']);self.assertNotIn('handoff',req)
            self.assertFalse(result);self.assertEqual(self.b.receipt,before['receipt'])
            after=self.b.snapshot()
            for key in ('req_id','digest','can_allow','can_deny','action_mode','review_page'):
                self.assertEqual(after.get(key),before.get(key))
            self.assertNotIn('mac_ready',after)
        finally:alive.clear();worker.join(2)
        self.assertEqual(result,[{}]);self.assertIsNone(self.b.request)

    def test_retired_window_entrypoint_is_inert(self):
        self.assertIsNone(mac_approval_gui.launch('old-running-broker'))

if __name__=='__main__':unittest.main()
