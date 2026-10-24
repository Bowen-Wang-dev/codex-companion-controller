#!/usr/bin/env python3
"""Launch the desktop UI with a version-bound local standard-protocol relay.

The launch switches are present in this installed App build, not documented
stable public settings. Never patch the installed App or change global config.
"""
import hashlib
import json
import os
from pathlib import Path
import signal
import struct
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'bridge'))
from ipc_path import acquire_endpoint

APP=Path('/Applications/ChatGPT.app')
BUILD='26.1016.62342'
MAIN='.vite/build/main-JI9qDiXp.js'
MAIN_SHA='b8c5d07cc3c30fbf0abe729b05434e7d1ffa19ee6c4daa818ae8f855be66d1e1'


def read_asar(stream,header,data_offset,path):
    entry=header
    for part in path.split('/'):entry=entry['files'][part]
    stream.seek(data_offset+int(entry['offset']))
    return stream.read(entry['size'])


def verify_build(app=APP):
    with (app/'Contents/Resources/app.asar').open('rb') as stream:
        sizes=struct.unpack('<4I',stream.read(16))
        if not 0<sizes[3]<16*1024*1024:raise ValueError('App archive header is unsupported')
        header=json.loads(stream.read(sizes[3]));data_offset=8+sizes[1]
        package=json.loads(read_asar(stream,header,data_offset,'package.json'))
        source=read_asar(stream,header,data_offset,MAIN)
    if package.get('version')!=BUILD or hashlib.sha256(source).hexdigest()!=MAIN_SHA:
        raise ValueError('桌面 App 已变化；须重新核对启动接口，未启用旧版适配')
    if b'CODEX_APP_SERVER_FORCE_CLI' not in source or b'CODEX_CLI_PATH' not in source:
        raise ValueError('桌面 App 没有已核对的本地执行器启动开关')
    return package['version']


def stop_bridge(process):
    if process and process.poll() is None:
        process.send_signal(signal.SIGINT)
        try:process.wait(timeout=5)
        except subprocess.TimeoutExpired:process.terminate();process.wait(timeout=3)


def main():
    print('桌面 App 实体审批接入：保留 App 界面与账户，不打开 CLI 操作界面。',flush=True)
    print('此启动适配使用已安装版本的内部开关；尚需真实 App 联调验收。',flush=True)
    version=verify_build()
    running=subprocess.run(['/usr/bin/pgrep','-f','^/Applications/ChatGPT.app/Contents/MacOS/ChatGPT'],capture_output=True)
    if running.returncode==0:
        raise RuntimeError('请先 Command+Q 完全退出桌面 App，再运行本入口；不会自动关闭正在工作的 App。')
    lease=acquire_endpoint();lease.close()
    private=ROOT/'private';private.mkdir(mode=0o700,exist_ok=True)
    bridge=app=None
    with (private/'desktop-bridge.log').open('ab') as bridge_log,(private/'desktop-app.log').open('ab') as app_log:
        try:
            bridge=subprocess.Popen([sys.executable,str(ROOT/'bridge/service.py'),'--desktop'],
                stdout=bridge_log,stderr=bridge_log,start_new_session=True)
            time.sleep(.5)
            if bridge.poll() is not None:raise RuntimeError('Bridge 未启动，请先在旧 Bridge 终端 Control+C。日志：private/desktop-bridge.log')
            env=dict(os.environ)
            env['CODEX_APP_SERVER_FORCE_CLI']='1'
            env['CODEX_CLI_PATH']=str(ROOT/'scripts/app_relay.command')
            env['PASSPORT_REAL_CODEX']=str(APP/'Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS/codex')
            app=subprocess.Popen([str(APP/'Contents/MacOS/ChatGPT')],env=env,
                stdout=app_log,stderr=app_log,start_new_session=True)
            print('已启动 App '+version+'；请打开原来的本地聊天。',flush=True)
            print('设备连接页出现「App 实体审批已接入」后，再进行批准 / 拒绝测试。',flush=True)
            print('如果没有出现该状态，本次接入没有成功；不要把“在 Mac 确认”当成设备批准。',flush=True)
            print('关闭 App 后本次 Bridge 自动停止；日后仍通过这个入口启动。',flush=True)
            while app.poll() is None:
                if bridge.poll() is not None:raise RuntimeError('Bridge 已退出；App 可继续处理原生请求，请检查私有日志。')
                time.sleep(.5)
        finally:
            stop_bridge(bridge)
    return app.returncode if app else 1


if __name__=='__main__':
    os.umask(0o077)
    try:sys.exit(main())
    except KeyboardInterrupt:print('实体审批 Bridge 已停止。')
    except (OSError,RuntimeError,ValueError,KeyError,struct.error) as error:sys.exit(str(error))
