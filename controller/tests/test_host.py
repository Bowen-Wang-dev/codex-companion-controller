import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import sys
import threading
import time
import unittest
import socket
import tempfile
from unittest import mock
from types import SimpleNamespace
import errno
import stat

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'bridge'))
import ipc_path
from service import Broker
from account import AccountClient
from ipc_path import SOCKET, check_directory
spec = importlib.util.spec_from_file_location('flash', ROOT/'scripts/flash.py')
flash = importlib.util.module_from_spec(spec)
spec.loader.exec_module(flash)


def backup(ota=False, overlap=False):
    image = bytearray(b'\xff' * flash.SIZE)
    table = b''
    for name, kind, subtype, offset, size in [('nvs', 1, 2, 0x9000, 0x6000),
       ('factory', 0, 16 if ota else 0, 0x10000, 0x7f0000)]:
        table += struct.pack('<HBBII16sI', 0x50aa, kind, subtype, offset, size, name.encode(), 0)
    if overlap:
        table += struct.pack('<HBBII16sI', 0x50aa, 1, 0, 0x20000, 0x1000, b'cardid', 0)
    table += b'\xeb\xeb' + b'\xff'*14 + hashlib.md5(table).digest()
    image[0x8000:0x8000+len(table)] = table
    return image


class IPCTests(unittest.TestCase):
    def test_short_path_and_real_bind(self):
        self.assertLess(len(bytes(SOCKET)), 104)
        check_directory(create=True)
        address = SOCKET.with_name('check.sock')
        with socket.socket(socket.AF_UNIX) as server:
            try:
                server.bind(str(address))
                server.listen(1)
                with socket.socket(socket.AF_UNIX) as client:
                    client.connect(str(address))
                    connection, _ = server.accept()
                    with connection:
                        client.sendall(b'check')
                        self.assertEqual(connection.recv(5), b'check')
            finally:
                address.unlink(missing_ok=True)


class EndpointTests(unittest.TestCase):
    def exercise(self, active):
        with tempfile.TemporaryDirectory() as directory:
            path = mock.MagicMock()
            path.parent = Path(directory)
            path.lstat.return_value = SimpleNamespace(st_mode=stat.S_IFSOCK | 0o600, st_uid=ipc_path.os.getuid())
            probe = mock.MagicMock()
            if not active:
                probe.connect.side_effect = ConnectionRefusedError(errno.ECONNREFUSED, 'stale')
            with mock.patch.object(ipc_path, 'SOCKET', path), mock.patch.object(ipc_path.socket, 'socket') as factory:
                factory.return_value.__enter__.return_value = probe
                if active:
                    with self.assertRaises(RuntimeError): ipc_path.acquire_endpoint()
                    path.unlink.assert_not_called()
                else:
                    lease = ipc_path.acquire_endpoint()
                    try:
                        path.unlink.assert_called_once()
                        with self.assertRaises(RuntimeError): ipc_path.acquire_endpoint()
                    finally:
                        lease.close()

    def test_stale_cleanup_and_duplicate_lock(self): self.exercise(False)
    def test_live_listener_not_removed(self): self.exercise(True)


class FlashTests(unittest.TestCase):
    def app(self, size=0xa0930):
        app = bytearray(size); app[0] = 0xe9; struct.pack_into('<H', app, 12, 5)
        return app

    def test_safe_app_only(self):
        p = flash.plan(backup(), self.app())
        self.assertEqual(p['offset'], 0x10000)
        self.assertEqual(p['erase_end'] % 4096, 0)
        self.assertFalse(p['erase_all'] or p['writes_partition_table'] or p['writes_bootloader'])

    def test_ota_refused(self):
        with self.assertRaises(ValueError): flash.plan(backup(ota=True), self.app())

    def test_corrupt_md5_refused(self):
        data = backup(); data[0x8008] ^= 1
        with self.assertRaises(ValueError): flash.plan(data, self.app())

    def test_overlap_refused(self):
        with self.assertRaises(ValueError): flash.plan(backup(overlap=True), self.app())

    def test_identity_boundary_refused(self):
        with self.assertRaises(ValueError): flash.plan(backup(), self.app(0x300000))

    def test_other_chip_refused(self):
        app = self.app(); app[12] = 9
        with self.assertRaises(ValueError): flash.plan(backup(), app)


class BrokerTests(unittest.TestCase):
    def broker(self):
        b = Broker(); b.boot = 'boot'; b.last_seen = time.monotonic(); return b

    def test_offline_native_fallback(self):
        self.assertEqual(Broker().permission({}), {})

    def test_bound_deny_duplicate_and_allow(self):
        b = self.broker(); result = []
        t = threading.Thread(target=lambda: result.append(b.permission({'cwd': '/tmp/project', 'tool_input': {'command': 'pwd'}}, timeout=2)))
        t.start()
        for _ in range(100):
            if b.request: break
            time.sleep(.01)
        r = b.request
        msg = {'boot': 'boot', 'epoch': b.epoch, 'id': r['id'], 'digest': r['digest'], 'choice': 'allow'}
        self.assertFalse(b.decision(msg))
        msg['choice'] = 'deny'; msg['epoch'] = 'stale'
        self.assertFalse(b.decision(msg)); msg['epoch'] = b.epoch
        self.assertTrue(b.decision(msg)); self.assertFalse(b.decision(msg))
        t.join()
        self.assertEqual(result[0]['hookSpecificOutput']['decision']['behavior'], 'deny')

    def test_expiry_native_fallback(self):
        self.assertEqual(self.broker().permission({}, timeout=.02), {})

    def test_unknown_usage_stays_unknown(self):
        data = self.broker().snapshot()
        self.assertIsNone(data['primary']); self.assertIsNone(data['resets'])

    def test_stop_does_not_claim_success(self):
        b = self.broker(); b.event({'hook_event_name': 'UserPromptSubmit', 'session_id': 's'})
        b.event({'hook_event_name': 'Stop', 'session_id': 's'})
        self.assertEqual(b.state, 'completed')

    def test_account_mutations_refused(self):
        client = AccountClient.__new__(AccountClient)
        with self.assertRaises(ValueError): client.rpc('account/rateLimitResetCredit/consume', {})

    def test_account_normalizes_and_removes_identity(self):
        client = AccountClient.__new__(AccountClient)
        usage = {'rateLimitsByLimitId': {'codex': {'primary': {'usedPercent': 125, 'resetsAt': 123, 'windowDurationMins': 300}}},
                 'accountId': 'private-id', 'rateLimitResetCredits': {'availableCount': 2, 'credits': [{'id': 'secret-credit'}]}}
        client.rpc = lambda method, params=None: {'account': {'type': 'chatgpt', 'planType': 'plus', 'email': 'private@example.invalid'}} if method=='account/read' else usage
        result = client.read()
        self.assertEqual(result['limits'][0]['remaining'], 0)
        self.assertEqual(result['resets'], 2)
        self.assertNotIn('private', json.dumps(result)); self.assertNotIn('secret-credit', json.dumps(result))

    def test_api_key_does_not_impersonate_subscription(self):
        client = AccountClient.__new__(AccountClient)
        client.rpc = lambda *args: {'account': {'type': 'apiKey'}}
        with self.assertRaises(RuntimeError): client.read()


if __name__ == '__main__': unittest.main()
