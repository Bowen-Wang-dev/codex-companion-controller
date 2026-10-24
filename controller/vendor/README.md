# Bridge WebSocket dependency

`websockets-17.3-py3-none-any.whl` is the unmodified pure-Python distribution from
[PyPI](https://pypi.org/project/websockets/17.3/), authored by the websockets project.
It requires Python 3.11+. The BSD-3-Clause license is included inside the wheel at
`websockets-17.3.dist-info/licenses/LICENSE`.

SHA-256: `dc2b495a92b3971966bf102e73589f950db3ec1ca6713265355ce7771d97b199`.

`scripts/setup_bridge_deps.py` verifies this digest and enables the wheel only in
the project's private Bridge environment. Setup works offline and doesn't modify
system Python. No raw TCP or custom WebSocket implementation is used.
