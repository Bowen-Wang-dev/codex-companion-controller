"""Small host differences shared by the console, pairing and launcher."""
import glob
import json
import os
from pathlib import Path
import subprocess
import sys

from console_i18n import tr
WINDOWS = sys.platform == 'win32'


def powershell(script):
    result = subprocess.run(['powershell.exe', '-NoLogo', '-NoProfile', '-NonInteractive',
                             '-Command', '[Console]::OutputEncoding=[Text.UTF8Encoding]::new();'
                             "$ErrorActionPreference='Stop';" + script],
                            capture_output=True, encoding='utf-8', timeout=15,
                            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    if result.returncode:
        raise RuntimeError(tr('无法检查 Windows 系统信息；未启动或停止 App/Bridge。'))
    return result.stdout.strip().lstrip('\ufeff')


def desktop_app():
    override = os.environ.get('COMPANION_DESKTOP_APP')
    if override:return Path(override).resolve(strict=True)
    if not WINDOWS:return Path('/Applications/ChatGPT.app')
    paths = json.loads(powershell("ConvertTo-Json -Compress -InputObject @(Get-AppxPackage -Name OpenAI.Codex | Select-Object -ExpandProperty InstallLocation)"))
    if len(paths) != 1:
        raise RuntimeError(tr('未找到唯一的 Windows PC 端 App；可设置 COMPANION_DESKTOP_APP 为 App 的 app 目录。'))
    return Path(paths[0]) / 'app'


def usb_ports():
    if not WINDOWS:return sorted(glob.glob('/dev/cu.usbmodem*'))
    from serial.tools.list_ports import comports
    # ESP32-C3 native USB Serial/JTAG. Never select an arbitrary COM device.
    return sorted(p.device for p in comports() if p.vid == 0x303A and p.pid == 0x1001)


def openssl_binary():
    import shutil
    override = os.environ.get('CONTROLLER_OPENSSL')
    if override:return override
    found = shutil.which('openssl')
    if found:return found
    if WINDOWS:
        for base in (os.environ.get('ProgramFiles', 'C:/Program Files'),
                     os.environ.get('LOCALAPPDATA', '') + '/Programs'):
            candidate = Path(base) / 'Git/usr/bin/openssl.exe'
            if candidate.is_file():return str(candidate)
    raise RuntimeError(tr('未找到 OpenSSL；请设置 CONTROLLER_OPENSSL 指向 openssl 可执行文件。'))


def exec_process(executable, argv):
    if WINDOWS:raise SystemExit(subprocess.call(argv))
    os.execv(executable, argv)
