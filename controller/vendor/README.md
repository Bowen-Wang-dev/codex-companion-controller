# Bridge WebSocket dependency

`websockets-17.3-py3-none-any.whl` is the unmodified pure-Python distribution from
[PyPI](https://pypi.org/project/websockets/17.3/), authored by the websockets project.
It requires Python 3.11+. The BSD-3-Clause license is included inside the wheel at
`websockets-17.3.dist-info/licenses/LICENSE`.

SHA-256: `dc2b495a92b3971966bf102e73589f950db3ec1ca6713265355ce7771d97b199`.

`scripts/setup_bridge_deps.py` verifies this digest and enables the wheel only in
the project's private Bridge environment. Setup works offline and doesn't modify
system Python. No raw TCP or custom WebSocket implementation is used.

## pySerial offline dependency

`pyserial-3.5-py2.py3-none-any.whl` is the unmodified pySerial 3.5 wheel
from PyPI, authored by Chris Liechti. SHA-256:
`c4451db6ba391ca6ca299fb3ec7bae67a5c55dde170964c7a14ceefec02f2cf0`.
The upstream v3.5 BSD-3-Clause license is preserved as `pyserial-LICENSE.txt`
(the wheel itself omits a separate license file).

`scripts/setup_bridge_deps.py` now verifies both wheels before writing either
private `.pth`. Setup requires a private Python 3.11+ venv; it uses no pip or
network and never changes system site-packages. `requirements-bridge.txt`
records the same pinned versions and SHA-256 hashes for pip-based workflows.

Bridge launchers read `CONTROLLER_BRIDGE_PYTHON` from `scripts/env.sh` and the
ignored `private/local-env.sh`. This keeps stable local Python selection separate
from ESP-IDF's older firmware build interpreter. Do not copy virtualenvs when
restoring onto a different path or Mac.
