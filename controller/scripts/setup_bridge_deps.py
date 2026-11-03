"""Verify and enable pinned pure-Python wheels offline inside a private venv."""
import hashlib
from pathlib import Path
import sys
import sysconfig

ROOT = Path(__file__).resolve().parents[1]
WHEELS = {
    'websockets': ('websockets-17.3-py3-none-any.whl', 'dc2b495a92b3971966bf102e73589f950db3ec1ca6713265355ce7771d97b199'),
    'pyserial': ('pyserial-3.5-py2.py3-none-any.whl', 'c4451db6ba391ca6ca299fb3ec7bae67a5c55dde170964c7a14ceefec02f2cf0'),
}


sys.path.insert(0, str(ROOT/'bridge'))
from private_permissions import set_private

def enable(root=ROOT, site=None):
    site = Path(site) if site is not None else Path(sysconfig.get_path('purelib'))
    verified = {}
    # Verify everything before changing any import paths.
    for name, (filename, digest) in WHEELS.items():
        wheel = root / 'vendor' / filename
        if not wheel.is_file() or hashlib.sha256(wheel.read_bytes()).hexdigest() != digest:
            raise ValueError(name + ' dependency missing or checksum mismatch; no paths changed')
        verified[name] = wheel.resolve()
    for name, wheel in verified.items():
        pth = site / ('passport_' + name + '.pth')
        pth.write_text(str(wheel) + '\n', encoding='utf-8')
        set_private(pth, 0o600)


if __name__ == '__main__':
    if sys.version_info < (3, 11):
        sys.exit('Bridge requires Python 3.11 or newer')
    if sys.prefix == sys.base_prefix:
        sys.exit('Run dependency setup inside the private Bridge virtual environment')
    try:
        enable()
    except (OSError, ValueError) as error:
        sys.exit(str(error))
