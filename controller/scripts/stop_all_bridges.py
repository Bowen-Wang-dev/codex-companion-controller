#!/usr/bin/env python3
"""Stop only this project's per-user Bridge endpoint."""
import socket
import sys
from pathlib import Path

# This script lives beside bridge/, so make the project-local module explicit
# when launched from Finder or a normal Terminal.
BRIDGE_DIR = Path(__file__).resolve().parents[1] / 'bridge'
sys.path.insert(0, str(BRIDGE_DIR))
from ipc_path import SOCKET, check_directory

try:
    path = check_directory()
except FileNotFoundError:
    print('本项目没有运行中的 Bridge。')
    raise SystemExit(0)

try:
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
        client.settimeout(2)
        client.connect(str(path))
        client.sendall(b'{"type":"shutdown"}\n')
        response = client.makefile('rb').readline(1024)
    if b'"stopping": true' not in response and b'"stopping":true' not in response:
        raise RuntimeError('Bridge did not confirm shutdown')
except (ConnectionRefusedError, FileNotFoundError):
    try:
        SOCKET.unlink(missing_ok=True)
    except OSError:
        pass
    print('本项目没有可响应的 Bridge；已清理遗留 socket。')
    raise SystemExit(0)
except Exception as error:
    print(f'停止失败：{error}')
    raise SystemExit(1)
print('已向本项目 Bridge 发送停止请求；其他项目和 Codex 会话未受影响。')
