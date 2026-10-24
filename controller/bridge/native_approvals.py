"""Official App Server approvals for a CLI sharing this Bridge's Unix server.

Never attaches to a desktop process's private transport. Never starts a turn,
forks a thread, changes sandbox policy, or grants session-persistent permissions.
"""
import copy
import hashlib
import json
from pathlib import Path
import queue
import threading
import time
import uuid
from hook_policy import display as hook_display
from approval_review import native_view

from websockets.exceptions import WebSocketException
from websockets.sync.client import unix_connect


def permission_display(params):
    """Return a fully visible bounded grant, or require review in the CLI."""
    permissions=params.get('permissions')
    cwd=params.get('cwd')
    name=Path(cwd).name if isinstance(cwd,str) else ''
    fallback=('权限请求 · 在 CLI 查看',name,'范围过长或复杂 · CLI 审阅',False,{})
    if not name or not name.isascii() or len(name)>58 or params.get('environmentId') is not None:return fallback
    if not isinstance(permissions,dict) or set(permissions)-{'network','fileSystem'}:return fallback
    lines=['项目：'+name]; grant={}; kinds=[]
    network=permissions.get('network')
    if network is not None:
        if not isinstance(network,dict) or set(network)!={'enabled'} or network['enabled'] is not True:return fallback
        lines.append('网络连接权限'); grant['network']={'enabled':True}; kinds.append('网络')
    fs=permissions.get('fileSystem')
    if fs is not None:
        if not isinstance(fs,dict) or set(fs)-{'read','write','entries','globScanMaxDepth'} or fs.get('globScanMaxDepth') is not None:return fallback
        paths=[]; file_grant={}
        for mode,label in (('read','读取'),('write','写入')):
            values=fs.get(mode)
            if values is None:continue
            if not isinstance(values,list):return fallback
            for value in values:
                if not isinstance(value,str) or not value.isascii() or not value.startswith('/') or any(ord(c)<32 for c in value):return fallback
                paths.append((mode,value))
            if values:file_grant[mode]=list(values)
        entries=fs.get('entries')
        if entries is not None:
            if not isinstance(entries,list):return fallback
            for entry in entries:
                if not isinstance(entry,dict) or set(entry)!={'path','access'}:return fallback
                path=entry['path'];mode=entry['access']
                if not isinstance(path,dict) or set(path)!={'type','path'} or path['type']!='path' or mode not in ('read','write'):return fallback
                paths.append((mode,path['path']))
            if entries:file_grant['entries']=copy.deepcopy(entries)
        if any(not isinstance(value,str) for _,value in paths):return fallback
        paths=list(dict.fromkeys(paths))
        if len(paths)!=1:return fallback
        for mode,value in paths:
            p=Path(value)
            # Broad roots, hidden state and unresolved aliases need a full
            # CLI review. Never clip a path and leave approval enabled.
            if not value.isascii() or not value.startswith('/') or any(ord(c)<32 for c in value):return fallback
            if len(p.parts)<4 or '..' in p.parts or any(part.startswith('.') for part in p.parts[1:]):return fallback
            if len(p.parts)==4 and p.name in ('Documents','Downloads','Desktop'):return fallback
            if any(part in ('Library','System','etc','private','var','Applications') for part in p.parts[1:]):return fallback
            if str(p.resolve())!=value or len(value)>58:return fallback
            lines.append(('读取' if mode=='read' else '写入')+'：'+value)
        grant['fileSystem']=file_grant;kinds.append('目录')
    summary='\n'.join(lines)
    if not grant or len(summary.encode())>90 or len(summary)>78:return fallback
    return ('与'.join(kinds)+'权限请求',summary,'仅本轮 · 不保存长期权限',True,grant)


class NativeClient:
    """JSON-RPC text messages over the documented Unix WebSocket transport.

    `app-server proxy` only relays raw bytes; it doesn't convert JSONL into
    WebSocket messages. Use a WebSocket client for the HTTP upgrade and framing.
    """
    def __init__(self,socket_path,on_message,on_close):
        try:
            self.connection=unix_connect(str(socket_path),open_timeout=8,
                close_timeout=1,max_size=2*1024*1024,compression=None,proxy=None)
        except (WebSocketException,TimeoutError) as error:
            raise RuntimeError('Codex Unix WebSocket 握手失败：'+type(error).__name__) from error
        self.lock=threading.Lock();self.waiters={};self.counter=0;self.closed=threading.Event()
        self.error=''
        self.on_message=on_message;self.on_close=on_close
        self.reader=threading.Thread(target=self._read,daemon=True);self.reader.start()

    def send(self,message):
        with self.lock:
            if self.closed.is_set():raise OSError('CLI 审批连接已关闭')
            try:self.connection.send(json.dumps(message))
            except WebSocketException as error:raise OSError('Codex WebSocket 连接已断开') from error

    def rpc(self,method,params,timeout=12):
        if method not in ('initialize','account/read','thread/list','thread/read','thread/resume','thread/loaded/list'):
            raise ValueError('Passport never starts model turns or changes permission settings')
        with self.lock:
            self.counter+=1;identifier='passport-'+str(self.counter)
            waiter=queue.Queue(maxsize=1);self.waiters[identifier]=waiter
        try:
            self.send({'id':identifier,'method':method,'params':params})
            try:response=waiter.get(timeout=timeout)
            except queue.Empty as error:
                raise RuntimeError('Codex 接口 '+method+' 等待 '+str(timeout)+' 秒未响应') from error
            if 'error' in response:raise RuntimeError('Codex '+method+' 失败：'+str(response['error'].get('message','unknown'))[:240])
            return response.get('result',{})
        finally:
            with self.lock:self.waiters.pop(identifier,None)

    def _read(self):
        try:
            for frame in self.connection:
                if not isinstance(frame,str):raise ValueError('接口返回了非文本 WebSocket 消息')
                message=json.loads(frame)
                if not isinstance(message,dict):raise ValueError('接口返回了非对象 JSON')
                if 'method' in message:self.on_message(self,message)
                else:
                    with self.lock:waiter=self.waiters.get(message.get('id'))
                    if waiter:
                        try:waiter.put_nowait(message)
                        except queue.Full:pass
        except (OSError,WebSocketException,ValueError) as error:
            self.error='Codex WebSocket 读取失败：'+type(error).__name__
        finally:
            self.closed.set()
            with self.lock:
                for waiter in self.waiters.values():
                    try:waiter.put_nowait({'error':{'message':self.error or '连接中断'}})
                    except queue.Full:pass
            self.on_close(self)

    def close(self):
        self.closed.set();self.connection.close()
        if threading.current_thread() is not self.reader:self.reader.join(timeout=2)


class NativeApprovals:
    def __init__(self,broker,socket_path,thread_id,policy):
        self.broker=broker;self.socket_path=socket_path;self.thread_id=thread_id;self.policy=policy
        self.client=None;self.stopping=threading.Event();self.pending={};self.seen={};self.lock=threading.RLock()

    def start(self):
        threading.Thread(target=self._run,daemon=True).start()

    def _run(self):
        while not self.stopping.is_set():
            client=None
            try:
                client=NativeClient(self.socket_path,self.message,self.disconnected)
                with self.lock:self.client=client
                client.rpc('initialize',{'clientInfo':{'name':'passport_controller','version':'0.2.2'},'capabilities':{'experimentalApi':True}})
                client.send({'method':'initialized'})
                result=client.rpc('thread/resume',{'threadId':self.thread_id,'excludeTurns':True})
                if result.get('thread',{}).get('id')!=self.thread_id:raise RuntimeError('会话 ID 不匹配')
                with self.broker.lock:
                    self.broker.native_connected=True;self.broker.native_error=''
                    self.broker.notice=None
                print('CLI 原会话已接入实体审批：'+self.thread_id,flush=True)
                while not self.stopping.wait(.2) and not client.closed.is_set():pass
            except (OSError,RuntimeError,queue.Empty) as error:
                with self.broker.lock:self.broker.native_error=str(error) or 'App Server 等待超时'
            finally:
                if client:
                    self.disconnected(client);client.close()
            self.stopping.wait(2)

    def disconnected(self,client):
        with self.lock:
            if self.client is not client:return
            with self.broker.lock:
                self.broker.native_connected=False
                if self.broker.request and self.broker.request.get('source')=='native':self.broker.request['cancelled']=True
                self.broker.receipt='CLI 审批连接中断'
            for pending in self.pending.values():pending['resolved'].set()

    def message(self,client,message):
        method=message.get('method');params=message.get('params')
        if not isinstance(params,dict) or params.get('threadId')!=self.thread_id:return
        with self.lock:
            if self.client is not client:return
            if 'id' in message:
                if method not in ('item/permissions/requestApproval','item/commandExecution/requestApproval','item/fileChange/requestApproval'):return
                identifier=message['id']
                if type(identifier) not in (str,int):return
                key=json.dumps(identifier)
                self.seen={k:v for k,v in self.seen.items() if v>time.monotonic()}
                if key in self.seen or len(self.pending)>=16 or len(self.seen)>=64:return
                self.seen[key]=time.monotonic()+120
                pending={'resolved':threading.Event(),'id':identifier,'turn':params.get('turnId'),'sent':False}
                self.pending[key]=pending
                threading.Thread(target=self._approval,args=(client,copy.deepcopy(message),pending),daemon=True).start()
            elif method=='serverRequest/resolved':
                pending=self.pending.get(json.dumps(params.get('requestId')))
                if pending:
                    pending['resolved'].set()
                    if not pending['sent']:
                        with self.broker.lock:self.broker.receipt='请求已由 CLI 处理'
            elif method=='turn/completed':
                turn=params.get('turn',{})
                for pending in self.pending.values():
                    if pending['turn']==turn.get('id'):pending['resolved'].set()
                with self.broker.lock:
                    status=turn.get('status')
                    if status in ('completed','failed','interrupted'):
                        self.broker.set_state({'completed':'completed','failed':'failed','interrupted':'idle'}[status])
                        self.broker.receipt={'completed':'本轮响应已结束','failed':'任务失败 · 请在 CLI 查看','interrupted':'操作已中断'}[status]
                        self.broker.history.insert(0,self.broker.receipt);self.broker.history=self.broker.history[:20]
            elif method=='turn/started':
                with self.broker.lock:self.broker.set_state('working');self.broker.active_session=self.thread_id

    def _approval(self,client,message,pending):
        broker=self.broker;params=message['params'];method=message['method'];req=None
        try:
            started=params.get('startedAtMs')
            if not isinstance(started,(int,float)) or started>time.time()*1000+5000:return
            ttl=(600 if broker.review_protocol==1 else 110)-max(0,time.time()-started/1000)
            if ttl<=0 or not params.get('turnId') or not params.get('itemId'):return
            if method=='item/permissions/requestApproval':
                command,project,scope,can_allow,grant=permission_display(params)
                allow_result={'permissions':grant,'scope':'turn'}
                deny_result={'permissions':{},'scope':'turn'}
            else:
                command=params.get('command') or '文件修改 · 在 CLI 查看'
                cwd=params.get('cwd') or ''
                project=Path(cwd).name;scope='仅本次命令';can_allow=False
                if method=='item/commandExecution/requestApproval' and params.get('kind','command')=='command' and params.get('environmentId') is None and not params.get('networkApprovalContext'):
                    view=hook_display({'tool_name':'Bash','cwd':cwd,'tool_input':{'command':command}})
                    can_allow=view['can_allow'];scope=view['scope']
                    if can_allow:command=view['command'];project=view['project']
                if not can_allow:
                    scope='范围过长或复杂 · CLI 审阅'
                    if method=='item/commandExecution/requestApproval':command='复杂命令 · 在 CLI 查看'
                allow_result={'decision':'accept'};deny_result={'decision':'decline'}
            view=native_view(method,params) if broker.review_protocol==1 else None
            if view:
                command,project,scope,can_allow=(view[k] for k in ('command','project','scope','can_allow'))
                allow_result=view['allow_result'];deny_result=view['deny_result']
            with broker.lock:
                if not broker.online() or broker.request or pending['resolved'].is_set():return
                req={'id':str(uuid.uuid4()),'command':command,'project':project,'scope':scope,'can_allow':can_allow,
                     'deadline':time.monotonic()+ttl,'digest':hashlib.sha256(json.dumps(message,sort_keys=True).encode()).hexdigest(),
                     'choice':None,'cancelled':False,'boot':broker.boot,'session':self.thread_id,'source':'native'}
                if view:req.update(review_pages=view['review_pages'],review_index=0,review_furthest=0,review_delivered=-1)
                broker.request=req;broker.notice=None
            while time.monotonic()<req['deadline']:
                # Serialize resolutions and submissions. Never submit after a
                # CLI answer, reconnect, expired request, or device reboot.
                with self.lock,broker.lock:
                    if pending['resolved'].is_set() or self.client is not client or req['cancelled'] or not broker.online() or broker.boot!=req['boot']:return
                    choice=req['choice']
                    if choice in ('allow','deny'):
                        pending['sent']=True
                        if method=='item/permissions/requestApproval':
                            broker.native_awaiting={'session':self.thread_id,'turn':params['turnId'],'item':params['itemId'],'until':time.monotonic()+120}
                        client.send({'id':message['id'],'result':allow_result if choice=='allow' else deny_result})
                        broker.set_state('approval_sent' if choice=='allow' else 'denied')
                        broker.receipt='已提交'+('批准' if choice=='allow' else '拒绝')+'，等待 Codex 回执'
                        broker.history.insert(0,broker.receipt);broker.history=broker.history[:20]
                        broker.expression='' if choice=='allow' else 'crying';broker.expression_until=time.monotonic()+2.5
                        break
                if pending['resolved'].wait(.03):return
            else:
                with broker.lock:broker.receipt='请求已过期 · 请在 CLI 处理'
                return
            acknowledged=pending['resolved'].wait(max(0,min(5,req['deadline']-time.monotonic())))
            with broker.lock:
                if broker.native_awaiting is not None or method!='item/permissions/requestApproval':
                    broker.receipt='Codex 审批请求已结束' if acknowledged else '已提交，回执待确认'
                # Resolution alone does not prove which client won a race or
                # that a granted operation executed. Never fabricate success.
        except (OSError,ValueError,TypeError):
            with broker.lock:broker.receipt='审批连接中断 · 请在 CLI 查看'
        finally:
            with self.lock:self.pending.pop(json.dumps(message['id']),None)
            with broker.lock:
                if req is not None and broker.request is req:broker.request=None

    def close(self):
        self.stopping.set()
        with self.lock:
            client=self.client
            if client:self.disconnected(client)
        if client:client.close()
