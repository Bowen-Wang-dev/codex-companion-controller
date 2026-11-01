# 启动、检查与测试

## 日常
双击 `controller/Codex Companion 控制台.command`。保持 Bridge 所在 Terminal 运行；关闭 App/Terminal 对服务生命周期有影响，不能理解为已安装后台常驻服务。

菜单：1 App 实体审批；2 Bridge/USB/Wi-Fi 恢复；3 配对；4 费率/长上下文/倍率；5 用量核对/清零；6 Hooks；7 USB 固件备份更新。

迁移准备文件 `controller/private/runtime-migration.json` 存在时，菜单 1 自动先进入旧→新目录切换：先保存工作、手动 Command+Q 退出 App，再在 Terminal 按回车。脚本停止旧服务并同步最新账本、备份并精确切换 Hooks，然后从新路径启动 App。新路径 Hook 仍需重新审阅信任。不要用菜单 6 把新命令直接追加到旧 Hooks。

App 实体审批需要通过适配入口启动真实 App，不能在普通手动打开的 App 上仅启动 Bridge 就声称已接入。已有旧 Bridge 时先停旧 Bridge；保存当前工作后用户手动 Command+Q，再由入口启动并打开原聊天。程序不要自动退出用户工作。

## 状态含义
- Wi-Fi 在线：设备与 Bridge 成功同步，不等于 App relay 已接上。
- App 已连接·等待会话：relay 在，但未见到原聊天。
- App 实体审批已接入：relay 和会话握手，之后还需真实请求测试。
- 在 Mac 确认：不是设备批准成功。已读通知也不是回复。

## 改网或断线
1. 只读看进程/私有 IPC、HTTPS 监听、设备状态。
2. 检查 Mac 当前局域网 IPv4 是否还是设备配对 URL 的地址。
3. 换 IP 时旧 URL 与证书不能靠重启自动修正；用 USB 配对，先开串口稳定 hello，再在第六页短按确认允许 60 秒。
4. 修复后先等 Wi-Fi hello/同步，再拔 USB。建议路由器 DHCP 预留地址，别仅延长离线期限掩盖问题。
5. 网络/USB权限不足则由用户普通 Terminal 执行，不无限重试或更改 TLS 验证。

## 测试命令
```sh
controller/private/bridge-venv/bin/python -m unittest discover -s controller/tests -v
bash tools/check-host.sh
zsh mac-demo/test.sh
```
运行 socket 测试需要允许本机 TCP/Unix。网络沙箱拒绝不等于断言失败；不得删掉测试来宣称全通过。Swift 缓存目录可设 COMPANION_BUILD_CACHE。

固件需要 ESP-IDF 5.5.3；先 export.sh。已有离线组件时 PASSPORT_DEPS 指向缓存；仅构建：
```sh
bash controller/scripts/build.sh
```
构建不刷机。源码仓库不含 Apple 资源；迁移的本机私有文件可补足本地构建。固件/工具链目录迁移后不能复制旧 CMake 缓存继续用，须重新配置。

## 审计
```sh
controller/private/bridge-venv/bin/python controller/scripts/audit_usage.py --provider-log /absolute/path/to/export.csv --since '2026-11-01T00:00:00+11:00' --until '2026-11-02T00:00:00+11:00'
```
示例区间仅演示参数，不自动代表用户真实对账范围。不得打印凭据或上传实际账单。

## 独立 Bridge Python（2026-11-02）
本机 `private/local-env.sh` 选择 `/opt/homebrew/opt/python@3.12/bin/python3.12` 和 `private/bridge-venv-homebrew/bin/python`。所有 shell 启动入口通过 env.sh 的 CONTROLLER_BRIDGE_PYTHON 使用相同环境，不沿用 ESP-IDF 的旧 Python。

新启动配置需要用户自行退出当前 App 后生效；可运行唯一控制台 command 加 `--restart-app`，在 Terminal 按提示确认已退出。不会自动关闭当前聊天。启动成功后 private/active-python.json 记录实际解释器；不要把 prepared 回执当成进程已激活。

离线依赖校验：`bash controller/scripts/setup_bridge.sh`。本机测试：`controller/private/bridge-venv-homebrew/bin/python -m unittest discover -s controller/tests -v`；网络 sandbox 拒绝时需获准本机 socket，不能删测试。GUI 的 Tcl/Tk 基础检查不等于所有费率菜单人工验收。
