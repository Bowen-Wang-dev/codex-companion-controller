"""Discover and probe the documented local App Server; never spawn a server."""
import json
import os
from pathlib import Path
import stat
import time

from native_approvals import NativeClient


def control_socket(codex_home=None):
    home=Path(codex_home or os.environ.get('CODEX_HOME') or Path.home()/'.codex')
    return home/'app-server-control'/'app-server-control.sock'


def validate_socket(address):
    """The official listener may be a symlink into a private daemon directory."""
    address=Path(address)
    target=address.resolve(strict=True)
    info=target.stat();parent=target.parent.stat()
    if not stat.S_ISSOCK(info.st_mode) or info.st_uid!=os.getuid():
        raise ValueError('控制接口不是当前用户拥有的 Unix socket')
    if parent.st_uid!=os.getuid() or stat.S_IMODE(parent.st_mode)&0o022:
        raise ValueError('控制接口目录权限过宽，拒绝连接')
    return address


def initialize(client):
    result=client.rpc('initialize',{'clientInfo':{'name':'passport_desktop_bridge',
        'title':'AI Passport Desktop Companion','version':'0.3.0'},
        'capabilities':{'experimentalApi':True,
            'optOutNotificationMethods':['item/agentMessage/delta','item/reasoning/textDelta',
                'item/reasoning/summaryTextDelta','item/commandExecution/outputDelta']}},timeout=8)
    client.send({'method':'initialized'})
    return result


def probe(address=None,expected_thread=None):
    """Only initialize and list loaded IDs. No resume, model task, or decisions."""
    report={'version':1,'checked_at':int(time.time()),'connected':False,
        'expected_thread':expected_thread,'expected_loaded':False,'thread_ids':[],
        'read_only':True,'error':''}
    client=None
    try:
        address=validate_socket(address or control_socket())
        client=NativeClient(address,lambda *_:None,lambda *_:None)
        initialized=initialize(client)
        loaded=client.rpc('thread/loaded/list',{'limit':100},timeout=8)
        ids=loaded.get('data')
        if not isinstance(ids,list) or any(not isinstance(value,str) for value in ids):
            raise ValueError('已加载会话列表格式不匹配')
        report.update(connected=True,thread_ids=ids,
            expected_loaded=bool(expected_thread and expected_thread in ids),
            server_version=str(initialized.get('userAgent',''))[:160])
    except (OSError,RuntimeError,ValueError) as error:
        report['error']=type(error).__name__+': '+str(error)[:240]
    finally:
        if client:client.close()
    return report


def save_report(path,report):
    path=Path(path);path.parent.mkdir(parents=True,mode=0o700,exist_ok=True)
    temporary=path.with_suffix('.tmp')
    with temporary.open('w') as stream:
        os.chmod(temporary,0o600)
        json.dump(report,stream,ensure_ascii=False,indent=2)
        stream.write('\n');stream.flush();os.fsync(stream.fileno())
    os.replace(temporary,path)
