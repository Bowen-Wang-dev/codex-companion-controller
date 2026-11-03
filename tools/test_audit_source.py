"""Publication regressions stage synthetic fixtures in disposable Git indexes."""
import sys
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('source_audit', Path(__file__).with_name('audit-source.py'))
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class SourceAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        subprocess.run(['git', 'init', '--quiet', str(self.root)], check=True, capture_output=True)

    def stage(self, name, data):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        subprocess.run(['git', '-C', str(self.root), 'add', '--', name], check=True, capture_output=True)
        return path

    def test_staged_secret_cannot_hide_behind_clean_worktree_content(self):
        path = self.stage('notes.md', ('sk-' + 'x' * 30).encode())
        path.write_text('sanitized but not staged\n')
        with self.assertRaisesRegex(ValueError, 'possible secret; content suppressed') as error:
            audit.audit(self.root)
        self.assertNotIn('x' * 30, str(error.exception))

    def test_only_staged_bytes_are_described_as_audited(self):
        path = self.stage('notes.md', b'publication text\n')
        path.write_text('sk-' + 'x' * 30)
        self.assertEqual(audit.audit(self.root), 1)

    def test_forbidden_runtime_path_is_rejected(self):
        self.stage('controller/private/fixture.json', b'{}')
        with self.assertRaisesRegex(ValueError, 'forbidden publication path'):
            audit.audit(self.root)

    @unittest.skipIf(sys.platform == 'win32', 'POSIX symlink fixture requires Windows symlink privilege')
    def test_staged_symlink_is_rejected_after_worktree_replacement(self):
        self.stage('notes.md', b'text')
        path = self.root / 'link.md'
        path.symlink_to('notes.md')
        subprocess.run(['git', '-C', str(self.root), 'add', 'link.md'], check=True, capture_output=True)
        path.unlink()
        path.write_text('regular worktree file')
        with self.assertRaisesRegex(ValueError, 'index mode'):
            audit.audit(self.root)

    def test_vendor_digest_is_checked_against_staged_blob(self):
        name = 'controller/vendor/pyserial-3.5-py2.py3-none-any.whl'
        self.stage(name, b'synthetic bad wheel')
        with self.assertRaisesRegex(ValueError, 'vendor digest mismatch'):
            audit.audit(self.root)


if __name__ == '__main__':
    unittest.main()
