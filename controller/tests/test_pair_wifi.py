"""Exercise the physical-consent/serial-open race without hardware or secrets."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('pair_wifi', ROOT / 'scripts/pair_wifi.py')
pair = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pair)
CERT = '-----BEGIN CERTIFICATE-----\nTEST\n-----END CERTIFICATE-----\n'


def configuration():
    return dict(type='provision', ssid='test-network', password='test-password',
                url='https://192.0.2.10:8765/device', token='a' * 64,
                cert=CERT, utc=1792771200)


def frame(message):
    return b'PC1 ' + json.dumps(message).encode() + b'\n'


class Clock:
    def __init__(self):
        self.now = 0

    def monotonic(self):
        self.now += .05
        return self.now


class Device:
    def __init__(self):
        self.is_open = False
        self.armed = False
        self.opens = 0
        self.boot = 'initial-boot'
        self.received = []
        self.pending = []
        self.drop_ack = False

    def open(self):
        # Reproduce the actual class of failure: open invalidates prior consent.
        self.opens += 1
        self.is_open = True
        self.boot = 'opened-boot'
        self.armed = False
        assert self.dtr is False and self.rts is False

    def close(self):
        self.is_open = False

    def __enter__(self):
        assert self.is_open
        return self

    def __exit__(self, *_):
        self.close()

    def read(self, _):
        if self.pending:
            return self.pending.pop(0)
        return frame(dict(type='hello', boot=self.boot, firmware='0.2.0'))

    def write(self, value):
        self.received.append(json.loads(value[4:]))
        if not self.drop_ack:
            self.pending.append(frame(dict(type='provisioned', boot=self.boot, ok=self.armed)))
        return len(value)


class PairingTests(unittest.TestCase):
    def setUp(self):
        self.clock = Clock()
        patcher = mock.patch.object(pair.time, 'monotonic', self.clock.monotonic)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_main_opens_before_consent_and_saves_only_after_ack(self):
        device = Device()
        prompts = []
        answers = iter(['test-network', '192.0.2.10', ''])

        def answer(prompt):
            prompts.append(prompt)
            value = next(answers)
            if 'q 取消' in prompt:
                self.assertTrue(device.is_open)
                self.assertEqual(device.opens, 1)
                device.armed = True
            return value

        with tempfile.TemporaryDirectory() as directory:
            private = Path(directory) / 'private'
            private.mkdir()
            pair.create_certificate(private, '192.0.2.10')
            (private / 'wireless.json').write_text(json.dumps({'ip': '192.0.2.10', 'token': 'a' * 64}))
            with mock.patch.object(pair, 'ROOT', Path(directory)), mock.patch.object(pair.glob, 'glob', return_value=['/dev/test']), mock.patch.object(pair.serial, 'Serial', return_value=device) as factory, mock.patch.object(pair.subprocess, 'check_output', return_value='192.0.2.10'), mock.patch.object(pair.getpass, 'getpass', return_value='test-password'), mock.patch('builtins.input', side_effect=answer), mock.patch('builtins.print'):
                pair.main()
            self.assertIsNone(factory.call_args.kwargs['port'])
            self.assertEqual(len(device.received), 1)
            self.assertEqual(device.received[0]['password'], 'test-password')
            active = private / 'wireless.json'
            self.assertEqual(active.stat().st_mode & 0o777, 0o600)
            self.assertEqual(json.loads(active.read_text())['token'], 'a' * 64)
            self.assertFalse((private / 'wireless-pending.json').exists())
            self.assertNotIn('test-password', ''.join(p.read_text() for p in private.iterdir()))

    def test_rejection_retries_with_same_open_port_and_fresh_consent(self):
        device = Device()
        count = 0

        def answer(_):
            nonlocal count
            count += 1
            if count == 2:
                device.armed = True
            return ''

        with mock.patch.object(pair.serial, 'Serial', return_value=device):
            with pair.open_device('/dev/test') as opened:
                pair.provision(opened, configuration(), ask=answer, say=lambda _: None)
        self.assertEqual(count, 2)
        self.assertEqual(len(device.received), 2)
        self.assertEqual(device.opens, 1)

    def test_reboot_while_user_confirms_requires_fresh_consent_before_send(self):
        device = Device()
        device.is_open = True
        count = 0

        def answer(_):
            nonlocal count
            count += 1
            if count == 1:
                device.boot = 'rebooted'
            device.armed = True
            return ''

        pair.provision(device, configuration(), ask=answer, say=lambda _: None)
        self.assertEqual(count, 2)
        self.assertEqual(len(device.received), 1)

    def test_missing_ack_is_not_retried_or_reported_success(self):
        device = Device()
        device.drop_ack = True
        with self.assertRaisesRegex(pair.PairingError, '未收到保存回执'):
            pair.provision(device, configuration(), ask=lambda _: '', say=lambda _: None)
        self.assertEqual(len(device.received), 1)

    def test_cancel_sends_nothing(self):
        device = Device()
        with self.assertRaisesRegex(pair.PairingError, '已取消'):
            pair.provision(device, configuration(), ask=lambda _: 'q', say=lambda _: None)
        self.assertEqual(device.received, [])

    def test_exhausted_retries_do_not_claim_storage_or_network_success(self):
        device = Device()
        with self.assertRaisesRegex(pair.PairingError, '未完成配对'):
            pair.provision(device, configuration(), ask=lambda _: '', say=lambda _: None)
        self.assertEqual(len(device.received), 3)

    def test_old_firmware_rejected_before_sending(self):
        device = mock.Mock()
        device.read.return_value = frame(dict(type='hello', boot='old', firmware='0.1.1'))
        with self.assertRaisesRegex(pair.PairingError, '不支持'):
            pair.provision(device, configuration(), ask=lambda _: '', say=lambda _: None)
        device.write.assert_not_called()

    def test_fragmented_and_unrelated_serial_lines(self):
        device = mock.Mock()
        encoded = frame(dict(type='hello', boot='live', firmware='0.2.0'))
        device.read.side_effect = [b'boot log\nPC1 not-json\nPC1 []\n' + encoded[:10], encoded[10:]]
        reader = pair.Reader(device)
        self.assertEqual(reader.poll(), [])
        self.assertEqual(reader.poll()[0]['boot'], 'live')

    def test_utf8_limits_and_no_secret_in_validation_error(self):
        good = configuration()
        good['ssid'] = '网' * 10
        self.assertEqual(json.loads(pair.encode_config(good)[4:])['ssid'], good['ssid'])
        for field, value in [('ssid', '网' * 11), ('password', 'secret-' * 10),
                             ('ssid', 'bad\0ssid'), ('cert', 'no certificate'), ('token', 'x' * 64)]:
            with self.subTest(field=field):
                bad = dict(good, **{field: value})
                with self.assertRaises(pair.PairingError) as caught:
                    pair.encode_config(bad)
                self.assertNotIn(value, str(caught.exception))


if __name__ == '__main__':
    unittest.main()
