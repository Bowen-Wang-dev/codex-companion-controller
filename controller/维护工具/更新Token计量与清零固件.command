#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/../scripts/env.sh"
trap 'companion_message "流程结束；按回车关闭窗口。" "Finished; press Enter to close this window."; read -r' EXIT
"$CONTROLLER_ROOT/scripts/setup_bridge.sh"
if [[ ! -x "${CONTROLLER_FLASH_PYTHON:-}" ]]; then
 companion_message '尚未配置刷写解释器；请在 private/local-env.sh 设置 CONTROLLER_FLASH_PYTHON（需要 esptool 4.x）。未停止 Bridge，未写设备。' 'Flash interpreter not configured. Set CONTROLLER_FLASH_PYTHON in private/local-env.sh (esptool 4.x required). Bridge was not stopped; the device was not written.'
 exit 1
fi
"$CONTROLLER_FLASH_PYTHON" -c 'import esptool; assert esptool.__version__.split(".")[0]=="4", "esptool 4.x required"; print("Flash runtime: esptool",esptool.__version__)'
companion_message '0.2.13：原 App 与设备双端直接审批，移除长按转到 PC 端。' '0.2.13: direct approvals in the original App and device; hold-to-handoff removed.'
companion_prompt '程序目录：' 'Project directory: '; printf '%s\n' "$CONTROLLER_ROOT"
companion_message '先运行主机测试；不会调用模型，也不会消耗重置次数。' 'Running host tests first; no model calls or reset credits are consumed.'
"$CONTROLLER_BRIDGE_PYTHON" -m unittest discover -s "$CONTROLLER_ROOT/tests" -v
"$CONTROLLER_BRIDGE_PYTHON" - "$CONTROLLER_ROOT" <<'PY'
import hashlib,json,sys
from pathlib import Path
root=Path(sys.argv[1]);manifest=json.loads((root/'dist/manifest.json').read_text())
sys.path.insert(0,str(root/'bridge'))
from console_i18n import tr
assert manifest['version']=='0.2.13',tr('请先构建 0.2.13 固件')
assert manifest['sha256']==hashlib.sha256((root/'dist/PassportController.bin').read_bytes()).hexdigest(),tr('固件校验失败')
sys.path.insert(0,str(root/'scripts'))
from launch_desktop import verify_build
verify_build()
PY
CONTROLLER_PORT="$("$CONTROLLER_BRIDGE_PYTHON" -c 'import glob,sys,os; ports=glob.glob("/dev/cu.usbmodem*"); sys.exit("Connect one AI Passport with a USB data cable" if os.environ.get("COMPANION_LANGUAGE")=="en" else "请用 USB 数据线连接一台 AI Passport") if len(ports)!=1 else print(ports[0])')"
companion_message '保持 App 和聊天打开。接下来只停止本项目 Bridge，然后备份并更新。' 'Keep the App and chat open. Only this project Bridge will stop before backup and update.'
companion_prompt '按回车继续；Control+C 取消：' 'Press Enter to continue; Control+C cancels: '; read -r
"$CONTROLLER_BRIDGE_PYTHON" "$CONTROLLER_ROOT/scripts/stop_all_bridges.py"
for CONTROLLER_WAIT in {1..50}; do
  if "$CONTROLLER_BRIDGE_PYTHON" "$CONTROLLER_ROOT/scripts/preflight.py" >/dev/null 2>&1; then break; fi
  sleep 0.1
done
"$CONTROLLER_BRIDGE_PYTHON" "$CONTROLLER_ROOT/scripts/preflight.py"
companion_message '双读 8 MB 备份，仅更新 factory 应用，保留配网、费率和其他分区。' 'Reading two full 8 MB backups; only the factory application is updated, retaining pairing, rates and other partitions.'
"$CONTROLLER_FLASH_PYTHON" "$CONTROLLER_ROOT/scripts/flash.py" flash --port "$CONTROLLER_PORT" --execute
companion_message '固件已校验。保持从实体审批入口启动的 App 打开；本次直接接回原聊天。' 'Firmware verified. Keep the App started through the approval launcher open; reconnecting to the original chat.'
companion_message '不用退出 App，不用重新配网；计数和费率保留。' 'No App exit or Wi-Fi reconfiguration needed; counters and rates are retained.'
exec "$CONTROLLER_BRIDGE_PYTHON" "$CONTROLLER_ROOT/bridge/service.py" --desktop
