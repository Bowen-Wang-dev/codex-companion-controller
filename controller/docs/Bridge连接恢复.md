# Bridge 连接恢复 / Connection recovery

## 中文

- Bridge 进程停止、Mac DHCP 地址变化、桌面 App 升级是不同问题。检查入口显示各项状态，不把 USB 插入等同于 Bridge 已运行。
- 新增 `恢复Bridge连接.command`，保持 App 和聊天打开，在正常 Terminal 运行。选 1 恢复 USB，选 2 安全重配 Wi-Fi；不刷机、不清计数，不删除账户或配对文件。存在待处理审批时拒绝自动停止 Bridge。
- Mac 地址改变时，旧设备 URL 和证书不会随重启自动更新。重配无线需要当前 2.4 GHz 网络名称、密码及设备短按确认，密码只在本机隐藏输入。建议在路由器为 Mac 预留 DHCP 地址。
- 恢复脚本只连接已识别的单台 USB 设备。串口打开前设置 DTR/RTS 为 false；驱动仍可能触发复位。断开 USB 不再把正常 Wi-Fi 链路错误标记为离线。
- 桌面 App 适配增加对本机核对的 26.1027.30824 的明确文件摘要；保留 26.1016.62342。新版本分块 JS 布局不再导致原始 KeyError；未知版本或摘要变化仍拒绝启用适配。
- 当前 App 若不是由实体审批入口启动，恢复设备链路不会把它变成已接入审批。需要完成当前工作后手动退出，再通过 `启动桌面App实体审批.command` 打开并恢复原聊天。程序不会自动退出 App。

## English

Process availability, changed DHCP addresses and App compatibility are separate checks. The recovery launcher keeps the current App/chat open and offers USB recovery or consent-based Wi-Fi pairing without flashing, resetting counters or deleting credentials. Pending approvals prevent automatic Bridge shutdown.

A changed Mac IP requires updating the device URL and certificate through USB pairing; restarting alone is insufficient. Passwords are entered locally with hidden input. A router DHCP reservation can reduce future address changes.

USB opens with DTR/RTS disabled before opening, although drivers may still reset the device. USB loss no longer invalidates a healthy Wi-Fi transport. The adapter explicitly verifies inspected entry/chunk hashes for App 26.1027.30824 and the earlier 26.1016.62342; unknown builds remain blocked. Restoring transport does not attach a normally launched App to the approval relay. After finishing current work, manually restart through the physical-approval launcher when needed.

## 新版 App 接入 / Updated App attachment

`接入新版App实体审批.command` 会先核对版本，等待用户完成工作后手动退出 App，再停止空闲 Bridge 并通过适配入口启动原 App。若 App 尚未退出或存在待处理审批，它不会强制停止。无需 USB、刷机或重新配网。打开原聊天，设备连接页应显示“App 实体审批已接入”；仅显示 Wi-Fi 在线不等于审批接入成功。

The updated-App attachment launcher checks the inspected version, waits for a manual App quit, stops only an idle project Bridge and launches through the relay. It refuses to stop while the App is still running or an approval is pending. No USB, flash or re-pairing is required. Reopen the original chat and verify the device reports App approval attachment; Wi-Fi connectivity alone does not establish it.
