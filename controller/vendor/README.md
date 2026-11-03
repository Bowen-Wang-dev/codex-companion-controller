# Bridge WebSocket 依赖

简体中文（默认） · [English](README.en.md)

`websockets-17.3-py3-none-any.whl` 是 websockets 项目提供的 [PyPI 原始纯 Python 发行包](https://pypi.org/project/websockets/17.3/)，未经修改。需要 Python 3.11+；BSD-3-Clause 许可位于 wheel 内 `websockets-17.3.dist-info/licenses/LICENSE`。

SHA-256：`dc2b495a92b3971966bf102e73589f950db3ec1ca6713265355ce7771d97b199`。

`scripts/setup_bridge_deps.py` 核对摘要后，只在项目私有 Bridge 环境启用 wheel。环境准备可离线执行，不修改系统 Python；未使用原始 TCP 或自写 WebSocket 实现。

## pySerial 离线依赖

`pyserial-3.5-py2.py3-none-any.whl` 是 Chris Liechti 提供的 PyPI pySerial 3.5 原始 wheel，未经修改。SHA-256：`c4451db6ba391ca6ca299fb3ec7bae67a5c55dde170964c7a14ceefec02f2cf0`。

上游 v3.5 BSD-3-Clause 许可保留在 `pyserial-LICENSE.txt`；wheel 本身未单独包含许可文件。

`scripts/setup_bridge_deps.py` 先核对两项 wheel，再写入任何私有 `.pth`。需要私有 Python 3.11+ venv，不使用 pip 或网络，不修改系统 site-packages。`requirements-bridge.txt` 为 pip 工作流记录相同固定版本及 SHA-256。

Bridge 启动器从 `scripts/env.sh` 及 ignored `private/local-env.sh` 读取 `CONTROLLER_BRIDGE_PYTHON`，将稳定本机 Python 与 ESP-IDF 较旧的固件构建解释器分开。恢复至不同路径或 Mac 时不要复制 venv。
