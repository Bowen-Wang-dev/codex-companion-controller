"""Real TLS regressions: a half-open client must not stall device reconnects."""
import http.client
import json
from pathlib import Path
import socket
import ssl
import sys
import tempfile
import time
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'bridge'))
import wireless
from service import Broker
from tls_material import create_certificate


class WirelessResilienceTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        path = Path(self.directory.name)
        (path / 'wireless.json').write_text(json.dumps({'token': 'a' * 64}))
        create_certificate(path, '127.0.0.1')
        self.context = ssl.create_default_context(cafile=str(path / 'bridge-cert.pem'))
        with mock.patch.object(wireless, 'PRIVATE', path):
            self.server = wireless.start_https(Broker(), port=0)
        self.addCleanup(self.stop_server)

    def stop_server(self):
        self.server.shutdown()
        self.server.server_close()

    def test_incomplete_tls_handshake_does_not_block_real_device(self):
        stalled = socket.create_connection(('127.0.0.1', self.server.server_port), timeout=1)
        self.addCleanup(stalled.close)
        # No ClientHello: an interrupted/probing client must not own accept().
        client = http.client.HTTPSConnection('127.0.0.1', self.server.server_port,
                                             context=self.context, timeout=.8)
        try:
            client.request('POST', '/device', json.dumps({'type': 'hello', 'boot': 'test-boot'}),
                           {'Authorization': 'Bearer ' + 'a' * 64})
            response = client.getresponse()
            self.assertEqual(response.status, 200)
            self.assertEqual(json.loads(response.read())['boot'], 'test-boot')
        finally:
            client.close()
            stalled.close()

    def test_persistent_polling_has_complete_ordered_snapshots(self):
        client = http.client.HTTPSConnection('127.0.0.1', self.server.server_port,
                                             context=self.context, timeout=1)
        self.addCleanup(client.close)
        previous=0;connection=None
        for index in range(40):
            client.request('POST','/device',json.dumps({'type':'hello','boot':'persistent'}),
                           {'Authorization':'Bearer '+'a'*64})
            response=client.getresponse();self.assertEqual(response.status,200)
            packet=json.loads(response.read())
            self.assertEqual(packet['boot'],'persistent')
            self.assertGreater(packet['seq'],previous);previous=packet['seq']
            if connection is None:connection=client.sock
            self.assertIs(client.sock,connection)

    def test_stale_connection_reconnects_without_reusing_old_reply(self):
        for index in range(2):
            client=http.client.HTTPSConnection('127.0.0.1',self.server.server_port,
                                               context=self.context,timeout=1)
            try:
                client.request('POST','/device',json.dumps({'type':'hello','boot':'reconnect-'+str(index)}),
                               {'Authorization':'Bearer '+'a'*64})
                response=client.getresponse()
                self.assertEqual(json.loads(response.read())['boot'],'reconnect-'+str(index))
            finally:client.close()


class WirelessUnitTests(unittest.TestCase):
    def test_worker_performs_tls_and_bounds_connection_lifetime(self):
        server = object.__new__(wireless.DeviceHTTPServer)
        request = mock.Mock()
        connection = mock.Mock()
        server.tls_context = mock.Mock()
        server.tls_context.wrap_socket.return_value = connection
        with mock.patch.object(wireless.ThreadingHTTPServer, 'process_request_thread') as parent:
            server.process_request_thread(request, ('127.0.0.1', 1234))
        request.settimeout.assert_called_once_with(3)
        server.tls_context.wrap_socket.assert_called_once_with(request, server_side=True)
        connection.settimeout.assert_called_once_with(10)
        connection.setsockopt.assert_called_once_with(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        parent.assert_called_once_with(connection, ('127.0.0.1', 1234))

    def test_failed_handshake_closes_only_its_connection(self):
        server = object.__new__(wireless.DeviceHTTPServer)
        server.tls_context = mock.Mock()
        server.tls_context.wrap_socket.side_effect = TimeoutError()
        server.shutdown_request = mock.Mock()
        request = mock.Mock()
        with mock.patch.object(wireless.ThreadingHTTPServer, 'process_request_thread') as parent:
            server.process_request_thread(request, ('127.0.0.1', 1234))
        server.shutdown_request.assert_called_once_with(request)
        parent.assert_not_called()

    def test_chinese_snapshot_size_and_lossless_permission_fields(self):
        original = {'review_text': '申请读取和写入目录的具体权限范围及原因' * 25,
                    'scope': '仅限本轮申请的权限', 'digest': 'd' * 64,
                    'history': ['本轮响应已结束并等待你查看结果'] * 8}
        old = json.dumps(original, separators=(',', ':')).encode()
        response = wireless.encode_snapshot(original)
        self.assertGreater(len(old), len(response))
        self.assertLess(len(response), 4096)
        self.assertEqual(json.loads(response), original)

    def test_large_history_is_omitted_without_touching_approval(self):
        original = {'review_text': '申请的完整路径与权限', 'history': ['事件' * 1000],
                    'digest': 'd' * 64, 'can_allow': False, 'can_deny': True}
        payload = json.loads(wireless.encode_snapshot(original))
        self.assertEqual(payload['history'], [])
        self.assertEqual({k: v for k, v in payload.items() if k != 'history'},
                         {k: v for k, v in original.items() if k != 'history'})
        self.assertTrue(original['history'])

    def test_unbounded_approval_is_rejected_without_truncation(self):
        with self.assertRaises(ValueError):
            wireless.encode_snapshot({'review_text': '权限' * 3000})

    def test_network_counters_and_reconnect_are_bound_to_hello(self):
        broker = Broker()
        hello = {'type': 'hello', 'boot': 'boot', 'net': [0, 0, 0, 0]}
        broker.device_message(hello, 'wifi')
        broker.last_seen -= 6
        hello['net'] = [1, 200, 2, 3]
        broker.device_message(hello, 'wifi')
        status = broker.status()
        self.assertEqual(status['reconnect_count'], 1)
        self.assertEqual(status['network']['wifi_disconnects'], 1)
        self.assertEqual(status['network']['http_phase'], 3)
        self.assertTrue(status['online'])
        broker.device_message(dict(hello, net=[True, -1, 'bad', None]), 'wifi')
        self.assertEqual(broker.status()['network'], status['network'])


if __name__ == '__main__':
    unittest.main()
