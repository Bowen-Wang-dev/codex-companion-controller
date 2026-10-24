import copy
from contextlib import contextmanager
import json
from pathlib import Path
import queue
import sys
import tempfile
import threading
import time
import unittest

from websockets.sync.server import unix_serve

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'bridge'))
from native_approvals import NativeApprovals,NativeClient,permission_display
from service import Broker,review_policy
from permission_result import permission_outcome


def request(permissions=None,identifier='request-1'):
    return {'id':identifier,'method':'item/permissions/requestApproval','params':{
        'threadId':'thread-1','turnId':'turn-1','itemId':'item-1','environmentId':None,
        'startedAtMs':int(time.time()*1000),'cwd':'/Users/test/project','reason':'not sent to device',
        'permissions':permissions or {'network':{'enabled':True},'fileSystem':None}}}


class Client:
    def __init__(self):self.sent=queue.Queue()
    def send(self,value):self.sent.put(value)


class NativeTests(unittest.TestCase):
    def setUp(self):
        self.b=Broker();self.b.native_session='thread-1';self.b.native_connected=True
        self.b.device_message({'type':'hello','boot':'boot','readonly_notices':True},'wifi')
        self.a=NativeApprovals(self.b,'unused','thread-1',review_policy)
        self.c=Client();self.a.client=self.c

    def wait(self,predicate):
        end=time.monotonic()+1
        while not predicate():
            if time.monotonic()>end:self.fail('Asynchronous native request did not settle')
            time.sleep(.005)

    def resolve(self,identifier='request-1'):
        self.a.message(self.c,{'method':'serverRequest/resolved','params':{'threadId':'thread-1','requestId':identifier}})
        self.wait(lambda:not self.a.pending)

    def decide(self,choice):
        self.wait(lambda:self.b.request is not None)
        r=self.b.request
        return self.b.decision({'boot':'boot','epoch':self.b.epoch,'id':r['id'],'digest':r['digest'],'choice':choice})

    def test_physical_network_allow_returns_exact_turn_grant(self):
        self.a.message(self.c,request())
        self.assertTrue(self.decide('allow'))
        result=self.c.sent.get(timeout=1)
        self.assertEqual(result,{'id':'request-1','result':{'permissions':{'network':{'enabled':True}},'scope':'turn'}})
        self.assertFalse(self.decide('allow'))
        self.resolve();self.assertIsNone(self.b.request)
        self.assertNotEqual(self.b.expression,'delight') # resolved is not execution evidence

    def test_physical_network_deny_grants_nothing_and_cries(self):
        self.a.message(self.c,request());self.assertTrue(self.decide('deny'))
        self.assertEqual(self.c.sent.get(timeout=1)['result'],{'permissions':{},'scope':'turn'})
        self.resolve();self.assertEqual(self.b.expression,'crying')

    def test_only_matching_actual_tool_result_confirms_grant(self):
        self.a.message(self.c,request());self.assertTrue(self.decide('allow'))
        self.c.sent.get(timeout=1);self.resolve()
        event={'hook_event_name':'PostToolUse','session_id':'thread-1','turn_id':'turn-1',
               'tool_use_id':'wrong','tool_name':'request_permissions','permission_outcome':'granted'}
        self.b.event(event);self.assertNotEqual(self.b.expression,'delight')
        event['tool_use_id']='item-1';self.b.event(event)
        self.assertEqual(self.b.expression,'delight');self.assertEqual(self.b.receipt,'权限已授予')

    def test_folder_and_new_entries_form_preserve_exact_scope(self):
        for i,fs in enumerate(({'read':None,'write':['/Users/test/project/export']},
                   {'entries':[{'path':{'type':'path','path':'/Users/test/project/export'},'access':'write'}]})):
            with self.subTest(fs=fs):
                event=request({'network':None,'fileSystem':fs},'folder-'+str(i))
                self.a.message(self.c,event);self.assertTrue(self.decide('allow'))
                result=self.c.sent.get(timeout=1)['result']
                self.assertEqual(result['scope'],'turn')
                self.assertEqual(result['permissions']['fileSystem'],{k:v for k,v in fs.items() if v is not None})
                self.resolve('folder-'+str(i))

    def test_complex_scope_never_becomes_allowable_after_truncation(self):
        unsafe=[{'fileSystem':{'write':['/Users/test']}},
                {'fileSystem':{'write':['/Users/test/Documents']}},
                {'fileSystem':{'write':['/Users/test/.ssh/key']}},
                {'fileSystem':{'write':['/Users/test/project/'+('x'*100)]}},
                {'fileSystem':{'entries':[{'path':{'type':'special','value':'root'},'access':'write'}]}},
                {'network':{'enabled':True,'unknown':True}}]
        for i,permissions in enumerate(unsafe):
            with self.subTest(permissions=permissions):
                self.a.message(self.c,request(permissions,'unsafe-'+str(i)));self.assertFalse(self.decide('allow'))
                self.assertTrue(self.decide('deny'));self.c.sent.get(timeout=1);self.resolve('unsafe-'+str(i))

    def test_cli_resolution_cancels_hardware_choice(self):
        self.a.message(self.c,request());self.wait(lambda:self.b.request is not None)
        r=copy.deepcopy(self.b.request)
        self.resolve()
        self.assertFalse(self.b.decision({'boot':'boot','epoch':self.b.epoch,'id':r['id'],'digest':r['digest'],'choice':'allow'}))
        self.assertTrue(self.c.sent.empty())
        self.a.message(self.c,request())
        self.assertIsNone(self.b.request) # No ghost prompt after a resolved callback.

    def test_duplicate_keeps_identity_and_deadline(self):
        e=request();self.a.message(self.c,e);self.wait(lambda:self.b.request is not None)
        r=copy.deepcopy(self.b.request);self.a.message(self.c,e)
        self.assertEqual(r,self.b.request);self.resolve()

    def test_reboot_and_disconnect_never_submit(self):
        for mode in ('reboot','disconnect'):
            self.setUp();self.a.message(self.c,request());self.wait(lambda:self.b.request is not None)
            if mode=='reboot':self.b.device_message({'type':'hello','boot':'new-boot'},'wifi')
            else:self.a.disconnected(self.c)
            self.wait(lambda:not self.a.pending)
            self.assertIsNone(self.b.request);self.assertTrue(self.c.sent.empty())

    def test_expired_other_session_or_offline_stays_in_cli(self):
        for mode in ('expired','other','offline'):
            e=request()
            if mode=='expired':e['params']['startedAtMs']-=111000
            if mode=='other':e['params']['threadId']='other'
            if mode=='offline':self.b.last_seen=0
            self.a.message(self.c,e);self.wait(lambda:not self.a.pending)
            self.assertIsNone(self.b.request);self.assertTrue(self.c.sent.empty())

    def test_failed_turn_is_failed_and_cancels_pending_approval(self):
        self.b.event({'hook_event_name':'UserPromptSubmit','session_id':'thread-1'})
        self.b.event({'hook_event_name':'Stop','session_id':'thread-1'})
        self.assertEqual(self.b.state,'working') # Await the actual turn status.
        self.a.message(self.c,request());self.wait(lambda:self.b.request is not None)
        self.a.message(self.c,{'method':'turn/completed','params':{'threadId':'thread-1','turn':{'id':'turn-1','status':'failed'}}})
        self.wait(lambda:not self.a.pending)
        self.assertEqual(self.b.state,'failed');self.assertTrue(self.c.sent.empty())

    def test_command_approval_uses_accept_not_permissions_response(self):
        e=request();e['method']='item/commandExecution/requestApproval'
        e['params'].update(kind='command',command='pwd');e['params'].pop('permissions')
        self.a.message(self.c,e);self.assertTrue(self.decide('allow'))
        self.assertEqual(self.c.sent.get(timeout=1),{'id':'request-1','result':{'decision':'accept'}})
        self.resolve()

    def test_native_mode_suppresses_duplicate_hook_approval_and_notice(self):
        event={'hook_event_name':'PreToolUse','session_id':'thread-1','tool_name':'request_permissions',
               'tool_input':{'permissions':{'network':{'enabled':True}}}}
        self.b.event(event);self.assertIsNone(self.b.notice)
        self.assertEqual(self.b.permission(event),{})


class NativeWebSocketTests(unittest.TestCase):
    @contextmanager
    def server(self,handler):
        # macOS AF_UNIX paths must be short; the default pytest/temp directory
        # plus the project path can exceed its limit.
        with tempfile.TemporaryDirectory(prefix='pcc-ws-',dir='/tmp') as directory:
            path=Path(directory)/'app.sock'
            with unix_serve(handler,str(path),compression=None,close_timeout=1) as server:
                thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
                try:yield path
                finally:server.shutdown();thread.join(timeout=2)

    def test_websocket_upgrade_initialize_resume_and_no_model_turn_api(self):
        frames=[]
        def handler(connection):
            # A JSONL-only client cannot pass this HTTP upgrade or text framing.
            self.assertEqual(connection.request.headers['Upgrade'].lower(),'websocket')
            for frame in connection:
                frames.append(frame);self.assertIsInstance(frame,str)
                m=json.loads(frame)
                if 'id' in m:
                    result={'thread':{'id':m.get('params',{}).get('threadId')}} if m['method']=='thread/resume' else {}
                    connection.send(json.dumps({'id':m['id'],'result':result}))
        with self.server(handler) as path:
            client=NativeClient(path,lambda *_:None,lambda *_:None)
            try:
                client.rpc('initialize',{})
                self.assertEqual(client.rpc('thread/resume',{'threadId':'existing'})['thread']['id'],'existing')
                with self.assertRaises(ValueError):client.rpc('turn/start',{})
                with self.assertRaises(ValueError):client.rpc('thread/start',{})
            finally:client.close()
        self.assertEqual(len(frames),2)

    def test_native_server_request_response_and_ping_share_connection(self):
        received=queue.Queue();notifications=queue.Queue()
        def handler(connection):
            m=json.loads(connection.recv())
            connection.send(json.dumps({'id':m['id'],'result':{}}))
            connection.ping(b'keepalive').wait(1)
            # Fragmented text must still be one JSON-RPC message for the Bridge.
            payload=json.dumps(request())
            connection.send([payload[:20],payload[20:]])
            received.put(json.loads(connection.recv()))
        with self.server(handler) as path:
            client=NativeClient(path,lambda _,m:notifications.put(m),lambda *_:None)
            try:
                client.rpc('initialize',{})
                self.assertEqual(notifications.get(timeout=1)['method'],'item/permissions/requestApproval')
                reply={'id':'request-1','result':{'permissions':{},'scope':'turn'}}
                client.send(reply);self.assertEqual(received.get(timeout=1),reply)
            finally:client.close()

    def test_timeout_names_exact_rpc(self):
        def handler(connection):
            for _ in connection:pass # Deliberately never respond.
        with self.server(handler) as path:
            client=NativeClient(path,lambda *_:None,lambda *_:None)
            try:
                with self.assertRaisesRegex(RuntimeError,'account/read.*未响应'):
                    client.rpc('account/read',{},timeout=.05)
            finally:client.close()

    def test_disconnect_wakes_waiter_without_waiting_for_timeout(self):
        closed=threading.Event()
        def handler(connection):connection.recv();connection.close()
        with self.server(handler) as path:
            client=NativeClient(path,lambda *_:None,lambda *_:closed.set())
            try:
                started=time.monotonic()
                with self.assertRaisesRegex(RuntimeError,'initialize.*连接中断'):client.rpc('initialize',{})
                self.assertLess(time.monotonic()-started,2)
                self.assertTrue(closed.wait(1))
            finally:client.close()


class PermissionOutcomeTests(unittest.TestCase):
    def test_portable_project_and_folder_are_completely_visible(self):
        params=request()['params']
        params['cwd']='/Users/developer/Documents/Codex/2026-10-23/codex-companion-controller-ai-passport-folotoy'
        self.assertTrue(permission_display(params)[3])
        params['cwd']='/Users/developer/Documents/Codex/2026-10-24/codex-approve-deny-2'
        path='/Users/developer/Documents/approval-test'
        params['permissions']={'network':None,'fileSystem':{'read':None,'write':[path]}}
        _,summary,_,can_allow,_=permission_display(params)
        self.assertTrue(can_allow);self.assertIn(path,summary)
        self.assertLessEqual(len(summary.encode()),90)

    def test_documented_response_is_reduced_to_outcome(self):
        event={'hook_event_name':'PostToolUse','tool_name':'request_permissions',
               'tool_input':{'permissions':{'network':{'enabled':True}}}}
        for grant,expected in (({'network':{'enabled':True}},'granted'),({},'denied')):
            event['tool_response']={'permissions':grant,'sensitive':'never forwarded'}
            self.assertEqual(permission_outcome(event),expected)
            event['tool_response']=json.dumps(event['tool_response'])
            self.assertEqual(permission_outcome(event),expected)
        event['tool_response']='not JSON';self.assertIsNone(permission_outcome(event))

    def test_partial_filesystem_grant_is_not_denial_or_full_success(self):
        event={'hook_event_name':'PostToolUse','tool_name':'request_permissions',
               'tool_input':{'permissions':{'file_system':{'write':['/first','/second']}}},
               'tool_response':{'permissions':{'file_system':{'write':['/first']}}}}
        self.assertEqual(permission_outcome(event),'partial')


if __name__=='__main__':unittest.main()
