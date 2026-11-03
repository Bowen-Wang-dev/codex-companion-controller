import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('flash_read_test_module', Path(__file__).resolve().parents[1]/'scripts/flash.py')
flash = importlib.util.module_from_spec(spec)
spec.loader.exec_module(flash)


class ReadRecoveryTests(unittest.TestCase):
    def test_failed_partial_block_is_discarded_not_spliced(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(flash.sys, 'platform', 'win32'):
            tool = flash.Tool('COM4');calls=[]
            def run(*args):
                calls.append(args)
                self.assertEqual(tool.base[tool.base.index('--after')+1], 'no_reset')
                target=Path(args[3]);length=int(args[2],16)
                if len(calls)==1:
                    target.write_bytes(b'bad');raise RuntimeError('Corrupt data')
                self.assertFalse(target.exists())
                target.write_bytes(bytes([int(args[1],16)//262144])*length)
            tool.run=run
            target=Path(folder)/'flash.bin'
            tool.read_range(0,262144+17,target)
            self.assertEqual(target.read_bytes(),bytes(262144)+bytes([1])*17)
            self.assertEqual(len(calls),3)
            self.assertEqual(calls[0][1],calls[1][1])
            self.assertTrue(all(c[0]=='read_flash' and c[-1]=='--no-progress' for c in calls))

    def test_rom_fallback_is_bounded_and_failure_stops(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(flash.sys, 'platform', 'win32'):
            tool=flash.Tool('COM4');commands=[]
            def fail(*args):
                commands.append(tool.base.copy());raise RuntimeError('Corrupt data')
            tool.run=fail
            with self.assertRaisesRegex(RuntimeError,'未写入设备'):
                tool.read_range(0,262144,Path(folder)/'flash.bin')
            self.assertEqual(len(commands),3)
            self.assertNotIn('--no-stub',commands[0]);self.assertIn('--no-stub',commands[-1])

    def test_short_successful_read_also_retries(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(flash.sys, 'platform', 'win32'):
            tool=flash.Tool('COM4');calls=[]
            def run(*args):
                calls.append(args);Path(args[3]).write_bytes(b'x'*(1 if len(calls)==1 else 16))
            tool.run=run;target=Path(folder)/'flash.bin'
            tool.read_range(0,16,target)
            self.assertEqual(target.read_bytes(),b'x'*16);self.assertEqual(len(calls),2)

    def test_existing_backup_is_never_truncated(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(flash.sys, 'platform', 'win32'):
            target=Path(folder)/'flash.bin';target.write_bytes(b'previous')
            with self.assertRaises(FileExistsError):flash.Tool('COM4').read_range(0,16,target)
            self.assertEqual(target.read_bytes(),b'previous')

    def test_backup_failure_never_creates_manifest(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(flash,'ROOT',Path(folder)), patch.object(flash,'set_private'):
            tool=flash.Tool('COM4');tool.identity=lambda:'00:11:22:33:44:55'
            def fail(*args):raise RuntimeError('read failed')
            tool.read_range=fail
            with self.assertRaisesRegex(RuntimeError,'read failed'):flash.backup(tool)
            self.assertFalse(list(Path(folder).rglob('manifest.json')))

    def test_posix_read_keeps_original_single_transfer(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(flash.sys,'platform','darwin'):
            tool=flash.Tool('/dev/test');calls=[]
            def run(*args):calls.append(args);Path(args[3]).write_bytes(b'x'*16)
            tool.run=run;tool.read_range(0,16,Path(folder)/'flash.bin')
            self.assertEqual(len(calls),1)
