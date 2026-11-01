"""Migration tests use only synthetic state and temporary destinations."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

spec=importlib.util.spec_from_file_location('migration',Path(__file__).with_name('migrate_local.py'))
migration=importlib.util.module_from_spec(spec);spec.loader.exec_module(migration)


class MigrationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.src=self.root/'source';self.src.mkdir()
        subprocess.run(['git','init','--quiet',str(self.src)],check=True,capture_output=True)
        (self.src/'.gitignore').write_text('**/private/\nLOCAL-MIGRATION-*.json\n')
        (self.src/'AGENTS.md').write_text('Synthetic handoff\n')
        (self.src/'controller').mkdir()
        subprocess.run(['git','-C',str(self.src),'add','.'],check=True,capture_output=True)
        subprocess.run(['git','-C',str(self.src),'-c','user.name=Migration Test','-c','user.email=migration@example.invalid','commit','--quiet','-m','fixture'],check=True,capture_output=True)
        self.runtime=self.root/'runtime';(self.runtime/'private/backups/example').mkdir(parents=True)
        (self.runtime/'private/wireless.json').write_text('{"ip":"10.20.30.40","token":"synthetic"}')
        (self.runtime/'private/backups/example/flash.bin').write_bytes(b'synthetic backup')
        (self.runtime/'private/build').mkdir();(self.runtime/'private/build/cache').write_text('skip')
        (self.runtime/'private/desktop-app.log').write_text('skip')
        (self.runtime/'firmware/main').mkdir(parents=True);(self.runtime/'firmware/main/pet_assets.h').write_text('synthetic local resource')
        (self.runtime/'dist').mkdir();(self.runtime/'dist/manifest.json').write_text('{"version":"test"}')

    def migrate(self):
        return migration.migrate(self.src,self.root/'destination',self.runtime,build_env=False)

    def test_copies_tracked_and_untracked_docs_and_history(self):
        (self.src/'NEXT.md').write_text('next agent')
        receipt=self.migrate();dest=self.root/'destination'
        self.assertEqual((dest/'AGENTS.md').read_text(),'Synthetic handoff\n')
        self.assertEqual((dest/'NEXT.md').read_text(),'next agent')
        self.assertTrue((dest/'.git').is_dir());self.assertTrue(receipt['private_copied'])
        self.assertFalse(receipt['live_services_changed']);self.assertFalse(receipt['hooks_changed'])
        self.assertTrue((dest/'LOCAL-MIGRATION-RECEIPT.json').is_file())

    def test_private_pairing_backup_asset_and_dist_survive_without_caches(self):
        self.migrate();dest=self.root/'destination'
        self.assertEqual((dest/'controller/private/wireless.json').read_bytes(),(self.runtime/'private/wireless.json').read_bytes())
        self.assertEqual((dest/'controller/private/backups/example/flash.bin').read_bytes(),b'synthetic backup')
        self.assertTrue((dest/'controller/firmware/main/pet_assets.h').is_file())
        self.assertTrue((dest/'controller/dist/manifest.json').is_file())
        self.assertFalse((dest/'controller/private/build').exists())
        self.assertFalse((dest/'controller/private/desktop-app.log').exists())
        self.assertEqual((dest/'controller/private/wireless.json').stat().st_mode & 0o777,0o600)

    def test_existing_target_is_never_overwritten(self):
        dest=self.root/'destination';dest.mkdir();(dest/'keep').write_text('preserved')
        with self.assertRaises(FileExistsError):self.migrate()
        self.assertEqual((dest/'keep').read_text(),'preserved')

    def test_refuses_destination_inside_source(self):
        with self.assertRaises(ValueError):migration.migrate(self.src,self.src/'child',build_env=False)

    def test_never_copies_ignored_credentials_from_source(self):
        (self.src/'controller/private').mkdir();(self.src/'controller/private/auth.json').write_text('synthetic do not copy')
        migration.migrate(self.src,self.root/'destination',build_env=False)
        self.assertFalse((self.root/'destination/controller/private/auth.json').exists())

    def test_rejects_symlink_in_source_without_changing_original(self):
        (self.src/'linked.md').symlink_to(self.src/'AGENTS.md')
        with self.assertRaises(ValueError):self.migrate()
        self.assertTrue((self.src/'AGENTS.md').is_file())

    def test_checksum_failure_does_not_remove_source(self):
        with mock.patch.object(migration,'digest',side_effect=['a','b']):
            with self.assertRaises(ValueError):self.migrate()
        self.assertTrue((self.src/'AGENTS.md').is_file())
        self.assertFalse((self.root/'destination').exists())


if __name__=='__main__':unittest.main()
