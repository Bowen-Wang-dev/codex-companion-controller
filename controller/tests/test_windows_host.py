"""Windows host transport, security and executable entry regressions."""
import json
import os
from pathlib import Path
import socket
import socketserver
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'bridge'), str(ROOT/'scripts')]
import ipc_path
import host_platform
import launch_desktop
from ipc_fixture import ipc_server


@unittest.skipUnless(sys.platform == 'win32', 'Windows native security/entry points')
class WindowsHostTests(unittest.TestCase):
    def test_loopback_requires_auth_before_dispatch(self):
        received=[]
        class Handler(socketserver.StreamRequestHandler):
            def handle(self):
                received.append(json.loads(self.rfile.readline()))
                self.wfile.write(b'{"ok":true}\n')
        with ipc_server(Handler) as server:
            self.assertEqual(server.server_address[0], '127.0.0.1')
            for payload in (b'wrong\n{"type":"shutdown"}\n', b'{"type":"shutdown"}\n'):
                with socket.create_connection(server.server_address, timeout=2) as client:
                    client.sendall(payload)
                    try:self.assertEqual(client.recv(100), b'')
                    except ConnectionResetError:pass
            self.assertEqual(received, [])
            with ipc_path.connect() as client:
                client.sendall(b'{"type":"status"}\n')
                self.assertEqual(json.loads(client.makefile('rb').readline()), {'ok':True})
            self.assertEqual(received, [{'type':'status'}])
            from windows_security import private_file
            private_file(ipc_path.SOCKET)

    def test_lifetime_lock_refuses_second_bridge_and_releases_on_close(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'ipc/endpoint.json'
            with mock.patch.object(ipc_path, 'SOCKET', path):
                lease=ipc_path.acquire_endpoint()
                try:
                    with self.assertRaisesRegex(RuntimeError, '另一份'):ipc_path.acquire_endpoint()
                finally:lease.close()
                lease=ipc_path.acquire_endpoint();lease.close()

    def test_broad_directory_and_file_acls_fail_closed(self):
        from windows_security import secure_directory, private_file, protect_file
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'broad';path.mkdir()
            with self.assertRaises(PermissionError):secure_directory(path)
            secure_directory(path, restrict_existing=True)
            value=Path(folder)/'broad.json';value.write_text('{}')
            with self.assertRaises(PermissionError):private_file(value)
            protect_file(value);private_file(value)

    def test_malformed_endpoint_cannot_redirect_to_a_remote_host(self):
        from windows_security import protect_file
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'ipc/endpoint.json'
            with mock.patch.object(ipc_path,'SOCKET',path):
                lease=ipc_path.acquire_endpoint()
                try:
                    for value in ({'port':True,'token':'a'*64}, {'port':2,'token':'not-a-token'}):
                        path.write_text(json.dumps(value));protect_file(path)
                        with mock.patch.object(socket.socket,'connect') as connect:
                            with self.assertRaises(ValueError):ipc_path.connect()
                            connect.assert_not_called()
                finally:lease.close()

    def test_usb_discovery_excludes_unrelated_com_ports(self):
        from types import SimpleNamespace
        devices=[SimpleNamespace(device='COM4',vid=0x303A,pid=0x1001),
                 SimpleNamespace(device='COM1',vid=None,pid=None),
                 SimpleNamespace(device='COM9',vid=0x303A,pid=0x9999)]
        with mock.patch('serial.tools.list_ports.comports',return_value=devices):
            self.assertEqual(host_platform.usb_ports(),['COM4'])

    def test_windows_app_probe_fails_closed(self):
        for value,expected in [(json.dumps([r'C:\Program Files\WindowsApps\OpenAI.Codex_1_x64__test\app\ChatGPT.exe']),True),('[]',False)]:
            with mock.patch.object(launch_desktop,'powershell',return_value=value):
                self.assertIs(launch_desktop.app_is_running(),expected)
        with mock.patch.object(launch_desktop,'powershell',return_value='[null]'):
            with self.assertRaises(RuntimeError):launch_desktop.app_is_running()

    def test_native_relay_preserves_unicode_quoted_args_and_exit_code(self):
        executable=ROOT/'private/app-relay.exe'
        if not executable.exists():self.skipTest('Run setup_windows.py --setup-only first')
        args=['space here', '中文目录', 'quote " inside', '& echo must-stay-data', 'C:\\path with space\\']
        code='import json,sys; print(json.dumps(sys.argv[1:],ensure_ascii=False)); sys.exit(7)'
        result=subprocess.run([str(executable),'-c',code,*args],
                              env=dict(os.environ,PASSPORT_REAL_CODEX=sys.executable,PYTHONUTF8='1'),
                              capture_output=True,encoding='utf-8',timeout=10)
        self.assertEqual(result.returncode,7,result.stderr)
        self.assertEqual(json.loads(result.stdout),args)

    def test_hook_command_preserves_stdin_and_quoted_unicode_path(self):
        from install_hooks import hook_command
        with tempfile.TemporaryDirectory(prefix="中文 path ' ") as folder:
            root=Path(folder);(root/'bridge').mkdir()
            (root/'bridge/hook.py').write_text('import sys\nsys.stdout.buffer.write(sys.stdin.buffer.read())\n',encoding='utf-8')
            command=hook_command(root).split()
            payload=json.dumps({'event':'中文 payload','quote':"a'b"},ensure_ascii=False).encode('utf-8')
            result=subprocess.run(command,input=payload,capture_output=True,timeout=10)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(result.stdout,payload)


if __name__ == '__main__':unittest.main()
