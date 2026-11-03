"""Archive tests use only synthetic secrets and temporary files."""
import sys
import importlib.util
import json
from pathlib import Path
import tarfile
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('archive_local', Path(__file__).with_name('archive_local.py'))
a = importlib.util.module_from_spec(spec); spec.loader.exec_module(a)


class ArchiveTests(unittest.TestCase):
    def test_private_archive_manifest_and_permissions(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); private = root / 'controller/private'; private.mkdir(parents=True)
            ledger = private / 'token-ledger.json'; ledger.write_text('{"synthetic":42}')
            output = root / 'private.tar.gz'
            self.assertEqual(a.pack_private(output, list(a.private_files(root))), 1)
            if sys.platform == 'win32':
                from windows_security import private_file
                private_file(output)
            else:self.assertEqual(output.stat().st_mode & 0o777, 0o600)
            with tarfile.open(output) as archive:
                self.assertEqual(json.load(archive.extractfile('controller/private/token-ledger.json'))['synthetic'], 42)
                self.assertEqual(len(json.load(archive.extractfile('PRIVATE-MANIFEST.json'))['files']), 1)

    def test_excludes_credentials_logs_venvs_and_symlinks(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); private = root / 'controller/private'; private.mkdir(parents=True)
            for name in ('auth.json', 'service.log'): (private / name).write_text('excluded')
            for env_name in ('bridge-venv-homebrew','bridge-venv-windows'):
                (private / env_name).mkdir(); (private / env_name / 'cache').write_text('excluded')
            (private / 'app-relay.exe').write_text('excluded'); (private / 'app-relay.json').write_text('{}')
            (private / 'wireless.json').write_text('{"token":"synthetic"}')
            if sys.platform != 'win32':(private / 'link').symlink_to(private / 'wireless.json')
            self.assertEqual([name for _, name in a.private_files(root)], ['controller/private/wireless.json'])

    def test_invalid_live_json_refuses_archive_success(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); source = root / 'bad.json'; source.write_text('partial')
            output=root/'output.tar.gz'
            with self.assertRaises(ValueError): a.pack_private(output, [(source, 'bad.json')])
            if sys.platform == 'win32':
                from windows_security import private_file
                private_file(output)
            else:self.assertEqual(output.stat().st_mode & 0o777,0o600)

    def test_existing_archive_is_never_truncated(self):
        with tempfile.TemporaryDirectory() as folder:
            output=Path(folder)/'recovery.tar.gz';output.write_bytes(b'previous archive')
            with self.assertRaises(FileExistsError):a.pack_private(output,[])
            self.assertEqual(output.read_bytes(),b'previous archive')

    @unittest.skipIf(sys.platform == 'win32', 'POSIX symlink fixture requires Windows symlink privilege')
    def test_symlinked_recovery_root_is_rejected(self):
        for relative in ('private','dist'):
            with self.subTest(relative=relative),tempfile.TemporaryDirectory() as folder:
                root=Path(folder);(root/'controller').mkdir();target=root/'target';target.mkdir()
                (target/'fixture.json').write_text('{}')
                (root/'controller'/relative).symlink_to(target,target_is_directory=True)
                with self.assertRaisesRegex(ValueError,'symlink'):list(a.private_files(root))


if __name__ == '__main__': unittest.main()
