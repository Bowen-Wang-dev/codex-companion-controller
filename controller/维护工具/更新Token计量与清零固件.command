#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/../scripts/env.sh"
trap 'echo "流程结束；按回车关闭窗口。"; read -r' EXIT
"$CONTROLLER_ROOT/scripts/setup_bridge.sh"
echo '0.2.11：补计上下文压缩请求、费用核对、无线 HTTP 生命周期修复。'
echo '程序目录：'"$CONTROLLER_ROOT"
echo '先运行主机测试；不会调用模型，也不会消耗重置次数。'
"$CONTROLLER_ROOT/private/bridge-venv/bin/python" -m unittest discover -s "$CONTROLLER_ROOT/tests" -v
"$CONTROLLER_ROOT/private/bridge-venv/bin/python" - "$CONTROLLER_ROOT" <<'PY'
import hashlib,json,sys
from pathlib import Path
root=Path(sys.argv[1]);manifest=json.loads((root/'dist/manifest.json').read_text())
assert manifest['version']=='0.2.11','请先构建 0.2.11 固件'
assert manifest['sha256']==hashlib.sha256((root/'dist/PassportController.bin').read_bytes()).hexdigest(),'固件校验失败'
sys.path.insert(0,str(root/'scripts'))
from launch_desktop import verify_build
verify_build()
PY
CONTROLLER_PORT="$(python -c 'import glob,sys; ports=glob.glob("/dev/cu.usbmodem*"); sys.exit("请用 USB 数据线连接一台 AI Passport") if len(ports)!=1 else print(ports[0])')"
echo '保持 App 和聊天打开。接下来只停止本项目 Bridge，然后备份并更新。'
read -r -p '按回车继续；Control+C 取消：'
"$CONTROLLER_ROOT/private/bridge-venv/bin/python" "$CONTROLLER_ROOT/scripts/stop_all_bridges.py"
for CONTROLLER_WAIT in {1..50}; do
  if python "$CONTROLLER_ROOT/scripts/preflight.py" >/dev/null 2>&1; then break; fi
  sleep 0.1
done
python "$CONTROLLER_ROOT/scripts/preflight.py"
echo '双读 8 MB 备份，仅更新 factory 应用，保留配网、费率和其他分区。'
python "$CONTROLLER_ROOT/scripts/flash.py" flash --port "$CONTROLLER_PORT" --execute
echo '固件已校验。保持从实体审批入口启动的 App 打开；本次直接接回原聊天。'
echo '不用退出 App，不用重新配网；计数和费率保留。'
exec "$CONTROLLER_ROOT/private/bridge-venv/bin/python" "$CONTROLLER_ROOT/bridge/service.py" --desktop
