import os
from pathlib import Path
import socket
import sys
import tempfile
import unittest
from unittest import mock

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'bridge'))
import desktop_connection as desktop


class DesktopProbeTests(unittest.TestCase):
    def test_official_socket_discovery(self):
        self.assertEqual(desktop.control_socket('/test/codex'),Path('/test/codex/app-server-control/app-server-control.sock'))

    def test_probe_only_initializes_and_lists_loaded_threads(self):
        client=mock.Mock()
        client.rpc.side_effect=[{'userAgent':'test-server'},{'data':['app-thread']}]
        with mock.patch.object(desktop,'validate_socket'),mock.patch.object(desktop,'NativeClient',return_value=client):
            report=desktop.probe('/unused','app-thread')
        self.assertTrue(report['connected']);self.assertTrue(report['expected_loaded'])
        self.assertEqual([call.args[0] for call in client.rpc.call_args_list],['initialize','thread/loaded/list'])
        client.send.assert_called_once_with({'method':'initialized'});client.close.assert_called_once()

    def test_no_connection_is_not_a_success_and_closes_partial_client(self):
        client=mock.Mock();client.rpc.side_effect=RuntimeError('timeout')
        with mock.patch.object(desktop,'validate_socket'),mock.patch.object(desktop,'NativeClient',return_value=client):
            report=desktop.probe('/unused','app-thread')
        self.assertFalse(report['connected']);self.assertFalse(report['expected_loaded'])
        client.close.assert_called_once()

    def test_unsafe_socket_directory_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'control.sock'
            with socket.socket(socket.AF_UNIX) as server:
                server.bind(str(path));os.chmod(folder,0o700)
                self.assertEqual(desktop.validate_socket(path),path)
                os.chmod(folder,0o777)
                with self.assertRaises(ValueError):desktop.validate_socket(path)
                os.chmod(folder,0o700)

    def test_regular_file_is_not_a_control_endpoint(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'not-a-socket';path.write_text('test')
            with self.assertRaises(ValueError):desktop.validate_socket(path)
