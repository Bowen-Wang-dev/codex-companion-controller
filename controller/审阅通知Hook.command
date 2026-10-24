#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/scripts/env.sh"
if [[ -z "${COMPANION_CODEX:-}" ]]; then echo '没有找到 Codex CLI。'; read -r; exit 1; fi
echo '这里只打开 Codex 配置界面，不发送模型任务。'
echo '打开后输入 /hooks，审阅并信任来源 ~/.codex/hooks.json 的 Passport Hook。'
echo '信任后退出这个 CLI，再用 Command+Q 完全退出 Codex / ChatGPT 桌面应用并重新打开。'
echo '仅切换聊天或关闭窗口不保证卸载旧会话。保持 Bridge 终端运行，无需刷机或重配 Wi-Fi。'
"$COMPANION_CODEX" -C "$CONTROLLER_ROOT"
echo '如果刚完成 Hook 信任：请用 Command+Q 完全退出桌面应用，再打开原来的测试聊天。'
echo '保持 Bridge 运行，然后发起一次新请求；旧的已结束请求不会补发。'
