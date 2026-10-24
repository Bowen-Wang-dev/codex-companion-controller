"""Enable the pinned, licensed pure-Python wheel without pip or network access."""
import hashlib
from pathlib import Path
import sys
import sysconfig

ROOT=Path(__file__).resolve().parents[1]
WHEEL=ROOT/'vendor/websockets-17.3-py3-none-any.whl'
SHA256='dc2b495a92b3971966bf102e73589f950db3ec1ca6713265355ce7771d97b199'

if sys.version_info<(3,11):sys.exit('无线 Bridge 需要 Python 3.11 或以上')
if not WHEEL.is_file() or hashlib.sha256(WHEEL.read_bytes()).hexdigest()!=SHA256:
    sys.exit('WebSocket 依赖缺失或校验失败；未启动 Bridge，也未写入 Flash')
site=Path(sysconfig.get_path('purelib'))
# Wheel imports are supported by zipimport. Keep the bundled BSD license and
# dist-info intact; only this project's private virtual environment is changed.
pth=site/'passport_websockets.pth'
pth.write_text(str(WHEEL.resolve())+'\n')
pth.chmod(0o600)
