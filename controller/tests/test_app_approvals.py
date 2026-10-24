import copy
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest
from unittest import mock

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'bridge'))
from service import Broker,excerpt
from hook_policy import display,permission_summary


def event(name='PermissionRequest',identifier='one',session='s'):
    return {'hook_event_name':name,'session_id':session,'turn_id':'turn',
            'tool_use_id':identifier,'tool_name':'Bash','cwd':'/tmp/project',
            'tool_input':{'command':'ls -la /tmp/example'}}


class AppApprovalTests(unittest.TestCase):
    def setUp(self):
        self.b=Broker();self.b.device_message({'type':'hello','boot':'boot','firmware':'0.2.3',
            'readonly_notices':True,'prehook_review':True},'wifi')
        self.threads=[]

    def wait(self,predicate):
        end=time.monotonic()+1
        while not predicate():
            if time.monotonic()>end:self.fail('Hook worker did not settle')
            time.sleep(.005)

    def run_hook(self,e,**kwargs):
        result=[]
        thread=threading.Thread(target=lambda:result.append(self.b.handle_hook(e,**kwargs)),daemon=True)
        self.threads.append(thread);thread.start();return result

    def choose(self,choice):
        r=self.b.snapshot()
        return self.b.decision({'boot':'boot','epoch':self.b.epoch,'id':r.get('req_id'),
                                'digest':r.get('digest'),'choice':choice})

    def tearDown(self):
        self.b.device_message({'type':'hello','boot':'reboot'},'wifi')
        for thread in self.threads:thread.join(timeout=1)

    def permission_event(self):
        e=event('PreToolUse');e['tool_name']='functions.request_permissions';e['passport_hook_version']=3
        e['tool_input']={'permissions':{'file_system':{'write':['/tmp/directory']},'network':{'enabled':True}}}
        return e

    def test_completion_returns_to_idle_after_three_seconds(self):
        self.b.event(event('UserPromptSubmit'));self.b.event(event('Stop'))
        self.assertEqual(self.b.snapshot()['state'],'completed')
        self.assertAlmostEqual(self.b.completed_until-time.monotonic(),3,delta=.1)
        self.b.completed_until=time.monotonic()-1
        self.assertEqual(self.b.snapshot()['state'],'idle');self.assertEqual(self.b.receipt,'')
        self.assertIn('本轮响应已结束',self.b.history)

    def test_new_work_and_pending_request_are_not_reset_by_old_completion(self):
        self.b.event(event('UserPromptSubmit'));self.b.event(event('Stop'))
        self.b.event(event('UserPromptSubmit'))
        self.assertEqual(self.b.completed_until,0)
        self.assertEqual(self.b.snapshot()['state'],'working')
        self.b.set_state('failed');self.assertEqual(self.b.snapshot()['state'],'failed')
        self.b.set_state('denied');self.assertEqual(self.b.snapshot()['state'],'denied')

    def test_duplicate_completion_does_not_extend_hold(self):
        self.b.set_state('completed');deadline=self.b.completed_until
        self.b.set_state('completed');self.assertEqual(self.b.completed_until,deadline)

    def test_builtin_directory_request_can_be_rejected_before_native_dialog(self):
        result=self.run_hook(self.permission_event());self.wait(lambda:self.b.request is not None)
        self.assertEqual(self.b.snapshot()['action_mode'],'mac_confirm')
        self.assertTrue(self.choose('deny'));self.wait(lambda:bool(result))
        output=result[0]['hookSpecificOutput']
        self.assertEqual(output['hookEventName'],'PreToolUse');self.assertEqual(output['permissionDecision'],'deny')
        self.assertEqual(self.b.state,'denied');self.assertEqual(self.b.expression,'crying')

    def test_continue_to_mac_never_returns_a_grant(self):
        result=self.run_hook(self.permission_event());self.wait(lambda:self.b.request is not None)
        identifier=self.b.request['id']
        self.assertTrue(self.choose('allow'));self.wait(lambda:bool(result))
        self.assertEqual(result,[{}]);self.assertIsNone(self.b.awaiting_execution)
        self.assertEqual(self.b.state,'working');self.assertEqual(self.b.receipt,'请在 Mac 确认权限')
        data=self.b.snapshot();self.assertEqual(data['req_id'],identifier)
        self.assertFalse(data['can_allow'] or data['can_deny'])
        self.b.set_state('completed')
        self.assertEqual(self.b.handle_hook(self.permission_event()),{})
        self.assertEqual(self.b.state,'completed') # A late duplicate can't restart work.

    def test_old_firmware_or_old_hook_stays_readonly(self):
        e=self.permission_event();self.b.prehook_review=False
        self.assertEqual(self.b.handle_hook(e),{})
        self.assertFalse(self.b.snapshot()['can_deny'])
        self.b.prehook_review=True;e.pop('passport_hook_version')
        self.assertEqual(self.b.handle_hook(e),{});self.assertIsNone(self.b.request)

    def test_disconnect_cancels_prompt_without_submitting(self):
        alive=threading.Event();alive.set()
        result=self.run_hook(self.permission_event(),alive=alive.is_set)
        self.wait(lambda:self.b.request is not None);alive.clear();self.wait(lambda:bool(result))
        self.assertEqual(result,[{}]);self.assertIsNone(self.b.request)
        self.assertNotEqual(self.b.state,'denied')

    def test_concurrent_requests_are_queued_and_have_separate_ids(self):
        first=self.run_hook(event());self.wait(lambda:self.b.request is not None)
        identifier=self.b.request['id']
        second=self.run_hook(event(identifier='two',session='other'))
        self.wait(lambda:len(self.b.hook_pending)==2)
        self.assertEqual(self.b.request['id'],identifier)
        self.assertTrue(self.choose('allow'));self.wait(lambda:bool(first))
        self.wait(lambda:self.b.request is not None and self.b.request['id']!=identifier)
        self.assertTrue(self.choose('deny'));self.wait(lambda:bool(second))
        self.assertEqual(first[0]['hookSpecificOutput']['decision']['behavior'],'allow')
        self.assertEqual(second[0]['hookSpecificOutput']['decision']['behavior'],'deny')

    def test_duplicate_waiters_share_one_hardware_decision(self):
        first=self.run_hook(event());self.wait(lambda:self.b.request is not None)
        second=self.run_hook(event());time.sleep(.02)
        self.assertEqual(len(self.b.hook_pending),1)
        self.assertTrue(self.choose('deny'));self.wait(lambda:bool(first) and bool(second))
        self.assertEqual(first,second)
        self.assertEqual(self.b.handle_hook(event()),first[0])
        self.assertIsNone(self.b.request) # A late duplicate doesn't replay a prompt.

    def test_identical_requests_without_call_ids_are_not_merged(self):
        e=event();e.pop('tool_use_id')
        first=self.run_hook(e);self.wait(lambda:self.b.request is not None)
        second=self.run_hook(e);self.wait(lambda:len(self.b.hook_pending)==2)
        identifier=self.b.request['id'];self.assertTrue(self.choose('deny'))
        self.wait(lambda:bool(first));self.wait(lambda:self.b.request is not None and self.b.request['id']!=identifier)
        self.assertFalse(second);self.assertTrue(self.choose('deny'));self.wait(lambda:bool(second))

    def test_short_lived_duplicate_cannot_cancel_long_lived_hook(self):
        alive=threading.Event();alive.set()
        first=self.run_hook(event(),alive=alive.is_set)
        self.wait(lambda:self.b.request is not None);identifier=self.b.request['id']
        second=self.run_hook(event());self.wait(lambda:self.b.request['waiters']==2)
        alive.clear();self.wait(lambda:bool(first))
        self.assertEqual(first,[{}]);self.assertFalse(second)
        self.assertEqual(self.b.request['id'],identifier)
        self.assertEqual(self.b.request['waiters'],1)
        self.assertTrue(self.choose('deny'));self.wait(lambda:bool(second))
        self.assertEqual(second[0]['hookSpecificOutput']['decision']['behavior'],'deny')
        self.assertIsNone(self.b.request)

    def test_last_disconnected_duplicate_removes_prompt_without_decision(self):
        first_alive=threading.Event();first_alive.set()
        second_alive=threading.Event();second_alive.set()
        first=self.run_hook(event(),alive=first_alive.is_set)
        self.wait(lambda:self.b.request is not None)
        second=self.run_hook(event(),alive=second_alive.is_set)
        self.wait(lambda:self.b.request['waiters']==2)
        first_alive.clear();self.wait(lambda:bool(first))
        self.assertIsNotNone(self.b.request)
        second_alive.clear();self.wait(lambda:bool(second))
        self.assertEqual(second,[{}]);self.assertIsNone(self.b.request)

    def test_interrupt_cancels_only_matching_session(self):
        result=self.run_hook(self.permission_event());self.wait(lambda:self.b.request is not None)
        self.b.event(event('Interrupt',session='other'));self.assertFalse(self.b.request['cancelled'])
        self.b.event(event('Interrupt'));self.wait(lambda:bool(result))
        self.assertEqual(result,[{}])

    def test_camelcase_entries_notify_without_losing_network(self):
        e=self.permission_event();e['tool_input']['permissions']={'fileSystem':{'entries':[
            {'path':{'type':'path','path':'/tmp/example'},'access':'write'}]},'network':{'enabled':True}}
        heading,summary=permission_summary(e)
        self.assertEqual(heading,'权限请求');self.assertIn('网络',summary);self.assertIn('/tmp/example',summary)


class DisplayPolicyTests(unittest.TestCase):
    def test_utf8_excerpt_fits_firmware_buffer_without_a_partial_character(self):
        text=excerpt('写入 /目录/'+'测试'*50,90)
        self.assertLessEqual(len(text.encode()),90)
        self.assertNotIn('\ufffd',text)

    def test_complete_read_commands_and_filesystem_mcp_can_be_reviewed(self):
        for command in ('ls -la /tmp/example','stat /tmp/example','cat /tmp/example','head -n 20 /tmp/example'):
            e=event();e['tool_input']['command']=command;view=display(e)
            self.assertTrue(view['can_allow'],command);self.assertIn(command,view['project'])
            self.assertLessEqual(len(view['project'].encode()),90)
        e=event();e['tool_name']='mcp__filesystem__read_file';e['tool_input']={'path':'/tmp/example'}
        self.assertTrue(display(e)['can_allow'])

    def test_script_sensitive_path_long_scope_and_unknown_mcp_stay_on_mac(self):
        for command in ('cat ~/.ssh/id_rsa','cat /Users/test/.codex/auth.json','rm -rf /tmp/example',
                        'ls /tmp/a; pwd','ls /tmp/'+'x'*100):
            e=event();e['tool_input']['command']=command
            self.assertFalse(display(e)['can_allow'],command)
        e=event();e['tool_name']='mcp__other__delete_file';e['tool_input']={'path':'/tmp/a'}
        self.assertFalse(display(e)['can_allow'])

    def test_symlink_to_hidden_credentials_stays_on_mac(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'.ssh').mkdir();(root/'public').symlink_to(root/'.ssh')
            e=event();e['cwd']=directory;e['tool_input']['command']='cat public/key'
            self.assertFalse(display(e)['can_allow'])


class HookOutputTests(unittest.TestCase):
    def test_hook_forwards_pre_deny_but_never_pre_allow_as_permission_grant(self):
        import socketserver
        from types import SimpleNamespace
        spec=importlib.util.spec_from_file_location('passport_hook',ROOT/'bridge/hook.py')
        hook=importlib.util.module_from_spec(spec);spec.loader.exec_module(hook)
        for decision in ('deny','allow'):
            with tempfile.TemporaryDirectory(prefix='pcc-hook-',dir='/tmp') as directory:
                path=str(Path(directory)/'hook.sock')
                class Handler(socketserver.StreamRequestHandler):
                    def handle(self):
                        incoming=json.loads(self.rfile.readline())
                        self.server.received=incoming
                        self.wfile.write(json.dumps({'hookSpecificOutput':{'hookEventName':'PreToolUse',
                            'permissionDecision':decision}}).encode()+b'\n')
                with socketserver.UnixStreamServer(path,Handler) as server:
                    thread=threading.Thread(target=server.handle_request,daemon=True);thread.start()
                    e=event('PreToolUse');e['tool_name']='request_permissions'
                    e['tool_input']={'permissions':{'network':{'enabled':True}}}
                    output=io.StringIO()
                    with mock.patch.object(hook,'check_directory',return_value=Path(path)),mock.patch.object(hook.sys,'stdin',SimpleNamespace(buffer=io.BytesIO(json.dumps(e).encode()))),mock.patch.object(hook.sys,'stdout',output):
                        hook.main()
                    thread.join(timeout=1)
                    self.assertEqual(server.received['passport_hook_version'],3)
                    result=json.loads(output.getvalue())
                    if decision=='deny':self.assertEqual(result['hookSpecificOutput']['permissionDecision'],'deny')
                    else:self.assertEqual(result,{})


if __name__=='__main__':unittest.main()
