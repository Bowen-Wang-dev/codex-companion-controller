import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import sys
import unittest
from unittest.mock import patch, Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))

spec = importlib.util.spec_from_file_location('firmware_update', Path(__file__).resolve().parents[1]/'scripts/firmware_update.py')
update = importlib.util.module_from_spec(spec)
spec.loader.exec_module(update)


class ImageGateTests(unittest.TestCase):
    def setUp(self):
        platform=patch.object(update,'WINDOWS',True);platform.start();self.addCleanup(platform.stop)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root/'firmware/main').mkdir(parents=True)
        (self.root/'dist').mkdir()
        (self.root/'firmware/CMakeLists.txt').write_text('set(PROJECT_VER "companion-0.2.13")')
        (self.root/'firmware/main/main.c').write_text('new UI')
        image = b'firmwareCOMPANION_UI_LANGUAGE=zh-CN\0'
        (self.root/'dist/PassportController.bin').write_bytes(image)
        self.manifest = dict(version='0.2.13', chip='esp32c3', size=len(image),
                             sha256=hashlib.sha256(image).hexdigest(),
                             source_sha256=update.source_digest(self.root),
                             ui_language='zh-CN',
                             apple_assets_included=True, bootloader_included=False,
                             partition_table_included=False)
        self.save()

    def save(self):
        (self.root/'dist/manifest.json').write_text(json.dumps(self.manifest))

    def test_current_image(self):
        self.assertEqual(update.validate_image(self.root), self.manifest)

    def test_installed_language_must_match_entry_before_any_write(self):
        with patch.dict('os.environ',COMPANION_LANGUAGE='en'):
            with self.assertRaisesRegex(ValueError,'language'):update.validate_image(self.root)
        self.assertEqual(update.validate_image(self.root,expected_language='zh-CN'),self.manifest)

    def test_manifest_language_cannot_disguise_compiled_language(self):
        self.manifest['ui_language']='en';self.save()
        with self.assertRaisesRegex(ValueError,'语言'):update.validate_image(self.root,expected_language='en')

    def test_missing_or_ambiguous_language_marker_rejected(self):
        for image in (b'old firmware',b'COMPANION_UI_LANGUAGE=en\0COMPANION_UI_LANGUAGE=zh-CN\0'):
            with self.subTest(image=image),self.assertRaisesRegex(ValueError,'语言'):update.image_language(image)

    def test_changed_source_and_configuration_rejected(self):
        for path in ('main/main.c', 'sdkconfig', 'dependencies.lock', 'main/pet_assets.h'):
            with self.subTest(path=path):
                target = self.root/'firmware'/path
                previous = target.read_bytes() if target.exists() else None
                target.write_text('changed')
                with self.assertRaisesRegex(ValueError, '源码'):update.validate_image(self.root)
                if previous is None:target.unlink()
                else:target.write_bytes(previous)

    def test_corrupt_image(self):
        (self.root/'dist/PassportController.bin').write_bytes(b'corrupt!')
        with self.assertRaisesRegex(ValueError, '摘要'):update.validate_image(self.root)

    def test_missing_source_binding(self):
        del self.manifest['source_sha256'];self.save()
        with self.assertRaisesRegex(ValueError, '源码'):update.validate_image(self.root)

    def test_no_assets_rejected(self):
        self.manifest['apple_assets_included'] = False;self.save()
        with self.assertRaisesRegex(ValueError, '表情'):update.validate_image(self.root)

    def test_unsafe_manifest(self):
        for key, value in [('version', '0.2.12'), ('chip', 'esp32'), ('bootloader_included', True), ('partition_table_included', True)]:
            with self.subTest(key=key):
                original=self.manifest[key];self.manifest[key]=value;self.save()
                with self.assertRaises(ValueError):update.validate_image(self.root)
                self.manifest[key]=original;self.save()

    def test_cancel_does_not_stop_bridge_or_open_serial(self):
        with patch.object(update, 'validate_image', return_value=self.manifest), patch.object(update, 'flash_python', return_value='python'), patch('host_platform.usb_ports', return_value=['COM4']), patch('builtins.input', return_value='q'), patch('recover_bridge.stop_idle_bridge') as stop, patch.object(update.subprocess, 'run') as run:
            update.update()
            stop.assert_not_called();run.assert_not_called()

    def test_missing_assets_build_does_not_run_toolchain(self):
        with patch.object(update, 'ROOT', self.root), patch.object(update.subprocess, 'run') as run:
            with self.assertRaisesRegex(RuntimeError, 'pet_assets'):update.build()
            run.assert_not_called()

    def test_failed_flash_releases_endpoint(self):
        lease=Mock()
        with patch.object(update, 'validate_image', return_value=self.manifest), patch.object(update, 'flash_python', return_value='python'), patch('host_platform.usb_ports', return_value=['COM4']), patch('builtins.input', return_value='FLASH'), patch('connection_diagnostics.inspect', return_value={'status': None}), patch('recover_bridge.stop_idle_bridge'), patch('ipc_path.acquire_endpoint', return_value=lease), patch.object(update.subprocess, 'run', side_effect=RuntimeError('write failed')):
            with self.assertRaisesRegex(RuntimeError, 'write failed'):update.update()
            lease.close.assert_called_once()


class MacMaintenanceTests(unittest.TestCase):
    def test_mac_language_check_precedes_existing_safe_updater(self):
        with patch.object(update,'WINDOWS',False),patch.object(update,'validate_image',side_effect=ValueError('wrong language')),patch.object(update.subprocess,'run') as run:
            with self.assertRaisesRegex(ValueError,'wrong language'):update.update()
            run.assert_not_called()
        with patch.object(update,'WINDOWS',False),patch.object(update,'validate_image',return_value={}),patch.object(update.subprocess,'run',return_value=Mock(returncode=0)) as run:
            self.assertEqual(update.update(),0)
            self.assertEqual(run.call_args.args[0],[str(update.ROOT/'维护工具/更新Token计量与清零固件.command')])
            self.assertTrue(run.call_args.kwargs['check'])

    def test_mac_environment_guidance_does_not_install_windows_tools(self):
        with patch.object(update,'WINDOWS',False),patch.object(update.subprocess,'run') as run,patch('builtins.print') as output:
            update.setup_flash()
            run.assert_not_called()
            self.assertIn('CONTROLLER_FLASH_PYTHON',output.call_args.args[0])
