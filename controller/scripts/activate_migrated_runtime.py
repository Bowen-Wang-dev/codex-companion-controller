#!/usr/bin/env python3
"""Activate a copied runtime after the user has closed the desktop App."""
import copy
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import socket
import stat
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
PENDING = ROOT / 'private/runtime-migration.json'


def endpoint_at(root):
    key = hashlib.sha256(os.fsencode(root.resolve())).hexdigest()[:16]
    return Path('/private/tmp') / f'pcc-{os.getuid()}-{key}' / 'bridge.sock'


def request_at(root, message):
    endpoint = endpoint_at(root)
    try:
        info = endpoint.parent.lstat()
        if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
            raise PermissionError('Unsafe migration IPC directory')
        with socket.socket(socket.AF_UNIX) as client:
            client.settimeout(3)
            client.connect(str(endpoint))
            client.sendall(json.dumps(message).encode() + b'\n')
            with client.makefile('rb') as stream:
                line = stream.readline(65537)
        if len(line) > 65536:
            raise ValueError('Bridge response too large')
        result = json.loads(line)
        if not isinstance(result, dict):
            raise ValueError('Invalid Bridge response')
        return result
    except (FileNotFoundError, ConnectionRefusedError):
        return None


def wait_stopped(root):
    try:
        fd = os.open(endpoint_at(root).parent / 'server.lock', os.O_RDWR | os.O_NOFOLLOW)
    except FileNotFoundError:
        return
    with os.fdopen(fd, 'a') as lease:
        for _ in range(100):
            try:
                fcntl.flock(lease.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                return
            except BlockingIOError:
                time.sleep(.1)
    raise RuntimeError('旧 Bridge 尚未退出；未复制账本。')


def migrate_hooks(data, old_root, new_root):
    """Replace only exact old Passport commands, preserving all other metadata."""
    result = copy.deepcopy(data)
    old = '/usr/bin/python3 ' + shlex.quote(str(old_root / 'bridge/hook.py'))
    new = '/usr/bin/python3 ' + shlex.quote(str(new_root / 'bridge/hook.py'))
    for groups in result.get('hooks', {}).values():
        already = any(h.get('command') == new for g in groups for h in g.get('hooks', []))
        kept = []
        for group in groups:
            handlers = []
            for handler in group.get('hooks', []):
                if handler.get('command') == old:
                    if already:
                        continue
                    handler['command'] = new
                    already = True
                handlers.append(handler)
            if handlers or not group.get('hooks'):
                group['hooks'] = handlers
                kept.append(group)
        groups[:] = kept
    return result


def copy_ledger(old_root, new_root, backup):
    source = old_root / 'private/token-ledger.json'
    target = new_root / 'private/token-ledger.json'
    if source.is_symlink() or target.is_symlink():
        raise ValueError('Refusing symlink ledger')
    data = source.read_bytes()
    if not isinstance(json.loads(data), dict):
        raise ValueError('Invalid source ledger')
    if target.exists() and target.read_bytes() == data:
        return
    if target.exists():
        shutil.copy2(target, backup / 'token-ledger.before.json')
    temporary = target.with_suffix('.migration-tmp')
    with temporary.open('xb') as stream:
        os.chmod(temporary, 0o600)
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    if temporary.read_bytes() != source.read_bytes():
        temporary.unlink()
        raise RuntimeError('Source ledger changed during migration; retry after stopping old Bridge')
    os.replace(temporary, target)


def activate(old_root, new_root=ROOT):
    from launch_desktop import verify_build
    from install_hooks import save
    version = verify_build()
    old_root = old_root.resolve()
    new_root = new_root.resolve()
    if old_root == new_root or not (old_root / 'bridge/service.py').is_file():
        raise ValueError('Invalid old runtime directory')
    running = subprocess.run(['/usr/bin/pgrep', '-f', '^/Applications/ChatGPT.app/Contents/MacOS/ChatGPT'], capture_output=True)
    if running.returncode != 1:
        raise RuntimeError('App 仍在运行或无法检查。请先手动 Command+Q；未停止 Bridge。')
    if request_at(new_root, {'type': 'status'}) is not None:
        raise RuntimeError('新目录 Bridge 已运行；拒绝覆盖运行中的账本。')
    for name in ('wireless.json', 'bridge-cert.pem', 'bridge-key.pem', 'token_rates.json'):
        if (old_root / 'private' / name).read_bytes() != (new_root / 'private' / name).read_bytes():
            raise RuntimeError('迁移后配对或费率发生变化，请先核对：' + name)
    hooks = Path(os.environ.get('CODEX_HOME', str(Path.home() / '.codex'))) / 'hooks.json'
    before = json.loads(hooks.read_text()) if hooks.exists() else {}
    # Validate the full transform before stopping the old service.
    migrate_hooks(before, old_root, new_root)
    status = request_at(old_root, {'type': 'status'})
    if status:
        if status.get('project_root') != str(old_root):
            raise RuntimeError('旧 Bridge 路径不匹配；未停止服务。')
        if status.get('permission_pending') or status.get('hook_pending'):
            raise RuntimeError('旧 Bridge 有待处理审批；未停止服务。')
        if request_at(old_root, {'type': 'shutdown'}) != {'stopping': True}:
            raise RuntimeError('旧 Bridge 未确认停止。')
    # The lifetime lock is released only after HTTPS and usage workers stop.
    wait_stopped(old_root)
    backup = new_root / 'private' / ('activation-backup-' + str(time.time_ns()))
    backup.mkdir(mode=0o700)
    copy_ledger(old_root, new_root, backup)
    save(hooks, lambda data: migrate_hooks(data, old_root, new_root), backup)
    receipt = {'activated_at': time.strftime('%Y-%m-%dT%H:%M:%S%z'), 'old_root': str(old_root),
               'new_root': str(new_root), 'verified_app': version,
               'ledger_synced': True, 'hooks_migrated': True,
               'app_device_approval_verified': False}
    path = new_root / 'private/runtime-activation.json'
    path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
    path.chmod(0o600)
    print('旧 Bridge 已停止；最新账本与 Hooks 已切换到新目录，备份已保留。', flush=True)


def main():
    config = json.loads(PENDING.read_text())
    print('切换到新工程：' + str(ROOT), flush=True)
    print('请保存当前工作，手动 Command+Q 退出桌面 App，再回到这个 Terminal。', flush=True)
    if input('App 已退出后按回车继续；输入 q 取消：').strip().lower() == 'q':
        return
    activate(Path(config['old_root']))
    PENDING.unlink()
    print('新路径 Hooks 需要在 Codex 中重新审阅信任；请打开原聊天验证设备审批。', flush=True)
    os.execv(sys.executable, [sys.executable, str(ROOT / 'scripts/launch_desktop.py')])


if __name__ == '__main__':
    os.umask(0o077)
    try:
        main()
    except (OSError, ValueError, RuntimeError) as error:
        sys.exit('运行目录切换未完成：' + str(error))
    except (EOFError, KeyboardInterrupt):
        sys.exit('已取消；没有自动关闭 App。')
