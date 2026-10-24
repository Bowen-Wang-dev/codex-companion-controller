# Validation status / 验证状态

2026-10-24 · Australia/Sydney

## 中文

- 固件基线 0.2.3，Bridge 修订 0.2.3-hookfix1，Mac Demo 0.4.0。
- 设备已实际运行 0.2.3，并通过 Wi-Fi 同步账户额度、电量和运行状态。账户同步成功不等于审批通道全部可用。
- 用户已实际验证 App 内置权限申请的设备提醒与设备拒绝。另一次“允许”只继续到 Mac 原生授权，不算设备直接授予成功。测试没有修改被申请目录的文件。
- 最近一次原开发目录验证：88 项 Python 测试通过；控制器、音序和 8 组模拟 RTOS/BSP 的实际音频工作线程检查通过。Mac Demo 基线为 30 项状态机／导航检查。
- 原开发环境已构建 ESP-IDF 5.5.3 的 0.2.3 固件。这个可分享源码快照清理了本机路径及素材，不能因此声称已在任意干净环境完整重建或通过实机验收。
- 无线 TLS 轮询和 Unix WebSocket 审批使用真实主机传输测试；模拟批准、额度重置与音频测试不是全部实机链路验证，也没有消费真实重置次数。
- 声音调度、重绘和 HTTPS 连接复用已修改；实际扬声器卡顿改善仍需用户听感验收。声音设置目前重启恢复默认。
- 当前 App 原生目录／网络授权的直接批准尚未接通。CLI 模式的协议实现不证明可以批准 App 当前会话。官方 App Server 部分传输仍属实验接口。
- Apple 原图、图像生成头文件、含图固件和原设备备份未随源码上传。新构建须自行提供适用素材权限。

此次 GitHub 源码快照另行通过：88 项 Python 回归、30 项 Swift 状态机／导航检查、控制器／音序检查及 8 组音频线程检查。清理路径后的源码以 ESP-IDF 5.5.3 和现有离线组件缓存成功构建，无 Apple 图像的应用镜像大小 1,380,864 字节；没有刷写设备。127 个纳入 Git 的文件经过路径、凭据模式和许可资源检查。启发式扫描不等于不存在所有可能的敏感信息。

## English

- Firmware baseline: 0.2.3; Bridge revision: 0.2.3-hookfix1; Mac demo: 0.4.0.
- The physical device has run 0.2.3 and synchronized account usage, battery and state over Wi-Fi. Account synchronization does not establish full approval coverage.
- The user verified real App permission notifications and hardware denial. A separate allow test continued to the Mac's native prompt; it was not a device-only native grant. These tests did not modify files in the requested directory.
- Latest tests in the original development tree: 88 Python tests, controller/tone checks, and eight audio-worker cases with mocked RTOS/BSP. The Mac demo baseline has 30 state/navigation checks.
- ESP-IDF 5.5.3 firmware built in the original environment. This shareable snapshot removes local paths and artwork; that does not establish clean-machine reproducibility or complete hardware acceptance.
- HTTPS polling and Unix WebSocket approvals have real host transport tests. Mock grants, reset redemption and audio checks do not establish every hardware path, and no real reset credits were spent.
- Audio scheduling, redraw frequency and HTTPS reuse were changed. Subjective speaker smoothness still needs acceptance. Sound settings currently reset on reboot.
- Direct approval of the desktop App's built-in directory/network grants is not connected. CLI protocol support does not prove access to an existing App session. Parts of the official App Server transport remain experimental.
- Apple artwork, generated image headers, artwork-containing firmware and flash backups are excluded. Supply appropriately authorized artwork for a new build.

This GitHub snapshot separately passed 88 Python regression tests, 30 Swift state/navigation checks, controller/tone checks and eight audio-worker cases. The sanitized source built successfully with ESP-IDF 5.5.3 and the existing offline component cache; the artwork-free application image is 1,380,864 bytes. No device was flashed. The 127 Git-indexed files were checked for blocked paths, credential patterns and licensed resources. Heuristic scanning does not establish the absence of every possible sensitive value.
