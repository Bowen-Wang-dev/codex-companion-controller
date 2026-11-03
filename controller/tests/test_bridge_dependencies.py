"""Dependency integrity and launcher routing checks use temporary site paths."""
import hashlib
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
import sys
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('bridge_deps', ROOT / 'scripts/setup_bridge_deps.py')
deps = importlib.util.module_from_spec(spec); spec.loader.exec_module(deps)


class DependencyTests(unittest.TestCase):
    def test_all_wheels_verified_and_import_paths_local(self):
        with tempfile.TemporaryDirectory() as folder:
            site = Path(folder)
            deps.enable(ROOT, site)
            for name, (filename, digest) in deps.WHEELS.items():
                wheel = ROOT / 'vendor' / filename
                self.assertEqual(hashlib.sha256(wheel.read_bytes()).hexdigest(), digest)
                pth = site / ('passport_' + name + '.pth')
                self.assertEqual(pth.read_text(), str(wheel.resolve()) + '\n')
                if sys.platform == 'win32':
                    from windows_security import private_file
                    private_file(pth)
                else:self.assertEqual(pth.stat().st_mode & 0o777, 0o600)

    def test_corrupt_wheel_changes_no_import_paths(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); (root / 'vendor').mkdir(); (root / 'site').mkdir()
            (root / 'vendor/bad.whl').write_bytes(b'corrupt')
            with mock.patch.object(deps, 'WHEELS', {'bad': ('bad.whl', '0' * 64)}):
                with self.assertRaisesRegex(ValueError, 'checksum'): deps.enable(root, root / 'site')
            self.assertEqual(list((root / 'site').iterdir()), [])

    def test_missing_wheel_preserves_existing_import_path(self):
        with tempfile.TemporaryDirectory() as folder:
            site = Path(folder); existing = site / 'passport_pyserial.pth'
            existing.write_text('original\n')
            with self.assertRaises(ValueError): deps.enable(site, site)
            self.assertEqual(existing.read_text(), 'original\n')

    @unittest.skipIf(sys.platform == 'win32', 'macOS shell launchers')
    def test_shell_launchers_use_configured_interpreter_and_parse(self):
        paths = list((ROOT / 'scripts').glob('*.sh')) + list((ROOT / 'scripts').glob('*.command'))
        paths += list((ROOT / '维护工具').glob('*.command')) + [ROOT / 'Codex Companion 控制台.command']
        for path in paths:
            subprocess.run(['/bin/bash', '-n', str(path)], check=True, capture_output=True)
            if '$CONTROLLER_BRIDGE_PYTHON' in path.read_text():
                self.assertIn('env.sh', path.read_text())
        relay = (ROOT / 'scripts/app_relay.command').read_text()
        self.assertIn('exec "$CONTROLLER_BRIDGE_PYTHON"', relay)
        self.assertNotIn('/private/bridge-venv/bin/python', relay)


if __name__ == '__main__': unittest.main()
