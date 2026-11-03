#!/usr/bin/env python3
"""User-driven App restart; never close the active chat automatically."""
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
from connection_diagnostics import inspect, show
from launch_desktop import app_is_running, verify_build
from recover_bridge import stop_idle_bridge
from host_platform import exec_process


def main():
    version=verify_build()
    print('已核对本机 App '+version+' 的启动接口；不刷机、不重配 Wi-Fi、不改账户。',flush=True)
    show(inspect())
    print('请先完成当前操作并保存工作，再手动完全退出 PC 端 App。',flush=True)
    print('回到本控制台按回车，由已核对入口启动 App。',flush=True)
    if input('App 已退出后按回车继续；输入 q 取消：').strip().lower()=='q':return
    if app_is_running():raise RuntimeError('App 仍在运行；没有停止 Bridge。请先手动完全退出后重试。')
    stop_idle_bridge(inspect()['status'])
    exec_process(sys.executable,[sys.executable,str(ROOT/'scripts/launch_desktop.py')])


if __name__=='__main__':
    try:main()
    except (OSError,ValueError,RuntimeError) as error:sys.exit('App 审批接入未完成：'+str(error))
    except (KeyboardInterrupt,EOFError):sys.exit('已取消；未自动关闭 App。')
