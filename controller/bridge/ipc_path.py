"""Per-project private IPC: short Unix socket or authenticated Windows loopback."""
import hashlib
import os
from pathlib import Path
import stat
import errno
import socket
import json
import secrets
import sys
import tempfile

WINDOWS = sys.platform == 'win32'
if WINDOWS:
    import msvcrt
    from windows_security import secure_directory, private_file, protect_file
else:
    import fcntl

ROOT = Path(__file__).resolve().parents[1]
PROJECT_KEY = hashlib.sha256(os.fsencode(ROOT)).hexdigest()[:16]
if WINDOWS:
    SOCKET = Path(os.environ.get('LOCALAPPDATA', tempfile.gettempdir())) / 'CodexCompanion' / PROJECT_KEY / 'endpoint.json'
else:
    SOCKET = Path('/private/tmp' if sys.platform == 'darwin' else tempfile.gettempdir()) / f'pcc-{os.getuid()}-{PROJECT_KEY}' / 'bridge.sock'


def check_directory(create=False):
    if WINDOWS:
        secure_directory(SOCKET.parent, create=create)
        return SOCKET
    if create:
        SOCKET.parent.mkdir(mode=0o700, exist_ok=True)
    info = SOCKET.parent.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise PermissionError('Unsafe IPC directory: must be owned by current user, mode 0700, no symlink')
    return SOCKET


def acquire_endpoint():
    """Hold a lifetime lock; remove only an owned socket proven not to listen."""
    check_directory(create=True)
    if WINDOWS:
        lock = SOCKET.parent / 'server.lock'
        if lock.exists():private_file(lock)
        lease = lock.open('a+b')
        try:
            protect_file(lock)
            try:
                lease.seek(0)
                # Locking beyond EOF is supported by Windows; do not read a
                # byte already locked by the first Bridge before trying lock.
                msvcrt.locking(lease.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError as error:
                raise RuntimeError('另一份 Bridge 正在运行；未启动第二份服务。') from error
            if SOCKET.exists():private_file(SOCKET);SOCKET.unlink()
            return lease
        except BaseException:
            lease.close()
            raise
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


def connect(timeout=3):
    """Return a socket with the same JSONL semantics on both platforms."""
    path = check_directory()
    if WINDOWS:
        endpoint = json.loads(private_file(path).read_text(encoding='utf-8'))
        port, token = endpoint.get('port'), endpoint.get('token')
        if (type(port) is not int or not 0 < port < 65536 or not isinstance(token, str)
                or len(token) != 64 or any(c not in '0123456789abcdef' for c in token)):
            raise ValueError('Invalid private Bridge endpoint')
        client = socket.socket(socket.AF_INET)
        address = ('127.0.0.1', port)
    else:
        client = socket.socket(socket.AF_UNIX)
        address = str(path)
    try:
        client.settimeout(timeout)
        client.connect(address)
        if WINDOWS:client.sendall(token.encode('ascii') + b'\n')
        return client
    except BaseException:
        client.close()
        raise


def create_server(handler):
    import socketserver
    if WINDOWS:
        class Server(socketserver.ThreadingTCPServer):
            daemon_threads = True
            allow_reuse_address = False
            def server_bind(self):
                self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
                super().server_bind()
        token = secrets.token_hex(32)
        class Authenticated(handler):
            def handle(self):
                self.connection.settimeout(2)
                try:
                    received = self.rfile.readline(66)
                    if not secrets.compare_digest(received, token.encode('ascii') + b'\n'):return
                    self.connection.settimeout(None)
                    super().handle()
                except (OSError, ValueError):return
        server = Server(('127.0.0.1', 0), Authenticated)
        try:
            temporary = SOCKET.with_suffix('.tmp')
            if temporary.exists():private_file(temporary)
            temporary.write_text(json.dumps({'port': server.server_address[1], 'token': token}), encoding='utf-8')
            protect_file(temporary)
            os.replace(temporary, SOCKET)
        except BaseException:
            server.server_close()
            raise
        return server
    class Server(socketserver.ThreadingUnixStreamServer):
        daemon_threads = True
    server = Server(str(SOCKET), handler)
    os.chmod(SOCKET, 0o600)
    return server
