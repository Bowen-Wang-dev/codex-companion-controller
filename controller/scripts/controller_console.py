#!/usr/bin/env python3
"""Unified Finder entry for Codex App, device transport and local metering."""
import glob
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'bridge'));sys.path.insert(0,str(ROOT/'scripts'))
from connection_diagnostics import inspect,show
from meter_client import request
from recover_bridge import stop_idle_bridge

PY=sys.executable


def run(*parts):
    return subprocess.run([PY,*map(str,parts)],cwd=ROOT).returncode


def device_bridge_menu():
    report=inspect();show(report)
    print('\n1 诊断状态\n2 安全重启 Bridge（保留现有配对）\n3 恢复 USB / 重配 Wi-Fi\nq 返回')
    choice=input('选择：').strip().lower()
    if choice=='1':return
    if choice=='3':run(ROOT/'scripts/recover_bridge.py');return
    if choice!='2':return
    status=report['status']
    stop_idle_bridge(status)
    wireless=ROOT/'private/wireless.json'
    ports=glob.glob('/dev/cu.usbmodem*')
    port='' if wireless.exists() else ports[0] if len(ports)==1 else None
    if port is None:
        raise RuntimeError('没有无线配对记录，也没有唯一 USB 设备；请先选恢复／配网。')
    print('正在用现有配对启动 Bridge；关闭本终端会停止服务。',flush=True)
    os.execv(PY,[PY,str(ROOT/'bridge/service.py'),'--desktop','--port',port])


def billing_menu():
    print('价格编辑器：custom 或 OpenAI 官方价格 × 倍率（默认 1）；保存后 Bridge 热加载。')
    run(ROOT/'bridge/token_rates_gui.py')


def usage_menu():
    print('\n1 显示当前累计\n2 只读核对最近一小时\n3 清零本机计数（需再输入 RESET）\nq 返回')
    choice=input('选择：').strip().lower()
    if choice=='1':run(ROOT/'scripts/metering.py')
    elif choice=='2':run(ROOT/'scripts/audit_usage.py')
    elif choice=='3':run(ROOT/'scripts/metering.py','--reset')


def pairing_menu():
    report=inspect();stop_idle_bridge(report['status'])
    code=run(ROOT/'scripts/pair_wifi.py')
    if code==0:
        print('配对完成；启动无线 Bridge。关闭终端会停止服务。',flush=True)
        os.execv(PY,[PY,str(ROOT/'bridge/service.py'),'--desktop','--port',''])


def hooks_menu():
    print('此操作注册本机用户级 Hook，不改账号或固件。之后需在 Codex 审阅并信任。')
    if input('输入 YES 安装／更新 Hook；其他输入返回：').strip()!='YES':return
    project=ROOT.parent.parent
    subprocess.run([PY,str(ROOT/'scripts/install_hooks.py'),'--user','--remove-project-copy',str(project)],cwd=ROOT)
    print('请在 Codex 审阅并信任 Passport Hook，再通过菜单启动桌面 App 审批。')


def main():
    print('Codex Companion 控制台 · AI Passport')
    print('USB 方向键与确认键审批由设备固件处理；此处管理 Mac Bridge 和费率。')
    actions={
        '1':('启动 Codex App + 实体按键审批',lambda:run(ROOT/'scripts/launch_desktop.py')),
        '2':('设备 / Bridge 连接管理',device_bridge_menu),
        '3':('首次配对或更新 Wi-Fi',pairing_menu),
        '4':('Token 计费方式、基准价、长上下文及倍率',billing_menu),
        '5':('Token 统计、只读核对、本机清零',usage_menu),
        '6':('安装／修复 Codex Hooks',hooks_menu),
        '7':('设备固件与备份维护（USB）',lambda:subprocess.run([str(ROOT/'维护工具'/'更新Token计量与清零固件.command')],cwd=ROOT).returncode),
    }
    while True:
        print('\n'+ '\n'.join(f'{key}  {title}' for key,(title,_) in actions.items())+'\nq 退出')
        choice=input('选择：').strip().lower()
        if choice in ('q','quit','exit'):return
        if choice not in actions:
            print('未识别该选项。');continue
        try:
            actions[choice][1]()
        except (OSError,ValueError,RuntimeError,subprocess.SubprocessError) as error:
            print('操作未完成：'+str(error))
        if choice not in ('1','2','3','7'):
            input('按回车返回控制台。')


if __name__=='__main__':
    try:main()
    except (EOFError,KeyboardInterrupt):print('\n控制台已退出。')
