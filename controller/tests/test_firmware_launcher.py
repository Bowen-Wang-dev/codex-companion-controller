"""Exercise the real updater shell with isolated, non-device interpreters."""
import os
from pathlib import Path
import shlex
import subprocess
import tempfile
import unittest
import sys

ROOT=Path(__file__).resolve().parents[1]


@unittest.skipIf(sys.platform == 'win32', 'macOS shell updater; Windows updater remains unavailable')
class FirmwareLauncherTests(unittest.TestCase):
    def run_launcher(self,configured=True,dependency_ok=True):
        with tempfile.TemporaryDirectory(prefix='passport update ') as folder:
            root=Path(folder);(root/'scripts').mkdir();(root/'维护工具').mkdir()
            log=root/'calls.log';bridge=root/'bridge-python';flash=root/'flash-python'
            bridge.write_text('''#!/bin/bash
printf 'bridge:%s\\n' "$*" >> "$CALL_LOG"
if [[ "$1" == '-' ]]; then cat >/dev/null; fi
if [[ "$1" == '-c' ]]; then echo /dev/fixture-only; fi
''')
            flash.write_text('''#!/bin/bash
printf 'flash:%s\\n' "$*" >> "$CALL_LOG"
if [[ "$1" == '-c' && "$DEPENDENCY_OK" != 1 ]]; then exit 1; fi
''')
            bridge.chmod(0o700);flash.chmod(0o700)
            (root/'scripts/env.sh').write_text(
                'export CONTROLLER_ROOT='+shlex.quote(str(root))+'\n'+
                'export CONTROLLER_BRIDGE_PYTHON='+shlex.quote(str(bridge))+'\n'+
                'export CONTROLLER_FLASH_PYTHON='+shlex.quote(str(flash) if configured else '')+'\n')
            setup=root/'scripts/setup_bridge.sh';setup.write_text('#!/bin/bash\nexit 0\n');setup.chmod(0o700)
            updater=root/'维护工具/update.command'
            updater.write_text((ROOT/'维护工具/更新Token计量与清零固件.command').read_text())
            env=dict(os.environ,PATH='/usr/bin:/bin:/usr/sbin:/sbin',CALL_LOG=str(log),
                     DEPENDENCY_OK='1' if dependency_ok else '0')
            result=subprocess.run(['/bin/bash',str(updater)],input='\n\n',env=env,
                                  capture_output=True,text=True,timeout=10)
            return result,log.read_text() if log.exists() else ''

    def test_update_routes_without_a_python_command_on_path(self):
        result,calls=self.run_launcher()
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn('bridge:-c import glob,sys',calls)
        self.assertIn('/scripts/preflight.py',calls)
        self.assertIn('flash:',calls)
        self.assertIn('/scripts/flash.py flash --port /dev/fixture-only --execute',calls)
        self.assertLess(calls.index('flash:-c import esptool'),calls.index('/scripts/stop_all_bridges.py'))
        self.assertIn('bridge:',calls.splitlines()[-1])
        self.assertIn('/bridge/service.py --desktop',calls.splitlines()[-1])

    def test_missing_flash_interpreter_fails_before_stopping_or_writing(self):
        result,calls=self.run_launcher(configured=False)
        self.assertNotEqual(result.returncode,0)
        self.assertIn('未停止 Bridge，未写设备',result.stdout)
        self.assertNotIn('stop_all_bridges.py',calls)
        self.assertNotIn('flash.py',calls)

    def test_missing_esptool_fails_before_stopping_or_writing(self):
        result,calls=self.run_launcher(dependency_ok=False)
        self.assertNotEqual(result.returncode,0)
        self.assertNotIn('stop_all_bridges.py',calls)
        self.assertNotIn('flash.py',calls)


if __name__=='__main__':unittest.main()
