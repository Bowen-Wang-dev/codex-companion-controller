# 整理、迁移与私有数据

简体中文（默认） · [English](07-MIGRATION-AND-PRIVACY.en.md)

目标布局沿用 GitHub：
```text
codex-companion-controller/
  AGENTS.md
  README.md
  controller/         # 固件、PC 端 Bridge、主控制台
    private/          # 仅本机：配对/证书/费率/账本/备份
  mac-demo/           # 独立模拟 Demo
  docs/handoff/       # 新 Agent 交接
  tools/              # 检查及一次性迁移工具
```

## 整理原则
复制整理，不删除旧目录；保留 Git 历史、remote 和未提交交接文档。迁移源码基线来自已整理的本地 GitHubSource（`00b6133`）；旧 outputs/work 的构建缓存与压缩归档不并入源码树。

迁移工具仅将本机关键文件复制到 ignored 路径：配对配置与证书、费率/模型校准、账本、私有审计文件、Flash 备份、Apple 素材、个人构建镜像。不复制 `~/.codex/auth.json`；运行目录顶层和私有备份树也显式排除同名登录凭据文件。旧 compiler/Swift/component 缓存、巨量日志和临时测试目录不复制，原位置保留。

虚拟环境在最终目标重新创建；旧路径 shebang 和 wheel 的 .pth 不能直接搬。组件缓存和 IDF 工具链在旧工程之外，暂不删除旧工具链；迁移器会在 ignored `controller/private/local-env.sh` 记录本机 Python；旧外部 IDF 路径可手动用 PASSPORT_TOOL_ROOT 指定。构建前仍需重新配置 ESP-IDF。Windows 使用独立 venv、原生 relay 及当前用户 DACL；机器专属生成文件不进入源码归档。

## 激活新目录是另一步
1. 仅完成文件复制不会改变当前运行的 App/Bridge，也不会自动刷机。
2. 新根路径使私有 IPC hash 改变；不得并行运行新旧 Bridge，它们使用同一设备服务端口 8765。
3. 保留当前聊天，先完成工作；停旧 Bridge，用户手动退出 App 后，从新目录启动控制台。
4. 用户级 Hooks 保存旧 bridge/hook.py 的绝对路径。不要直接运行普通安装器把新命令追加成重复；先备份 ~/.codex/hooks.json，按旧命令精确移除旧 Passport handlers，再注册新路径；保留其他插件/Hook。
5. 移除/更换 hooks 可能触发重新信任，不能替用户 Trust All。新路径必须重新验证事件和实体审批。

Windows 环境准备不复制旧 Mac 账户或激活 Mac 配对；设备主机 IP、证书及防火墙可达性需针对实际主机核对。

## 隐私和版权
private/、auth、token/密码/私钥、设备唯一标识、真实 CSV、Apple 原图与含图固件不入 Git。原工程保留用于回退，不可因为“GitHub 已有”就删除 NVS 备份或图片。复制后核对 .gitignore 生效、所有关键文件 hash、venv 依赖和 source tests，再启用服务。

## 迁移执行状态（2026-11-02 更新）
Developer 目标已完成复制和激活。根下 ignored `LOCAL-MIGRATION-RECEIPT.json` 记录 340 个文件校验；`controller/private/runtime-activation.json` 记录最新账本同步和 Hooks 路径切换。新目录 Bridge/relay 及设备 Wi-Fi 在线已实测，旧服务未运行。真实设备授权验收边界见 01-PROJECT-STATE.md。

旧工程、旧工具链及新目录 private/ 内配对、备份、私有素材暂时保留，不因迁移完成自动删除。Git 不能代替私有恢复包；后续归档仍需单独备份 private/，且不可上传秘密或 Apple 原图/含图固件。

## 本地归档恢复
`tools/archive_local.py --destination <新目录> --include-hooks` 要求源码工作树无未提交修改，生成 source.tar.gz、source-history.bundle、PRIVATE-RECOVERY.tar.gz、RESTORE.txt 和摘要回执。私有包不得上传；包含 host-config/hooks.json 仅作恢复参考，不能直接覆盖其他插件配置，也不包含 ~/.codex/auth.json。

本机归档目标：`/Users/bowen/Developer/codex-companion-archives/2026-11-02-python-handoff`。这是同盘副本，异地/离线加密备份尚未执行。校验成功以 ARCHIVE-RECEIPT.json 和包内 PRIVATE-MANIFEST.json 为证；所有成员回读比对 SHA-256。运行中逐文件读取账本，不声称停机一致快照。

恢复 Python：先装独立 Python 3.11+ / OpenSSL 3；本机已选择 Homebrew python@3.12 与 python-tk@3.12。按新位置重建私有 venv，调整 private/local-env.sh 的 CONTROLLER_MODERN_PYTHON 和 CONTROLLER_BRIDGE_PYTHON，再运行 scripts/setup_bridge.sh（两项 wheel 均在 vendor 内，可离线校验加载）。Windows 使用 `scripts/setup_windows.py`。保留本机旧环境直到新进程启动验证。

最终激活补记归档为 sibling 目录 `2026-11-02-final`，包含实际 Homebrew Python 启动回执与更新交接文档。首份 `2026-11-02-python-handoff` 不覆盖；各自以 ARCHIVE-RECEIPT.json 指明对应源码提交。

2026-11-02 审查补充：私有归档在写入内容前设为 0600，拒绝覆盖已有归档和符号链接根目录；失败的部分文件不作为成功归档。迁移与归档回归仅使用合成材料，该审查没有重新迁移或归档实际私有数据，本次文档阶段也不执行。
