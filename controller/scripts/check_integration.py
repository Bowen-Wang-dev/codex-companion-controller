#!/usr/bin/env python3
"""Read-only configuration/Bridge diagnostic. Does not start a Codex model turn."""
import json
import os
from pathlib import Path
import queue
import shutil
import socket
import subprocess
import sys
import threading

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'bridge'))
from ipc_path import check_directory


def hook_metadata(cwd, binary):
    process=subprocess.Popen([binary,'app-server','--stdio'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,
                             stderr=subprocess.DEVNULL,text=True)
    messages=queue.Queue()
    def receive():
        for line in process.stdout:
            try:messages.put(json.loads(line))
            except ValueError:pass
        messages.put({'closed':True})
    threading.Thread(target=receive,daemon=True).start()
    def request(identifier,method,params):
        # Only these read-only methods are ever sent. No thread/start/resume,
        # turn/start, permission response, hook trust change or account reset.
        assert method in ('initialize','hooks/list')
        process.stdin.write(json.dumps({'id':identifier,'method':method,'params':params})+'\n');process.stdin.flush()
        while True:
            result=messages.get(timeout=15)
            if result.get('closed'):raise RuntimeError('Codex 配置读取提前结束')
            if result.get('id')==identifier:
                if 'error' in result:raise RuntimeError('Codex 配置读取失败：'+str(result['error'].get('code')))
                return result.get('result',{})
    try:
        request(1,'initialize',{'clientInfo':{'name':'passport_hooks_check','version':'0.2.1'},
                                'capabilities':{'experimentalApi':True}})
        process.stdin.write('{"method":"initialized"}\n');process.stdin.flush()
        return request(2,'hooks/list',{'cwds':[str(cwd)]})
    finally:
        process.terminate()
        try:process.wait(timeout=3)
        except subprocess.TimeoutExpired:process.kill();process.wait()


def main():
    cwd=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else ROOT.parent
    print('检查聊天目录：',cwd)
    try:
        with socket.socket(socket.AF_UNIX) as connection:
            connection.settimeout(2);connection.connect(str(check_directory()))
            connection.sendall(b'{"type":"status"}\n')
            with connection.makefile('rb') as stream:status=json.loads(stream.readline(4096))
        if 'hook_count' not in status:
            print('Bridge 还是旧版，请先停止旧 Bridge 并重新启动。')
        else:
            print('设备在线：',status['online'],'连接：',status['transport'],'固件：',status['firmware'])
            if status.get('bridge_revision'):print('Bridge 修订：',status['bridge_revision'])
            print('已收到 Hook：',status['hook_count'],'最近事件距今秒数：',status['hook_age'])
            if status.get('notification_version',0)<2:
                print('当前 Bridge 尚未加载网络权限提醒修复。先在旧 Bridge 终端 Control+C，再运行「仅启动桥接.command」；无需刷机或重启桌面应用。')
            else:
                print('通知处理版本：',status['notification_version'],'事件类型计数：',status.get('event_counts',{}))
                print('工具事件计数：',status.get('tool_counts',{}))
            if status.get('audio'):print('设备音频诊断：',status['audio'])
            if status.get('notification_version',0)>=3:
                print('App 审批能力：',status.get('approval_capabilities',{}))
                print('排队 Hook：',status.get('hook_pending',0),'完成状态停留秒数：',status.get('completion_hold_seconds'))
            if status.get('native',{}).get('thread'):
                print('CLI 原会话实体审批：',status['native']['connected'],'会话：',status['native']['thread'])
                if status['native'].get('error'):print('CLI 接入提示：',status['native']['error'])
    except (OSError,ValueError):print('Bridge 未连接，请先运行「仅启动桥接」。')
    binary=os.environ.get('COMPANION_CODEX') or shutil.which('codex')
    if not binary:raise RuntimeError('未找到 Codex CLI')
    data=hook_metadata(cwd,binary)
    own=[]
    for entry in data.get('data',[]):
        for hook in entry.get('hooks',[]):
            if str(ROOT/'bridge'/'hook.py') in hook.get('command',''):
                own.append(hook)
    print('发现 Passport Hook：',len(own))
    for h in own:print(h.get('eventName'), '启用='+str(h.get('enabled')), '信任='+str(h.get('trustStatus')))
    if not own:print('尚未注册。运行「安装通知接入.command」，然后在 Codex 审阅并信任 Hook。')
    elif any(h.get('trustStatus') not in ('trusted','managed') for h in own):
        print('存在未信任或已修改的 Hook。Codex 会跳过它们；请手动审阅信任，CLI 使用 /hooks。')
    print('此检查读取磁盘配置，不代表桌面应用的旧会话已重载。没有发送模型任务或测试批准。')
    print('若刚安装 / 信任 Hook 而计数仍为 0：保持 Bridge 运行，用 Command+Q 完全退出桌面应用，再打开原聊天并发起新请求。')
    print('仅切换聊天或关闭窗口不保证卸载旧会话；不要因此重复刷机、配网或 Trust All。')


if __name__=='__main__':
    try:main()
    except (OSError,RuntimeError,queue.Empty) as error:sys.exit('检查未完成：'+str(error))
