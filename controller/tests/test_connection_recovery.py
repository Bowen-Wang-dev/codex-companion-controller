"""Recovery regressions use synthetic archives/addresses and mocked USB devices."""
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest import mock

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
sys.path.insert(0,str(ROOT/'bridge'))
import connection_diagnostics as diagnostics
import launch_desktop as launcher
import recover_bridge as recovery
import restart_desktop_bridge as restart
from usb_transport import open_usb


def archive(app,version,files):
    files={'package.json':json.dumps({'version':version}).encode(),**files}
    header={'files':{}};payload=b''
    for name,data in files.items():
        entry=header
        parts=name.split('/')
        for part in parts[:-1]:entry=entry.setdefault('files',{}).setdefault(part,{'files':{}})
        entry['files'][parts[-1]]={'size':len(data),'offset':str(len(payload))}
        payload+=data
    raw=json.dumps(header).encode();path=app/'Contents/Resources/app.asar'
    path.parent.mkdir(parents=True);path.write_bytes(struct.pack('<4I',4,len(raw)+8,0,len(raw))+raw+payload)


class RecoveryTests(unittest.TestCase):
    def test_adapter_checks_all_registered_chunks(self):
        sources={'a.js':b'CODEX_APP_SERVER_FORCE_CLI','b.js':b'CODEX_CLI_PATH'}
        known={'test':{p:hashlib.sha256(b).hexdigest() for p,b in sources.items()}}
        with tempfile.TemporaryDirectory() as folder, mock.patch.object(launcher,'VERIFIED_BUILDS',known):
            app=Path(folder);archive(app,'test',sources)
            self.assertEqual(launcher.verify_build(app),'test')
            path=app/'Contents/Resources/app.asar';path.write_bytes(path.read_bytes().replace(b'CODEX_CLI_PATH',b'CODEX_CLI_FAIL'))
            with self.assertRaisesRegex(ValueError,'已变化'):launcher.verify_build(app)

    def test_unknown_app_and_missing_chunk_fail_with_actionable_error(self):
        for version,known,error in [('new',{},'尚未核对'),('test',{'test':{'missing.js':'x'}},'布局无法识别')]:
            with tempfile.TemporaryDirectory() as folder,mock.patch.object(launcher,'VERIFIED_BUILDS',known):
                app=Path(folder);archive(app,version,{})
                with self.assertRaisesRegex(ValueError,error):launcher.verify_build(app)

    def test_dhcp_address_change_is_reported_without_modifying_pairing(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'private').mkdir();path=root/'private/wireless.json'
            original='{"ip":"192.168.50.10","token":"synthetic"}'
            path.write_text(original)
            with mock.patch.object(diagnostics,'local_ipv4',return_value=['10.10.0.20']),mock.patch.object(diagnostics,'request',side_effect=ConnectionRefusedError):
                report=diagnostics.inspect(root)
            self.assertTrue(report['address_changed']);self.assertIsNone(report['status'])
            self.assertEqual(path.read_text(),original)

    def test_local_addresses_ignore_loopback_ipv6_and_duplicates(self):
        fake=mock.Mock(stdout='inet 127.0.0.1\ninet6 fe80::1\ninet 169.254.1.3\ninet 10.10.0.20\ninet 10.10.0.20')
        with mock.patch.object(diagnostics.subprocess,'run',return_value=fake):
            self.assertEqual(diagnostics.local_ipv4(),['10.10.0.20'])

    def test_recovery_never_stops_a_pending_approval(self):
        with mock.patch.object(recovery,'request') as request:
            with self.assertRaisesRegex(RuntimeError,'待处理审批'):
                recovery.stop_idle_bridge({'permission_pending':True})
            request.assert_not_called()

    def test_running_app_does_not_stop_bridge_or_close_chat(self):
        with mock.patch.object(restart,'verify_build',return_value='test'), mock.patch.object(restart,'inspect',return_value={}), mock.patch.object(restart,'show'), mock.patch('builtins.input',return_value=''), mock.patch.object(restart.subprocess,'run',return_value=mock.Mock(returncode=0)), mock.patch.object(restart,'stop_idle_bridge') as stop, mock.patch.object(restart.os,'execv') as execute:
            with self.assertRaisesRegex(RuntimeError,'仍在运行'):restart.main()
            stop.assert_not_called();execute.assert_not_called()

    def test_macos_termios_permission_error_becomes_actionable_oserror(self):
        import termios
        serial=mock.Mock();device=serial.Serial.return_value
        device.open.side_effect=termios.error(1,'synthetic permission error')
        with self.assertRaises(PermissionError) as raised:open_usb('/dev/test',serial)
        self.assertEqual(raised.exception.errno,1)
        device.close.assert_called_once()

    def test_usb_control_lines_set_before_open_and_failure_closes_handle(self):
        serial=mock.Mock();device=serial.Serial.return_value
        def opened():
            self.assertIs(device.dtr,False);self.assertIs(device.rts,False)
            self.assertEqual(device.port,'/dev/test')
        device.open.side_effect=opened
        self.assertIs(open_usb('/dev/test',serial),device)
        device.open.side_effect=PermissionError('synthetic')
        with self.assertRaises(PermissionError):open_usb('/dev/test',serial)
        device.close.assert_called_once()


if __name__=='__main__':unittest.main()
