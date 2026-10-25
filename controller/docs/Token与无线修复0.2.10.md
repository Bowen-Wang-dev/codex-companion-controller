# 0.2.10 · Token 与无线修复 / Accounting and transport fixes

2026-10-26 · Australia/Sydney

## 中文

### Token 与费用

旧计量只读取普通 App Server 用量事件，可能漏掉上下文压缩调用。新增增量读取本机 `token_usage_record`，按线程、轮次和响应 ID 去重。普通累计和响应记录保留各自的重放基线，按轮次核对，不能直接相加。重启保留状态，清零保留原始基线；分别处理半行追加、重复或倒序事件、缺失模型和模型切换。

后台可能存在本机没有收到完成记录的已计费请求。可选的私有 CSV/TSV 导出用于对账：模型、数值和时间匹配后，只有唯一落入已知轮次的缺失请求才会补入。有歧义则不猜；迟到的本机记录会消除对应补充，防止重复。未提供的未来后台明细仍不可见；这不是账户全局账单，也没有虚构的第三方账单 API。

设备“输入含缓存”“输出含推理”均为包含关系，不能再加一次。后台导出的 Input Tokens 按非缓存输入解释；Billed Cost 已含后台倍率，不重复打折。费用只按本机明确配置的模型费率估算，不自动改费率。金额使用 `$`；本机计数清零要求短按打开二次确认、松开后重新长按一秒，既不清服务商账单，也不清聊天历史。

新增「核对Token用量.command」默认只读核对最近一小时，可用 `--provider-log` 提供导出路径，并用 `--since` / `--until` 指定含时区时间。「检查Token计量.command」用于诊断；「清零Token计数.command」用于明确确认后清零。后台导出、对账结果及账户信息只保存在本机 `private/`。公开测试使用合成数值。

### 无线传输

观察到的短暂离线中，诊断显示 Wi-Fi 未断开，但 HTTP 响应头阶段失败。固件改用 ESP-IDF 完整 HTTP 生命周期及有边界的接收回调，保留证书验证、持久连接、有限重试和 Wi-Fi 代际检查。Bridge 在实际 TLS socket 设置 TCP_NODELAY、刷新输出、增大接收队列，并补充错误码、状态码及耗时诊断。没有延长五秒离线判定。低延迟模式关闭 Wi-Fi modem sleep，会增加耗电。

### 构建、验证与更新

开发环境通过 197 项 Python 检查、控制器／音序／八组音频检查、ESP-IDF 5.5.3 构建、esptool 镜像校验及实际字库预览。中文长审批快照通过设备接收边界检查。构建和主机测试不能代替实机耐久验收。

截至此记录，Bridge 0.2.10 已接回原 App，设备最后确认版本为 0.2.9；新固件 0.2.10 是已构建候选版，仍待用户更新及实机稳定性验收。

更新运行「更新Token计量与清零固件.command」：双读完整 8 MB 备份、仅更新 factory、回读校验，保留身份、配网、计数和费率。保持原 App 和聊天打开，脚本只停止本项目 Bridge，完成后接回现有 App。日常入口为「启动桌面App实体审批.command」。源码不附 Apple 图片或含图固件；首次构建请参阅上级 README。

## English

### Tokens and costs

Ordinary App Server usage events can omit compaction calls. Incremental local `token_usage_record` reading supplements them with thread/turn reconciliation and response-ID deduplication. Separate source baselines prevent blindly adding overlapping histories. State survives restarts; counter resets preserve replay boundaries. Partial appends, reordered events, missing models and model switches are handled explicitly.

Optional private provider CSV/TSV exports can identify billed requests absent from local completion records. Supplementation requires matching numeric/model data and an unambiguous known turn; late local records remove the supplement. Future provider-only charges remain unknown without another export or a verified billing API. This is not account-wide billing telemetry.

Input includes cache; output includes reasoning. Exported Input Tokens represent uncached input, and Billed Cost already includes the provider multiplier. Local estimates use explicitly configured model rates, without changing them automatically. USD uses `$`. Resetting local counters requires a separate confirmation and a fresh one-second hold; it changes neither provider billing nor chat history.

The read-only audit launcher defaults to the past hour. Use `--provider-log`, `--since` and `--until` for an export and timezone-aware interval. Billing exports, reconciliation output and account data stay in local `private/`; public fixtures use synthetic values.

### Wireless transport

Observed HTTP-header failures occurred without Wi-Fi disconnects. Firmware now uses the complete IDF HTTP lifecycle, bounded callbacks, verified TLS, persistent connections, bounded retries and Wi-Fi-generation checks. The Bridge configures the live TLS socket, flushes responses, increases its accept backlog and exposes error/status/latency diagnostics. The existing five-second offline threshold is unchanged. Disabling modem sleep improves latency at a battery cost.

### Validation and updating

Development validation passed 197 Python checks, controller/tone and eight audio cases, ESP-IDF 5.5.3 build, esptool image validation, actual-font previews and the Chinese approval receive-size check. These do not establish hardware endurance.

Bridge 0.2.10 reattached to the existing App. The last confirmed device firmware is 0.2.9; built firmware 0.2.10 remains a candidate pending physical update and endurance acceptance.

The accounting firmware updater makes two matching full backups, writes/verifies only the factory application and retains pairing, identity, counters and rates. Keep the original App/chat open; the updater stops only this project's Bridge and reconnects it afterward. Use the desktop-approval launcher for daily startup. Source distribution excludes Apple artwork and artwork-containing firmware; see the parent README before building.
