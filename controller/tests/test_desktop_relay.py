import copy
import io
import json
import os
from pathlib import Path
import queue
import sys
import socketserver
import subprocess
import tempfile
import threading
import time
import unittest
from unittest import mock

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'bridge'))
from stdio_relay import Arbitration,valid_response
from service import Broker
import stdio_relay


def approval():
    return {'id':'approval-1','method':'item/permissions/requestApproval','params':{
        'threadId':'desktop-thread','turnId':'turn','itemId':'tool-call','environmentId':None,
        'startedAtMs':int(time.time()*1000),'cwd':'/Users/test/project',
        'permissions':{'network':{'enabled':True},'fileSystem':None}}}


class ArbitrationTests(unittest.TestCase):
    def setUp(self):
        self.writes=[];self.relay=Arbitration(self.writes.append);self.message=approval()
        self.pending=self.relay.offer(self.message)
        self.allow={'type':'desktop_decision','result':{'permissions':{'network':{'enabled':True}},'scope':'turn'}}

    def test_device_answer_is_exact_and_late_app_answer_is_suppressed(self):
        self.assertTrue(self.relay.from_device(self.pending,self.allow))
        reply=json.loads(self.writes[0]);self.assertEqual(reply['id'],'approval-1')
        self.assertEqual(reply['result'],self.allow['result'])
        self.assertFalse(self.relay.from_app(b'late\n',{'id':'approval-1','result':{}}))
        self.assertEqual(len(self.writes),1)

    def test_app_wins_without_a_second_device_reply(self):
        line=b'{"id":"approval-1","result":{"permissions":{},"scope":"turn"}}\n'
        self.assertTrue(self.relay.from_app(line,json.loads(line)))
        self.assertFalse(self.relay.from_device(self.pending,self.allow));self.assertEqual(self.writes,[line])

    def test_resolved_request_and_disconnect_cannot_submit(self):
        self.relay.resolve('approval-1')
        self.assertFalse(self.relay.from_device(self.pending,self.allow))
        self.pending=self.relay.offer(self.message);self.relay.close()
        self.assertFalse(self.relay.from_device(self.pending,self.allow));self.assertEqual(self.writes,[])

    def test_model_turn_and_unrelated_responses_are_byte_exact_passthrough(self):
        for line in (b'{"id":1,"method":"turn/start","params":{"input":["original"]}}\n',
                     b'{"id":"other","result":{"value":"unchanged"}}\n'):
            self.assertTrue(self.relay.from_app(line,json.loads(line)))
        self.assertEqual(len(self.writes),2)

    def test_no_new_permissions_or_session_grants(self):
        for value in ({'permissions':{'network':{'enabled':True},'fileSystem':{'write':['/']}},'scope':'turn'},
                      {'permissions':{'network':{'enabled':True}},'scope':'session'},
                      {'permissions':{'network':{'enabled':1}},'scope':'turn'}):
            result={'type':'desktop_decision','result':value}
            self.assertFalse(self.relay.from_device(self.pending,result))
        self.assertEqual(self.writes,[])

    def test_nullable_requested_fields_do_not_block_exact_filesystem_grant(self):
        value=approval();value['params']['permissions']={'fileSystem':{'read':None,'write':['/Users/test/project']}}
        self.assertTrue(valid_response(value,{'permissions':{'fileSystem':{'write':['/Users/test/project']}},'scope':'turn'}))


class DesktopBrokerTests(unittest.TestCase):
    def setUp(self):
        self.b=Broker();self.b.device_message({'type':'hello','boot':'boot','firmware':'0.2.3',
            'readonly_notices':True,'prehook_review':True},'wifi')
        self.b.desktop_event({'relay':'relay','sessions':['desktop-thread'],'kind':'heartbeat'})
        self.workers=[]

    def tearDown(self):
        self.b.device_message({'type':'hello','boot':'reboot'},'wifi')
        for worker in self.workers:worker.join(timeout=1)

    def wait(self,predicate):
        end=time.monotonic()+1
        while not predicate():
            if time.monotonic()>end:self.fail('Desktop review did not settle')
            time.sleep(.005)

    def request(self):
        message=approval()
        return {'type':'desktop_request','relay':'relay','method':message['method'],
                'native_id':message['id'],'params':message['params']}

    def test_physical_approve_replies_to_app_without_mac_confirmation(self):
        result=[];worker=threading.Thread(target=lambda:result.append(self.b.desktop_request(self.request())),daemon=True)
        self.workers.append(worker);worker.start();self.wait(lambda:self.b.request is not None)
        view=self.b.snapshot();self.assertEqual(view['action_mode'],'');self.assertTrue(view['can_allow'])
        self.assertTrue(self.b.decision({'boot':'boot','epoch':self.b.epoch,'id':view['req_id'],
            'digest':view['digest'],'choice':'allow'}))
        self.wait(lambda:bool(result))
        self.assertEqual(result,[{'type':'desktop_decision','result':{'permissions':{'network':{'enabled':True}},'scope':'turn'}}])

    def test_pretool_does_not_add_a_second_mac_handoff_for_attached_app(self):
        event={'hook_event_name':'PreToolUse','session_id':'desktop-thread','passport_hook_version':3,
            'tool_name':'request_permissions','tool_input':{'permissions':{'network':{'enabled':True}}}}
        self.assertEqual(self.b.handle_hook(event),{});self.assertIsNone(self.b.request);self.assertIsNone(self.b.notice)

    def test_unregistered_stale_or_wrong_relay_is_never_allowed(self):
        event=self.request();event['relay']='not-registered';self.assertEqual(self.b.desktop_request(event),{})
        self.b.desktop_relays['relay']['at']=time.monotonic()-9
        self.assertEqual(self.b.desktop_request(self.request()),{})

    def test_actual_desktop_turn_failure_overrides_hook_stop(self):
        self.b.active_session='desktop-thread';self.b.set_state('working')
        self.b.event({'hook_event_name':'Stop','session_id':'desktop-thread'})
        self.assertEqual(self.b.state,'working')
        self.b.desktop_event({'relay':'relay','sessions':['desktop-thread'],'kind':'turn/completed',
            'thread':'desktop-thread','status':'failed'})
        self.assertEqual(self.b.state,'failed')

    def test_extra_command_permissions_are_never_hidden_by_a_safe_command(self):
        event=self.request();event['method']='item/commandExecution/requestApproval'
        event['params']['command']='pwd';event['params']['additionalPermissions']={'fileSystem':{'write':['/']}}
        result=[];worker=threading.Thread(target=lambda:result.append(self.b.desktop_request(event)),daemon=True)
        self.workers.append(worker);worker.start();self.wait(lambda:self.b.request is not None)
        self.assertFalse(self.b.snapshot()['can_allow'])
        self.b.device_message({'type':'hello','boot':'changed'},'wifi');self.wait(lambda:bool(result))
        self.assertEqual(result,[{}])


class UserInputNoticeTests(unittest.TestCase):
    def setUp(self):
        self.b=Broker();self.b.device_message({'type':'hello','boot':'boot','readonly_notices':True},'wifi')
        self.event={'hook_event_name':'PreToolUse','tool_name':'request_user_input_async',
            'session_id':'s','tool_use_id':'question-1','tool_input':{'questions':[{'title':'请运行检查脚本，然后回复已检查。'}]}}

    def test_async_question_notifies_and_acceptance_does_not_remove_it(self):
        self.b.event(self.event);view=self.b.snapshot()
        self.assertEqual(view['request_kind'],'user_input');self.assertIn('检查',view['project'])
        self.assertFalse(view['can_allow'] or view['can_deny'])
        post=copy.deepcopy(self.event);post['hook_event_name']='PostToolUse';self.b.event(post)
        self.assertEqual(self.b.snapshot()['req_id'],view['req_id'])

    def test_duplicate_question_keeps_id_and_deadline(self):
        self.b.event(self.event);first=copy.deepcopy(self.b.input_notices[0]);self.b.event(self.event)
        self.assertEqual(self.b.input_notices,[first])

    def test_read_ack_is_bound_and_never_becomes_a_permission_answer(self):
        self.b.event(self.event);view=self.b.snapshot()
        message={'type':'dismiss','boot':'old','epoch':self.b.epoch,'id':view['req_id'],'digest':view['digest']}
        self.b.device_message(message,'wifi');self.assertEqual(len(self.b.input_notices),1)
        message['boot']='boot';self.b.device_message(message,'wifi')
        self.assertEqual(self.b.input_notices,[]);self.assertIsNone(self.b.request)

    def test_human_message_or_expiry_clears_notice(self):
        self.b.event(self.event);self.b.event({'hook_event_name':'UserPromptSubmit','session_id':'s'})
        self.assertEqual(self.b.input_notices,[])
        self.b.event(self.event);self.b.input_notices[0]['deadline']=time.monotonic()-1
        self.assertNotIn('request_kind',self.b.snapshot())


class StdioIntegrationTests(unittest.TestCase):
    def run_round_trip(self,physical,paged=False,choice='allow'):
        b=Broker();b.device_message({'type':'hello','boot':'boot','readonly_notices':True,'review_protocol':1 if paged else 0},'wifi')
        class Handler(socketserver.StreamRequestHandler):
            def handle(self):
                event=json.loads(self.rfile.readline(65537))
                if event['type']=='desktop_event':result=b.desktop_event(event)
                else:
                    import select
                    result=b.desktop_request(event,lambda:not select.select([self.connection],[],[],0)[0])
                try:self.wfile.write(json.dumps(result).encode()+b'\n')
                except (OSError,BrokenPipeError):pass # App cancellation closes the pending socket.
        class Server(socketserver.ThreadingUnixStreamServer):daemon_threads=True
        child_code='''
import json,sys
first=json.loads(sys.stdin.readline())
print(json.dumps({'id':first['id'],'result':{'userAgent':'fixture'}}),flush=True)
message=json.loads(sys.argv[1]);print(json.dumps(message),flush=True)
reply=json.loads(sys.stdin.readline())
print(json.dumps({'method':'fixture/echo','params':reply}),flush=True)
print(json.dumps({'method':'serverRequest/resolved','params':{'threadId':'desktop-thread','requestId':message['id']}}),flush=True)
'''
        with tempfile.TemporaryDirectory(prefix='pcc-relay-',dir='/tmp') as folder:
            path=Path(folder)/'bridge.sock'
            with Server(str(path),Handler) as server:
                server_thread=threading.Thread(target=server.serve_forever,daemon=True);server_thread.start()
                app_input_read,app_input_write=os.pipe();app_output_read,app_output_write=os.pipe()
                with os.fdopen(app_input_read,'rb') as app_in,os.fdopen(app_input_write,'wb') as app_writer,os.fdopen(app_output_read,'rb') as app_reader,os.fdopen(app_output_write,'wb') as app_out:
                    child=subprocess.Popen([sys.executable,'-u','-c',child_code,json.dumps(approval())],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                    relay=stdio_relay.Relay(child,app_in,app_out)
                    with mock.patch.object(stdio_relay,'check_directory',return_value=path):
                        worker=threading.Thread(target=relay.run,daemon=True);worker.start()
                        try:
                            app_writer.write(b'{"id":1,"method":"initialize","params":{}}\n');app_writer.flush()
                            self.assertEqual(json.loads(app_reader.readline())['id'],1)
                            request=json.loads(app_reader.readline());self.assertEqual(request['method'],'item/permissions/requestApproval')
                            deadline=time.monotonic()+2
                            while b.request is None and time.monotonic()<deadline:time.sleep(.005)
                            self.assertIsNotNone(b.request)
                            if physical:
                                req=b.request
                                message={'boot':'boot','epoch':b.epoch,'id':req['id'],'digest':req['digest'],'choice':choice}
                                if paged:
                                    view=b.snapshot()
                                    self.assertFalse(b.decision(message))
                                    for index in range(1,view['review_total']+1):
                                        self.assertTrue(b.review_page(dict(message,review_page=index)))
                                        view=b.snapshot()
                                    message['review_page']=view['review_total']
                                self.assertTrue(b.decision(message))
                            else:
                                app_writer.write(b'{"id":"approval-1","result":{"permissions":{},"scope":"turn"}}\n');app_writer.flush()
                            echo=json.loads(app_reader.readline())
                            self.assertEqual(echo['method'],'fixture/echo')
                            self.assertEqual(echo['params']['result'],{'permissions':{'network':{'enabled':True}},'scope':'turn'} if physical and choice=='allow' else {'permissions':{},'scope':'turn'})
                            resolved=json.loads(app_reader.readline());self.assertEqual(resolved['method'],'serverRequest/resolved')
                            worker.join(timeout=2);self.assertFalse(worker.is_alive())
                        finally:
                            relay.stopping.set();relay.arbiter.close()
                            if child.poll() is None:child.terminate()
                            child.wait(timeout=2)
                            child.stdin.close();child.stdout.close();child.stderr.close()
                server.shutdown();server_thread.join(timeout=2)

    def test_physical_choice_crosses_real_stdio_and_private_unix_ipc(self):self.run_round_trip(True)
    def test_app_choice_cancels_hardware_across_real_transports(self):self.run_round_trip(False)
    def test_paged_device_allow_crosses_real_stdio_and_private_unix_ipc(self):self.run_round_trip(True,paged=True)
    def test_paged_device_deny_crosses_real_stdio_and_private_unix_ipc(self):self.run_round_trip(True,paged=True,choice='deny')
