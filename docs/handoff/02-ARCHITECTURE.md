# 架构与源码导航

```text
Codex desktop App ↔ stdio relay ↔ 官方 Codex App Server
                         ↕ 私有 Unix IPC
                     Mac Bridge
                         ↕ HTTPS / Wi-Fi（或 PC1 JSONL USB）
                  AI Passport ESP32-C3
```

App 适配使用已安装版本的内部启动开关，并非稳定公开设置；协议层用官方 App Server 请求/通知。不能修改 App 安装包、自动点击 GUI 或取消版本校验来声称支持。

## Mac 源码
- `controller/scripts/controller_console.py`：统一菜单；`Codex Companion 控制台.command` 为主入口。
- `scripts/launch_desktop.py`：精确 App 版本/摘要、环境与 relay 启动、Bridge 生命周期。
- `scripts/app_relay.command` + `bridge/stdio_relay.py`：透明 JSONL 转发、硬件/原 App 审批竞争及唯一回执。
- `bridge/service.py`：Broker 状态、请求/事件管理、设备 snapshot、账户/数值更新、私有 IPC。
- **已退役的历史模块：** ~~`bridge/native_app_ui.py`：通过 `mac_handoff` 激活原 App。~~ v0.2.13 已删除模块和 service 对应加载/调用、Hook 交接释放及 `mac_ready` 字段；旧消息无动作，历史代码在 Git `v0.2.12`。双端审批直接使用原生卡片及 stdio relay，设备无需先转交。`mac_approval_gui.py` 是已退役的无操作兼容入口，当前 service 不加载；不可恢复独立弹窗（用户明确否定）。
- `bridge/ipc_path.py`：路径相关的短 Unix socket 与锁；迁移路径会改变 IPC endpoint。
- `bridge/wireless.py`：已配对 HTTPS、证书验证、固定设备接收上限。
- `bridge/usb_transport.py`：开串口前设置 DTR/RTS；macOS termios 错误规范化。
- `scripts/pair_wifi.py`：先打开 USB，等待稳定 hello，再由物理按键允许 60 秒配对。
- `bridge/approval_review.py`、`hook_policy.py`：自然语言详情/分页、授权范围判断。
- `bridge/usage_meter.py`：数值校验、账本、去重、逐请求双档、分项估价、费率。
- `bridge/response_usage.py`：增量读本机完成记录，包括 compaction；本地格式补充，非稳定账单 API。
- `bridge/provider_billing.py`：私有 CSV/TSV 核对与唯一可归属的缺失请求补充。
- `bridge/token_rates_gui.py`：本机 GUI 费率配置；`scripts/audit_usage.py` 为只读审计。
- `scripts/flash.py`：备份、现场分区校验、factory 写入和回读验证。

## 固件与 Demo
- `controller/firmware/main/controller.c/.h`：三键状态机与请求/确认流程。
- `main.c`：显示、snapshot 解码与提示；`network.c`：Wi-Fi/HTTPS/配网。
- `sound.c`、`sound_model.c`：非阻塞音频调度；`battery.c`：电量。
- `firmware/components/bsp/`：显示、三键 ADC、音频、I2C、电量驱动。
- `mac-demo/`：独立 SwiftUI/AppKit 交互模拟，不与真实设备业务混为一谈。

## 连接与安全模型
请求绑定唯一 ID、摘要、epoch/boot、有效期及页状态。离线、撤销、过期、竞争或未收到提交回执时不能显示已授权；确认已读不等于回答，也不等于授权。HTTPS 证书/设备配对 token 与 Codex 登录完全不同，设备不存 Codex 凭据。
