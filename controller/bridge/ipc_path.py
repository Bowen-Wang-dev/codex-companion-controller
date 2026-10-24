"""Short, per-user/project Unix endpoint (macOS sun_path is only 104 bytes)."""
import hashlib
import os
from pathlib import Path
import stat
import errno
import fcntl
import socket

ROOT = Path(__file__).resolve().parents[1]
PROJECT_KEY = hashlib.sha256(os.fsencode(ROOT)).hexdigest()[:16]
SOCKET = Path('/private/tmp') / f'pcc-{os.getuid()}-{PROJECT_KEY}' / 'bridge.sock'


def check_directory(create=False):
    if create:
        SOCKET.parent.mkdir(mode=0o700, exist_ok=True)
    info = SOCKET.parent.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise PermissionError('Unsafe IPC directory: must be owned by current user, mode 0700, no symlink')
    return SOCKET


def acquire_endpoint():
    """Hold a lifetime lock; remove only an owned socket proven not to listen."""
    check_directory(create=True)
    fd = os.open(SOCKET.parent/'server.lock', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    lease = os.fdopen(fd, 'a')
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError('另一份 Bridge 正在运行。请先在旧终端按 Control+C 停止，再启动。')
        try:
            info = SOCKET.lstat()
        except FileNotFoundError:
            return lease
        if not stat.S_ISSOCK(info.st_mode) or info.st_uid != os.getuid():
            raise PermissionError('Unexpected IPC path type/owner; refusing removal')
        with socket.socket(socket.AF_UNIX) as probe:
            probe.settimeout(.5)
            try:
                probe.connect(str(SOCKET))
            except OSError as error:
                if error.errno not in (errno.ECONNREFUSED, errno.ENOENT):
                    raise
            else:
                raise RuntimeError('已有旧版 Bridge 在监听。请先在旧终端按 Control+C 停止。')
        SOCKET.unlink(missing_ok=True)
        print('已清理上次退出遗留的 IPC socket。', flush=True)
        return lease
    except BaseException:
        lease.close()
        raise
