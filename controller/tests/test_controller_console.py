"""Regression tests for the unified console's App/Bridge lifecycle choice."""
import sys
from pathlib import Path
import unittest
from unittest import mock

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import controller_console


class ConsoleLifecycleTests(unittest.TestCase):
    def test_app_probe_accepts_running_and_stopped(self):
        with mock.patch.object(controller_console.subprocess,'run',return_value=mock.Mock(returncode=0)) as run:
            self.assertTrue(controller_console.app_is_running())
            run.assert_called_once()
        with mock.patch.object(controller_console.subprocess,'run',return_value=mock.Mock(returncode=1)):
            self.assertFalse(controller_console.app_is_running())

    def test_app_probe_rejects_probe_failure(self):
        with mock.patch.object(controller_console.subprocess,'run',return_value=mock.Mock(returncode=2)):
            with self.assertRaisesRegex(RuntimeError,'无法检查'):
                controller_console.app_is_running()


if __name__=='__main__':unittest.main()
