#!/usr/bin/env python3
"""Recover device transport without flashing, deleting pairing or closing the App."""
import argparse
import glob
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'bridge'))
from connection_diagnostics import inspect, show
from meter_client import request
from ipc_path import acquire_endpoint


def stop_idle_bridge(status):
    if status is None:return
    if status.get('permission_pending') or status.get('hook_pending'):
        raise RuntimeError('存在待处理审批，请先在 Mac 完成或取消，再恢复连接；未停止 Bridge。')
    if request({'type':'shutdown'}).get('stopping') is not True:
        raise RuntimeError('旧 Bridge 未确认停止；未强制结束进程。')
    for _ in range(60):
        try:
            lease=acquire_endpoint();lease.close();return
        except RuntimeError:time.sleep(.1)
    raise RuntimeError('旧 Bridge 尚未释放端口，请在其终端按 Control+C 后重试。')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check-only',action='store_true')
    args=parser.parse_args()
    report=inspect();show(report)
    if args.check_only:return
    print('不刷机、不清计数、不退出当前 App。',flush=True)
    print('1：USB 恢复（默认，数据线保持连接）\n2：重新配置当前 Wi-Fi（密码仅在本机隐藏输入）\nq：取消',flush=True)
    choice=input('选择 [1]：').strip() or '1'
    if choice=='q':return
    if choice not in ('1','2'):raise RuntimeError('未选择有效模式；未改动现有连接。')
    ports=glob.glob('/dev/cu.usbmodem*')
    if len(ports)!=1:raise RuntimeError('请连接一台 AI Passport，并关闭其他串口工具。')
    stop_idle_bridge(report['status'])
    if choice=='2':
        subprocess.run([sys.executable,str(ROOT/'scripts/pair_wifi.py')],check=True)
        port=''
    else:port=ports[0]
    print('即将恢复设备链路。App 审批仍需原 App 已通过实体审批入口启动。',flush=True)
    command=[sys.executable,str(ROOT/'bridge/service.py'),'--desktop','--port',port]
    os.execv(sys.executable,command)


if __name__=='__main__':
    try:main()
    except (OSError,ValueError,RuntimeError,subprocess.CalledProcessError) as error:sys.exit('恢复未完成：'+str(error))
    except (EOFError,KeyboardInterrupt):sys.exit('已取消；未刷机。')
