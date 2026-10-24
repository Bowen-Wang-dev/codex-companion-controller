import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT / 'bridge'))
from service import Broker

spec=importlib.util.spec_from_file_location('install_hooks',ROOT/'scripts/install_hooks.py')
installer=importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


def directory_event(name='PreToolUse', identifier='request-1', session='test-session'):
    return {'hook_event_name':name,'tool_name':'request_permissions','session_id':session,
            'tool_use_id':identifier,'turn_id':'test-turn','cwd':'/tmp/project',
            'tool_input':{'permissions':{'file_system':{'write':['/tmp/directory-test']}},
                          'reason':'test reason, not forwarded'}}


class NotificationTests(unittest.TestCase):
    def broker(self):
        b=Broker()
        b.device_message({'type':'hello','boot':'test-boot','firmware':'0.2.1','readonly_notices':True},'wifi')
        return b

    def test_directory_request_notifies_without_returning_a_grant(self):
        b=self.broker()
        self.assertEqual(b.event(directory_event()),{})
        data=b.snapshot()
        self.assertIn('/tmp/directory-test',data['project'])
        self.assertFalse(data['can_allow'] or data['can_deny'])
        self.assertNotIn('test reason',json.dumps(data))
        self.assertEqual(b.status()['hook_count'],1)
        self.assertFalse(b.decision({'boot':b.boot,'epoch':b.epoch,'id':data['req_id'],
                                     'digest':data['digest'],'choice':'allow'}))
        self.assertFalse(b.decision({'boot':b.boot,'epoch':b.epoch,'id':data['req_id'],
                                     'digest':data['digest'],'choice':'deny'}))

    def test_actual_network_only_request_is_not_silently_dropped(self):
        # Same tool arguments as the real desktop test on 2026-10-24.
        e=directory_event()
        e['tool_input']={'permissions':{'network':{'enabled':True}},
                         'reason':'test reason, not forwarded'}
        b=self.broker()
        self.assertEqual(b.event(e),{})
        data=b.snapshot()
        self.assertIn('req_id',data)
        self.assertIn('网络',data['command'])
        self.assertIn('网络',data['project'])
        self.assertFalse(data['can_allow'] or data['can_deny'])
        self.assertNotIn('test reason',json.dumps(data))
        self.assertTrue(b.status()['permission_notice_pending'])
        self.assertEqual(b.status()['tool_counts']['request_permissions'],1)
        self.assertEqual(b.status()['event_counts']['PreToolUse'],1)
        e['hook_event_name']='PostToolUse'
        b.event(e)
        self.assertNotIn('req_id',b.snapshot())

    def test_mixed_permissions_preserve_network_and_path_summary(self):
        b=self.broker();e=directory_event()
        e['tool_name']='functions.request_permissions'
        e['tool_input']['permissions']['network']={'enabled':True}
        b.event(e);data=b.snapshot()
        self.assertIn('网络',data['project'])
        self.assertIn('/tmp/directory-test',data['project'])
        self.assertFalse(data['can_allow'] or data['can_deny'])

    def test_false_empty_or_malformed_network_does_not_invent_request(self):
        for value in (False,1,'true',None):
            with self.subTest(value=value):
                b=self.broker();e=directory_event()
                e['tool_input']={'permissions':{'network':{'enabled':value}}}
                b.event(e)
                self.assertNotIn('req_id',b.snapshot())
        for permissions in ({},{'network':None},{'file_system':None}):
            b=self.broker();e=directory_event()
            e['tool_input']={'permissions':permissions}
            b.event(e)
            self.assertNotIn('req_id',b.snapshot())

    def test_network_duplicate_expiry_interrupt_and_reboot(self):
        b=self.broker();e=directory_event()
        e['tool_input']={'permissions':{'network':{'enabled':True}}}
        b.event(e);original=copy.deepcopy(b.notice)
        b.event(e);self.assertEqual(b.notice,original)
        b.notice['deadline']=time.monotonic()-1
        self.assertNotIn('req_id',b.snapshot())
        b.event(e)
        b.event({'hook_event_name':'Interrupt','session_id':'test-session'})
        self.assertIsNone(b.notice)
        b.event(e)
        b.device_message({'type':'hello','boot':'new-boot','readonly_notices':True},'wifi')
        self.assertIsNone(b.notice)

    def test_matching_post_clears_notice_other_session_does_not(self):
        b=self.broker();b.event(directory_event())
        b.event(directory_event('PostToolUse',session='other'))
        self.assertIsNotNone(b.notice)
        b.event(directory_event('PostToolUse',identifier='different'))
        self.assertIsNotNone(b.notice)
        b.event(directory_event('PostToolUse'))
        self.assertIsNone(b.notice)
        self.assertNotIn('req_id',b.snapshot())
        self.assertNotEqual(b.expression,'delight')

    def test_duplicates_keep_id_expiry_and_new_boot_cancels(self):
        b=self.broker();b.event(directory_event());original=copy.deepcopy(b.notice)
        b.event(directory_event());self.assertEqual(b.notice,original)
        b.notice['deadline']=time.monotonic()-1
        self.assertNotIn('req_id',b.snapshot())
        b.event(directory_event());self.assertIsNotNone(b.notice)
        b.device_message({'type':'hello','boot':'new-boot','readonly_notices':True},'wifi')
        self.assertIsNone(b.notice)

    def test_interrupt_clears_only_its_own_session(self):
        b=self.broker();b.event(directory_event())
        b.event({'hook_event_name':'Interrupt','session_id':'other'})
        self.assertIsNotNone(b.notice)
        b.event({'hook_event_name':'Interrupt','session_id':'test-session'})
        self.assertIsNone(b.notice)

    def test_old_firmware_never_receives_false_actionable_directory_notice(self):
        b=Broker();b.boot='old';b.last_seen=time.monotonic();b.event(directory_event())
        self.assertNotIn('req_id',b.snapshot())

    def test_non_directory_tool_does_not_raise_notice(self):
        b=self.broker();e=directory_event();e['tool_name']='Bash'
        b.event(e);self.assertIsNone(b.notice)


class HookInstallationTests(unittest.TestCase):
    def test_user_install_removes_stale_project_copy_by_default(self):
        import io,os
        with tempfile.TemporaryDirectory() as directory:
            base=Path(directory);project=base/'project';controller=project/'outputs/PassportController'
            local=project/'.codex/hooks.json';local.parent.mkdir(parents=True)
            local.write_text(json.dumps({'hooks':{'PreToolUse':[{'hooks':[
                {'command':installer.COMMAND,'timeout':1},{'command':'keep-other-hook'}]}]}}))
            with mock.patch.object(installer,'ROOT',controller),mock.patch.object(sys,'argv',['install_hooks.py','--user']),mock.patch.dict(os.environ,{'CODEX_HOME':str(base/'home')}),mock.patch('sys.stdout',new=io.StringIO()):
                installer.main()
            data=json.loads(local.read_text())
            self.assertEqual(data['hooks']['PreToolUse'][0]['hooks'],[{'command':'keep-other-hook'}])
            installed=json.loads((base/'home/hooks.json').read_text())
            self.assertEqual(installed['hooks']['PreToolUse'][0]['hooks'][0]['timeout'],115)
            self.assertEqual(len(list((controller/'private/hook-backups').glob('hooks.backup-*'))),1)

    def test_global_merge_preserves_other_hooks_and_is_idempotent(self):
        data={'description':'mine','hooks':{'PreToolUse':[{'matcher':'Bash','hooks':[{'type':'command','command':'other-hook'}]}]}}
        installer.merge(data);first=copy.deepcopy(data);installer.merge(data)
        self.assertEqual(data,first)
        self.assertEqual(data['hooks']['PreToolUse'][0]['hooks'][0]['command'],'other-hook')
        self.assertEqual(data['description'],'mine')

    def test_project_dedup_removes_only_controller_handlers(self):
        data={'hooks':{'PreToolUse':[{'hooks':[{'command':installer.COMMAND},{'command':'other-hook'}]}]}}
        installer.remove_ours(data)
        self.assertEqual(data['hooks']['PreToolUse'][0]['hooks'],[{'command':'other-hook'}])

    def test_save_backups_only_changed_files(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'hooks.json';path.write_text('{"hooks":{}}')
            installer.save(path,installer.merge)
            first=path.read_bytes();installer.save(path,installer.merge)
            self.assertEqual(path.read_bytes(),first)
            self.assertEqual(len(list(path.parent.glob('hooks.backup-*'))),1)
            self.assertEqual(path.stat().st_mode & 0o777,0o600)


if __name__=='__main__':unittest.main()
