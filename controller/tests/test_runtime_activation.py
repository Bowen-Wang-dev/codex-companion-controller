"""Runtime activation regression tests use synthetic files and mocked services."""
import copy
import json
from pathlib import Path
import shlex
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import activate_migrated_runtime as activation
import launch_desktop


class ActivationTests(unittest.TestCase):
    def test_exact_hook_replacement_preserves_other_commands_and_metadata(self):
        old, new = Path('/old runtime'), Path('/new runtime')
        command = '/usr/bin/python3 ' + shlex.quote(str(old / 'bridge/hook.py'))
        data = {'extra': 1, 'hooks': {'Stop': [{'matcher': 'x', 'hooks': [
            {'command': command, 'timeout': 1}, {'command': command + ' --other'}]}]}}
        original = copy.deepcopy(data)
        result = activation.migrate_hooks(data, old, new)
        self.assertEqual(data, original)
        handlers = result['hooks']['Stop'][0]['hooks']
        self.assertEqual(handlers[0], {'command': '/usr/bin/python3 ' + shlex.quote(str(new / 'bridge/hook.py')), 'timeout': 1})
        self.assertEqual(handlers[1], original['hooks']['Stop'][0]['hooks'][1])
        self.assertEqual(result['hooks']['Stop'][0]['matcher'], 'x')
        self.assertEqual(result['extra'], 1)
        self.assertEqual(activation.migrate_hooks(result, old, new), result)

    def test_existing_new_hook_is_not_duplicated(self):
        old='/usr/bin/python3 '+shlex.quote(str(Path('/old')/'bridge/hook.py'))
        new='/usr/bin/python3 '+shlex.quote(str(Path('/new')/'bridge/hook.py'))
        data = {'hooks': {'Stop': [{'hooks': [{'command': old},
            {'command': 'third-party'}]}, {'hooks': [{'command': new}]}]}}
        result = activation.migrate_hooks(data, Path('/old'), Path('/new'))
        self.assertEqual([h['command'] for g in result['hooks']['Stop'] for h in g['hooks']],
                         ['third-party', new])

    def test_ledger_refresh_keeps_backup_and_private_permissions(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder); old = base / 'old'; new = base / 'new'; backup = base / 'backup'
            for p in (old / 'private', new / 'private', backup): p.mkdir(parents=True)
            source = old / 'private/token-ledger.json'; target = new / 'private/token-ledger.json'
            source.write_text('{"version":2,"total":42}'); target.write_text('{"version":2,"total":1}')
            activation.copy_ledger(old, new, backup)
            self.assertEqual(source.read_bytes(), target.read_bytes())
            self.assertEqual(json.loads((backup / 'token-ledger.before.json').read_text())['total'], 1)
            if sys.platform == 'win32':
                from windows_security import private_file
                private_file(target)
            else:self.assertEqual(target.stat().st_mode & 0o777, 0o600)

    def test_invalid_ledger_does_not_overwrite_destination(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            for name in ('old/private', 'new/private', 'backup'): (base / name).mkdir(parents=True)
            (base / 'old/private/token-ledger.json').write_text('invalid')
            target = base / 'new/private/token-ledger.json'; target.write_text('{}')
            with self.assertRaises(ValueError): activation.copy_ledger(base / 'old', base / 'new', base / 'backup')
            self.assertEqual(target.read_text(), '{}')

    @unittest.skipIf(sys.platform == 'win32', 'macOS runtime migration')
    def test_running_app_never_stops_services(self):
        with tempfile.TemporaryDirectory() as folder:
            old = Path(folder) / 'old'; (old / 'bridge').mkdir(parents=True)
            (old / 'bridge/service.py').touch()
            with mock.patch.object(launch_desktop, 'verify_build', return_value='test'), \
                 mock.patch.object(activation.subprocess, 'run', return_value=mock.Mock(returncode=0)), \
                 mock.patch.object(activation, 'request_at') as request:
                with self.assertRaisesRegex(RuntimeError, 'App 仍在运行'):
                    activation.activate(old, Path(folder) / 'new')
                request.assert_not_called()

    @unittest.skipIf(sys.platform == 'win32', 'macOS runtime migration')
    def test_pending_approval_prevents_shutdown_and_copy(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder); old = base / 'old'; new = base / 'new'
            (old / 'bridge').mkdir(parents=True); (old / 'bridge/service.py').touch()
            for root in (old, new):
                (root / 'private').mkdir(parents=True)
                for name in ('wireless.json', 'bridge-cert.pem', 'bridge-key.pem', 'token_rates.json'):
                    (root / 'private' / name).write_text('{}')
            with mock.patch.object(launch_desktop, 'verify_build', return_value='test'), \
                 mock.patch.dict(activation.os.environ, {'CODEX_HOME': str(base / 'home')}), \
                 mock.patch.object(activation.subprocess, 'run', return_value=mock.Mock(returncode=1)), \
                 mock.patch.object(activation, 'request_at', side_effect=[None, {'project_root':str(old.resolve()), 'permission_pending':True}]) as request, \
                 mock.patch.object(activation, 'copy_ledger') as copy_ledger:
                with self.assertRaisesRegex(RuntimeError, '待处理审批'): activation.activate(old, new)
                self.assertEqual(request.call_count, 2)
                copy_ledger.assert_not_called()


if __name__ == '__main__': unittest.main()
