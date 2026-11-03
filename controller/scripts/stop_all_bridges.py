#!/usr/bin/env python3
"""Stop only this project's per-user Bridge endpoint."""
import sys
from pathlib import Path

# This script lives beside bridge/, so make the project-local module explicit
# when launched from Finder or a normal Terminal.
BRIDGE_DIR = Path(__file__).resolve().parents[1] / 'bridge'
sys.path.insert(0, str(BRIDGE_DIR))
from console_i18n import tr
from ipc_path import SOCKET, check_directory, connect, WINDOWS

try:
    path = check_directory()
except FileNotFoundError:
    print(tr('本项目没有运行中的 Bridge。'))
    raise SystemExit(0)

try:
    with connect(timeout=2) as client:
        client.sendall(b'{"type":"shutdown"}\n')
        response = client.makefile('rb').readline(1024)
    if b'"stopping": true' not in response and b'"stopping":true' not in response:
        raise RuntimeError('Bridge did not confirm shutdown')
except (ConnectionRefusedError, FileNotFoundError):
    try:
        if not WINDOWS:SOCKET.unlink(missing_ok=True)
    except OSError:
        pass
    print(tr('本项目没有可响应的 Bridge；已清理遗留 socket。'))
    raise SystemExit(0)
except Exception as error:
    print(f"{tr('停止失败：')}{error}")
    raise SystemExit(1)
print(tr('已向本项目 Bridge 发送停止请求；其他项目和 Codex 会话未受影响。'))
