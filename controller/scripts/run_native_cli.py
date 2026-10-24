#!/usr/bin/env python3
"""Continue a selected real Codex thread through a private shared App Server."""
import argparse
import errno
import fcntl
import json
import os
from pathlib import Path
import queue
import shutil
import signal
import socket
import stat
import subprocess
import sys
import time
import uuid

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'bridge'))
from ipc_path import SOCKET,acquire_endpoint,check_directory
from native_approvals import NativeClient


def plain(value):
    return ''.join(c if c.isprintable() else '?' for c in str(value))


def ipc_status():
    with socket.socket(socket.AF_UNIX) as connection:
        connection.settimeout(.5);connection.connect(str(check_directory()))
        connection.sendall(b'{"type":"status"}\n')
        with connection.makefile('rb') as stream:return json.loads(stream.readline(8192))


def stop(process):
    if process and process.poll() is None:
        process.send_signal(signal.SIGINT)
        try:process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.terminate()
            try:process.wait(timeout=3)
            except subprocess.TimeoutExpired:process.kill();process.wait()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--thread',help='Existing thread UUID; otherwise choose from recent threads')
    parser.add_argument('--check',action='store_true',help='Read-only real App Server startup and protocol check; no resume or model turn')
    args=parser.parse_args()
    if args.check and args.thread:parser.error('--check cannot resume a thread')
    if args.thread:uuid.UUID(args.thread)
    binary=os.environ.get('COMPANION_CODEX') or shutil.which('codex')
    if not binary:raise RuntimeError('未找到官方 Codex CLI')
    os.umask(0o077)
    lease=acquire_endpoint();lease.close() # Refuse a still-running Bridge.
    address=SOCKET.with_name('codex-native.sock')
    fd=os.open(address.with_suffix('.lock'),os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
    native_lease=os.fdopen(fd,'a')
    try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:raise RuntimeError('另一份 CLI 控制模式已在运行')
    if address.exists():
        info=address.lstat()
        if not stat.S_ISSOCK(info.st_mode) or info.st_uid!=os.getuid():raise RuntimeError('审批 socket 类型或所有者不符')
        with socket.socket(socket.AF_UNIX) as probe:
            probe.settimeout(.5)
            try:probe.connect(str(address))
            except OSError as error:
                if error.errno not in (errno.ECONNREFUSED,errno.ENOENT):raise
            else:raise RuntimeError('原审批 App Server 仍在运行；不会覆盖')
        address.unlink()
    private=ROOT/'private';private.mkdir(exist_ok=True)
    server=bridge=client=None
    server_log=(private/'native-server.log').open('a')
    bridge_log=(private/'native-bridge.log').open('a')
    try:
        print('1/4 启动官方 App Server（仅本机私有 socket）…',flush=True)
        server=subprocess.Popen([binary,'app-server','--listen','unix://'+str(address)],
                                stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=server_log)
        deadline=time.monotonic()+15
        while not address.exists():
            if server.poll() is not None or time.monotonic()>deadline:raise RuntimeError('App Server 启动失败，日志：private/native-server.log')
            time.sleep(.1)
        os.chmod(address,0o600)
        print('2/4 进行 Unix WebSocket 握手并初始化…',flush=True)
        client=NativeClient(address,lambda *_:None,lambda *_:None)
        client.rpc('initialize',{'clientInfo':{'name':'passport_session_picker','version':'0.2.2'},'capabilities':{'experimentalApi':True}})
        client.send({'method':'initialized'})
        print('3/4 只读验证已登录的 ChatGPT 账户…',flush=True)
        account=client.rpc('account/read',{'refreshToken':False}).get('account')
        if not isinstance(account,dict) or account.get('type')!='chatgpt':
            raise RuntimeError('需要原 ChatGPT 账户登录；请在终端运行 codex login，不会改用 API Key 计费')
        print('ChatGPT 账户已验证；没有消费模型额度或额外重置次数。')
        if args.check:
            print('4/4 只读检查会话列表…',flush=True)
            client.rpc('thread/loaded/list',{'limit':1})
            client.rpc('thread/list',{'limit':1,'useStateDbOnly':True})
            print('官方 CLI 实体审批接口检查通过：Unix 连接、初始化、会话列表正常。')
            print('未恢复 / 创建会话，未发送模型任务、权限决定或额度重置。')
            return
        if args.thread:
            target=client.rpc('thread/read',{'threadId':args.thread}).get('thread',{})
        else:
            print('正式接管前请确认已用 Command+Q 完全退出桌面 App，释放原会话。')
            data=client.rpc('thread/list',{'limit':15,'sortKey':'updated_at','archived':False,'useStateDbOnly':True}).get('data',[])
            if not data:raise RuntimeError('没有可继续的原会话；本脚本不会新建无关会话')
            print('选择要继续的原会话；保留同一 ID 与历史，不 fork、不新建：')
            for i,thread in enumerate(data,1):
                print(str(i)+'. '+plain(thread.get('name') or '未命名')+' ['+thread['id']+']')
                print('   '+plain(thread.get('cwd','')))
            answer=input('输入会话序号；q 取消：').strip()
            if answer.lower()=='q':return
            if not answer.isdigit() or not 1<=int(answer)<=len(data):raise RuntimeError('无效序号，未接管任何会话')
            target=data[int(answer)-1]
        identifier=target.get('id');uuid.UUID(identifier)
        client.close();client=None
        print('继续原会话：'+plain(target.get('name') or identifier))
        print('若该会话仍由桌面 App 加载，请先用 Command+Q 完全退出桌面 App。不会自动关闭或抢占它。')
        print('启动实体审批 Bridge；设备断线 / 超时后仍可在 CLI 原生页面处理。')
        bridge=subprocess.Popen([sys.executable,str(ROOT/'bridge/service.py'),'--native-socket',str(address),'--thread',identifier],
                                stdout=bridge_log,stderr=bridge_log)
        deadline=time.monotonic()+18;last_error=''
        while time.monotonic()<deadline:
            if bridge.poll() is not None:raise RuntimeError('Bridge 启动失败；先停止旧 Bridge，日志：private/native-bridge.log')
            try:
                status=ipc_status();native=status.get('native',{})
                if native.get('connected') and native.get('thread')==identifier:break
                last_error=native.get('error') or last_error
            except (OSError,ValueError):pass
            time.sleep(.2)
        else:raise RuntimeError('无法接入原会话。请完全退出桌面 App 后重试；不会复制历史建立新会话。 '+last_error)
        print('实体审批已接入。下面是官方 CLI；按键批准仅限本次 / 本轮，不保存长期权限。')
        print('复杂或显示不全的请求在 CLI 审阅；关闭 CLI 会结束本次 Bridge，原会话历史保留。')
        result=subprocess.run([binary,'resume',identifier,'--remote','unix://'+str(address)])
        if result.returncode:raise RuntimeError('CLI 已退出，代码 '+str(result.returncode))
    finally:
        if client:client.close()
        stop(bridge);stop(server)
        if address.exists():address.unlink()
        server_log.close();bridge_log.close();native_lease.close()


if __name__=='__main__':
    try:main()
    except KeyboardInterrupt:pass
    except (OSError,RuntimeError,ValueError,queue.Empty) as error:sys.exit(str(error) or '接口未响应；本次流程已停止')
