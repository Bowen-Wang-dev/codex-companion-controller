"""Regression tests for the unified console's App/Bridge lifecycle choice."""
import sys
from pathlib import Path
import unittest
from unittest import mock
import subprocess

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import controller_console
import launch_desktop


class ConsoleLifecycleTests(unittest.TestCase):
    def test_app_probe_accepts_running_and_stopped(self):
        self.addCleanup(mock.patch.stopall)
        mock.patch.object(launch_desktop,'WINDOWS',False).start()
        with mock.patch.object(controller_console.subprocess,'run',return_value=mock.Mock(returncode=0)) as run:
            self.assertTrue(controller_console.app_is_running())
            run.assert_called_once()
        with mock.patch.object(controller_console.subprocess,'run',return_value=mock.Mock(returncode=1)):
            self.assertFalse(controller_console.app_is_running())

    def test_app_probe_rejects_probe_failure(self):
        with mock.patch.object(launch_desktop,'WINDOWS',False), mock.patch.object(controller_console.subprocess,'run',return_value=mock.Mock(returncode=2)):
            with self.assertRaisesRegex(RuntimeError,'无法检查'):
                controller_console.app_is_running()

    def test_hooks_menu_targets_repository_and_propagates_install_failure(self):
        failure=subprocess.CalledProcessError(1,['fixture'])
        with mock.patch('builtins.input',return_value='YES'),mock.patch.object(controller_console.subprocess,'run',side_effect=failure) as run,mock.patch('builtins.print') as output:
            with self.assertRaises(subprocess.CalledProcessError):controller_console.hooks_menu()
        self.assertEqual(run.call_args.args[0][-1],str(ROOT.parent))
        self.assertTrue(run.call_args.kwargs['check'])
        self.assertFalse(any('请在 Codex 审阅' in str(call) for call in output.call_args_list))


if __name__=='__main__':unittest.main()
