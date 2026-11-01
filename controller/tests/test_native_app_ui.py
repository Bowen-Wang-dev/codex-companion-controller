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
import native_app_ui
import mac_approval_gui
from test_desktop_relay import approval


class NativeAppUiTests(unittest.TestCase):
    def setUp(self):
        self.focus=mock.Mock(return_value=True)
        self.b=Broker(app_focus=self.focus);self.b.desktop_mode=True
        self.b.device_message({'type':'hello','boot':'boot','review_protocol':1},'wifi')
        self.event={'hook_event_name':'PermissionRequest','session_id':'thread','tool_use_id':'call',
                    'tool_name':'Bash','tool_input':{'command':'pwd'}}

    def test_hook_returns_no_decision_even_without_a_recent_relay(self):
        self.assertEqual(self.b.handle_hook(self.event),{})
        self.assertIsNone(self.b.request);self.assertFalse(self.b.hook_pending)
        self.focus.assert_not_called()

    def test_cached_hook_allow_cannot_bypass_native_app(self):
        digest=hashlib.sha256(json.dumps(self.event,sort_keys=True).encode()).hexdigest()
        self.b.hook_results[digest]=(time.monotonic()+120,{'hookSpecificOutput':{'decision':{'behavior':'allow'}}})
        self.assertEqual(self.b.handle_hook(self.event),{})

    def test_pre_permission_does_not_block_native_card_creation(self):
        self.b.prehook_review=True
        event=dict(self.event,hook_event_name='PreToolUse',passport_hook_version=3,
                   tool_name='request_permissions',tool_input={'permissions':{'network':{'enabled':True}}})
        self.assertEqual(self.b.handle_hook(event),{});self.assertIsNone(self.b.request)

    def test_handoff_only_focuses_original_app_without_answering(self):
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
            self.assertFalse(self.b.mac_handoff(dict(binding,id='wrong')))
            self.assertTrue(self.b.mac_handoff(binding))
            end=time.monotonic()+1
            while not self.focus.called and time.monotonic()<end:time.sleep(.005)
            self.focus.assert_called_once_with();self.assertIsNone(req['choice'])
            self.assertFalse(result);self.assertEqual(self.b.snapshot()['req_id'],req['id'])
            self.assertFalse(self.b.snapshot()['mac_ready']) # Not proof the App painted a card.
        finally:alive.clear();worker.join(2)
        self.assertEqual(result,[{}]);self.assertIsNone(self.b.request)

    def test_retired_window_entrypoint_is_inert(self):
        self.assertIsNone(mac_approval_gui.launch('old-running-broker'))

    def test_focus_rejects_changed_app_before_activation(self):
        sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
        with mock.patch('launch_desktop.verify_build',side_effect=ValueError('changed')),mock.patch.object(native_app_ui.subprocess,'run') as run:
            with self.assertRaises(ValueError):native_app_ui.focus()
            run.assert_not_called()

    def test_focus_does_not_relaunch_a_closed_app(self):
        with mock.patch('launch_desktop.verify_build'),mock.patch.object(native_app_ui.subprocess,'run',return_value=mock.Mock(returncode=1)) as run:
            self.assertFalse(native_app_ui.focus());self.assertEqual(run.call_count,1)

    def test_focus_activates_only_verified_original_app(self):
        with mock.patch('launch_desktop.verify_build'),mock.patch.object(native_app_ui.subprocess,'run',return_value=mock.Mock(returncode=0)) as run:
            self.assertTrue(native_app_ui.focus())
            self.assertEqual(run.call_args.args[0],['/usr/bin/open','-a','/Applications/ChatGPT.app'])


if __name__=='__main__':unittest.main()
