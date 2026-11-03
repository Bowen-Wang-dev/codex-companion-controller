"""Read-only Windows readiness checks; no App restart, account RPC or USB open."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'bridge'))
from console_i18n import tr
from host_platform import desktop_app, usb_ports, openssl_binary
from launch_desktop import verify_build, app_is_running
from connection_diagnostics import inspect, show


def main():
    print(tr('Windows 环境检查（不打开串口、不启动或关闭 App、不读取登录凭据）'))
    app = desktop_app()
    print(tr('App 目录：')+str(app))
    print(tr('App 启动文件版本/摘要：通过 · ')+verify_build(app))
    print(tr('App 运行中：')+str(app_is_running()))
    print(tr('USB 候选：')+(', '.join(usb_ports()) or tr('未发现 ESP32-C3 USB Serial/JTAG')))
    try:print(tr('配网 OpenSSL：')+openssl_binary())
    except RuntimeError as error:print(tr('配网前需处理：')+str(error))
    show(inspect())
    return 0


if __name__ == '__main__':
    try:sys.exit(main())
    except (OSError, RuntimeError, ValueError) as error:sys.exit(tr('Windows 检查未完成：')+str(error))
