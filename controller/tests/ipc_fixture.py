"""Isolated real host IPC for tests; never contacts a running project Bridge."""
from contextlib import contextmanager
from pathlib import Path
import sys
import tempfile
import threading
from unittest import mock

import ipc_path


@contextmanager
def ipc_server(handler):
    with tempfile.TemporaryDirectory(prefix='pcc-', dir='/tmp' if sys.platform == 'darwin' else None) as folder:
        path = Path(folder)/'ipc'/('endpoint.json' if ipc_path.WINDOWS else 'bridge.sock')
        with mock.patch.object(ipc_path, 'SOCKET', path):
            lease = ipc_path.acquire_endpoint()
            try:
                with ipc_path.create_server(handler) as server:
                    thread = threading.Thread(target=server.serve_forever, daemon=True)
                    thread.start()
                    try:yield server
                    finally:server.shutdown();thread.join(3)
            finally:
                path.unlink(missing_ok=True)
                lease.close()
