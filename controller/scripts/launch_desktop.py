#!/usr/bin/env python3
"""Launch the desktop UI with a version-bound local standard-protocol relay.

The launch switches are present in this installed App build, not documented
stable public settings. Never patch the installed App or change global config.
"""
import hashlib
import json
import os
import re
from pathlib import Path
import signal
import struct
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'bridge'))
from ipc_path import acquire_endpoint
from host_platform import WINDOWS, desktop_app, powershell, usb_ports

APP=Path('/Applications/ChatGPT.app')
# Exact, locally inspected builds only. An unknown upgrade must fail closed.
VERIFIED_BUILDS = {
    '26.1016.62342': {
        '.vite/build/main-JI9qDiXp.js': 'b8c5d07cc3c30fbf0abe729b05434e7d1ffa19ee6c4daa818ae8f855be66d1e1',
    },
    '26.1027.30824': {
        '.vite/build/early-bootstrap.js': '5a4fe13a7371e73302b1cf10b54a035d16a77692ddb1c8de3c28c1c7e6fc5071',
        '.vite/build/early-bootstrap-824-3c24dda6dba622ec.js': 'c387296475ca0729e4be35c4831b512d39316e0f7e24fe4d631ad0d96ec8e13f',
        '.vite/build/early-bootstrap-916-2f6483d5bfd826f1.js': 'b50821d3723b10548c3321b9615140b8599033299c2890203c44b86ea7184e16',
    },
}

# Windows package 26.1027.3384.0 contains application version 26.1027.30824.
# These are separate platform artifacts; macOS digests are never reused.
WINDOWS_VERIFIED_BUILDS = {
    '26.1027.30824': {
        '.vite/build/early-bootstrap.js': '95314a94cb594f682bdb7b1f52eead05413645f6cf1419b733b4e3c54df14947',
        '.vite/build/early-bootstrap-339-096ec1020e8592e0.js': '25c8371f76e580829e8f387446901c5f09227fc645a0bce6efbfaaee2946ebc8',
        '.vite/build/early-bootstrap-491-e75c34fa1b2c0832.js': 'db3fd1590ec3d3c621a85c2cf925785ea6d99df8bc4eaec8bc4b1e974758a8ab',
        '.vite/build/early-bootstrap-824-e56448c7829c41c2.js': 'a785e3304e4e229cb5779d952475483e306bcf9ca7b34b8f21df15cea55c648a',
    },
}


def read_asar(stream,header,data_offset,path):
    entry=header
    for part in path.split('/'):entry=entry['files'][part]
    stream.seek(data_offset+int(entry['offset']))
    return stream.read(entry['size'])


def verify_build(app=None):
    app = Path(app) if app is not None else desktop_app()
    mac_layout = (app/'Contents').is_dir()
    archive = app/'Contents/Resources/app.asar' if mac_layout else app/'resources/app.asar'
    try:
        with archive.open('rb') as stream:
            sizes=struct.unpack('<4I',stream.read(16))
            if not 0<sizes[3]<16*1024*1024:raise ValueError('App archive header is unsupported')
            header=json.loads(stream.read(sizes[3]));data_offset=8+sizes[1]
            package=json.loads(read_asar(stream,header,data_offset,'package.json'))
            version=package.get('version')
            expected=(VERIFIED_BUILDS if mac_layout else WINDOWS_VERIFIED_BUILDS).get(version)
            if not expected:
                raise ValueError('桌面 App 版本 '+str(version)+' 尚未核对；未启用旧版适配。设备同步仍可单独启动。')
            sources=[]
            for path,digest in expected.items():
                source=read_asar(stream,header,data_offset,path)
                if hashlib.sha256(source).hexdigest()!=digest:
                    raise ValueError('桌面 App 启动文件已变化；未启用旧版适配。设备同步仍可单独启动。')
                sources.append(source)
        combined=b'\n'.join(sources)
        if b'CODEX_APP_SERVER_FORCE_CLI' not in combined or b'CODEX_CLI_PATH' not in combined:
            raise ValueError('桌面 App 没有已核对的本地执行器启动开关')
        return version
    except (KeyError,struct.error,UnicodeError) as error:
        raise ValueError('桌面 App 文件布局无法识别；请保留原 App，先运行恢复 Bridge 连接入口。') from error


def stop_bridge(process):
    if process and process.poll() is None:
        if WINDOWS:
            from meter_client import request
            try:request({'type':'shutdown'})
            except (OSError, ValueError):pass
        else:process.send_signal(signal.SIGINT)
        try:process.wait(timeout=5)
        except subprocess.TimeoutExpired:process.terminate();process.wait(timeout=3)


def app_is_running():
    """Treat a failed process probe as unknown, never as an exited App."""
    if WINDOWS:
        values = json.loads(powershell("ConvertTo-Json -Compress -InputObject @(Get-CimInstance Win32_Process -Filter \"Name='ChatGPT.exe' OR Name='Codex.exe'\" | Select-Object -ExpandProperty ExecutablePath)"))
        if not isinstance(values,list) or any(not isinstance(v,str) or not v for v in values):
            raise RuntimeError('无法检查 桌面 App 是否运行；未启动或停止 Bridge。')
        override=os.environ.get('COMPANION_DESKTOP_APP')
        return any(re.search(r'\\OpenAI[.]Codex_[^\\]+\\app\\(ChatGPT|Codex)[.]exe$',value,re.I)
                   or (override and Path(value).parent.resolve()==Path(override).resolve()) for value in values)
    result=subprocess.run(['/usr/bin/pgrep','-f','^/Applications/ChatGPT.app/Contents/MacOS/ChatGPT'],
                          capture_output=True)
    if result.returncode not in (0,1):
        raise RuntimeError('无法检查 桌面 App 是否运行；未启动或停止 Bridge。')
    return result.returncode==0


def main():
    print('桌面 App 实体审批接入：保留 App 界面与账户，不打开 CLI 操作界面。',flush=True)
    print('Controller 0.2.13 · 原 App 原生审批与设备同步 · 双端直接允许或拒绝。',flush=True)
    print('程序目录：'+str(ROOT),flush=True)
    from usage_meter import load_rates
    rates=load_rates(ROOT/'private'/'token_rates.json')
    print('已配置费率模型：'+(', '.join(sorted(rates['models'])) or '无'),flush=True)
    from connection_diagnostics import inspect, show
    show(inspect())
    app_root=desktop_app()
    version=verify_build(app_root)
    if app_is_running():
        raise RuntimeError('请先手动完全退出 桌面 App，再运行本入口；不会自动关闭正在工作的 App。')
    lease=acquire_endpoint();lease.close()
    private=ROOT/'private';private.mkdir(mode=0o700,exist_ok=True)
    if WINDOWS:
        from windows_security import secure_directory
        secure_directory(private)
    bridge=app=None
    with (private/'desktop-bridge.log').open('ab') as bridge_log,(private/'desktop-app.log').open('ab') as app_log:
        try:
            ports=usb_ports() if not (private/'wireless.json').exists() else []
            if len(ports)>1:raise RuntimeError('检测到多台设备，未自动选择 USB 目标。')
            child_options={'creationflags': subprocess.CREATE_NO_WINDOW} if WINDOWS else {'start_new_session':True}
            bridge=subprocess.Popen([sys.executable,str(ROOT/'bridge/service.py'),'--desktop','--port',ports[0] if ports else ''],
                stdout=bridge_log,stderr=bridge_log,**child_options)
            time.sleep(.5)
            if bridge.poll() is not None:raise RuntimeError('Bridge 未启动，请先在旧 Bridge 终端 Control+C。日志：private/desktop-bridge.log')
            import ssl
            import serial
            import websockets
            runtime={'recorded_at':int(time.time()),'executable':sys.executable,
                     'base_prefix':sys.base_prefix,'python':sys.version.split()[0],
                     'ssl':ssl.OPENSSL_VERSION,'pyserial':serial.VERSION,
                     'websockets':websockets.__version__,'app_version':version,
                     'note':'Bridge process started; not a device approval acceptance result'}
            runtime_path=private/'active-python.json'
            runtime_path.write_text(json.dumps(runtime,indent=2)+'\n');runtime_path.chmod(0o600)
            print('Bridge Python：'+sys.executable,flush=True)
            env=dict(os.environ)
            env['CODEX_APP_SERVER_FORCE_CLI']='1'
            env['CODEX_CLI_PATH']=str(private/'app-relay.exe' if WINDOWS else ROOT/'scripts/app_relay.command')
            env['PASSPORT_REAL_CODEX']=str(app_root/'resources/codex.exe' if WINDOWS else app_root/'Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS/codex')
            if not Path(env['CODEX_CLI_PATH']).is_file():raise RuntimeError('relay 启动器缺失；请先通过本平台控制台入口准备环境。')
            app=subprocess.Popen([str(app_root/'ChatGPT.exe' if WINDOWS else app_root/'Contents/MacOS/ChatGPT')],env=env,
                stdout=app_log,stderr=app_log,**child_options)
            print('已启动 App '+version+'；请打开原来的本地聊天。',flush=True)
            print('设备连接页出现「App 实体审批已接入」后，再进行批准 / 拒绝测试。',flush=True)
            print('如果没有出现该状态，本次接入没有成功；不要把“在 Mac确认”当成设备批准。',flush=True)
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
