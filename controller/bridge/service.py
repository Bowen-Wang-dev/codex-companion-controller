#!/usr/bin/env python3
"""Paired USB/HTTPS controller and official lifecycle hooks; no model tasks."""
import argparse
import datetime
import hashlib
import json
import os
import select
from pathlib import Path
import socketserver
import threading
import time
import uuid
from account import AccountClient
from ipc_path import SOCKET, acquire_endpoint
from wireless import start_https
from hook_policy import display as hook_display, permission_tool, permission_summary
from approval_review import native_view, hook_text, pages as review_pages

ROOT = Path(__file__).resolve().parents[1]

def excerpt(value,limit):
    return str(value).encode('utf-8')[:limit].decode('utf-8','ignore')


def desktop_reply(broker,event,connection,stream,interval=20):
    """Keep a long JSONL reply alive for already-running relay processes.

    Leading JSON whitespace is compatible with their existing readline/json
    reader. It carries no decision and never extends the approval deadline.
    """
    done=threading.Event();closed=threading.Event();result=[];errors=[]
    def alive():
        return not closed.is_set() and not select.select([connection],[],[],0)[0]
    def review():
        try:result.append(broker.desktop_request(event,alive))
        except Exception as error:errors.append(error)
        finally:done.set()
    worker=threading.Thread(target=review,daemon=True);worker.start()
    try:
        while not done.wait(interval):stream.write(b' ');stream.flush()
        if errors:raise errors[0]
        return result[0]
    finally:
        closed.set()


class Broker:
    def __init__(self):
        self.lock = threading.RLock()
        self.epoch = str(uuid.uuid4())
        self.boot = ''
        self.last_seen = 0
        self.seq = 0
        self.usage = {}
        self.usage_at = 0
        self.state = 'idle'
        self.completed_until = 0
        self.expression=''; self.expression_until=0
        self.awaiting_execution = None
        self.history = ['Bridge 已启动，等待会话事件']
        self.account_binding = None
        self.reset_offer = None
        self.reset_busy = False
        self.reset_status = ''
        self.transport = 'usb'
        self.usage_status = '正在读取账户'
        self.active_session = None
        self.request = None
        self.receipt = ''
        self.notice = None
        self.firmware = ''
        self.readonly_notices = False
        self.prehook_review = False
        self.battery = None
        self.hook_count = 0
        self.last_hook = 0
        self.event_counts = {}
        self.tool_counts = {}
        self.audio = {}
        self.native_session = None
        self.native_connected = False
        self.native_error = ''
        self.native_awaiting = None
        self.hook_pending = []
        self.hook_results = {}
        self.desktop_relays = {}
        self.input_notices = []
        self.desktop_mode = False
        self.review_protocol = 0
        self.last_device_decision = None

    def desktop_session(self,session):
        now=time.monotonic()
        return bool(session) and any(now-r['at']<8 and session in r['sessions'] for r in self.desktop_relays.values())

    def desktop_event(self,event):
        relay=event.get('relay');sessions=event.get('sessions');kind=event.get('kind')
        if not isinstance(relay,str) or len(relay)>64 or not isinstance(sessions,list) or len(sessions)>256 or any(not isinstance(v,str) or len(v)>128 for v in sessions):return {}
        with self.lock:
            if kind=='disconnected':
                self.desktop_relays.pop(relay,None)
                for pending in self.hook_pending:
                    if pending.get('relay')==relay:pending['cancelled']=True
            else:
                if relay not in self.desktop_relays and len(self.desktop_relays)>=16:return {}
                self.desktop_relays[relay]={'at':time.monotonic(),'sessions':set(sessions)}
            thread=event.get('thread')
            if thread not in sessions:return {}
            if kind=='turn/started':
                self.active_session=thread;self.set_state('working')
            elif kind=='turn/completed' and thread==self.active_session:
                status=event.get('status')
                if status in ('completed','failed','interrupted'):
                    self.set_state({'completed':'completed','failed':'failed','interrupted':'idle'}[status])
                    self.receipt={'completed':'本轮响应已结束','failed':'任务失败 · 请在 Mac 查看','interrupted':'操作已中断'}[status]
                    self.history.insert(0,self.receipt);self.history=self.history[:20]
        return {}

    def desktop_request(self,event,alive=lambda:True):
        from native_approvals import permission_display
        method=event.get('method');params=event.get('params');relay=event.get('relay')
        if method not in ('item/permissions/requestApproval','item/commandExecution/requestApproval','item/fileChange/requestApproval') or not isinstance(params,dict) or type(event.get('native_id')) not in (str,int):return {}
        thread=params.get('threadId');turn=params.get('turnId');item=params.get('itemId');started=params.get('startedAtMs')
        if not all(isinstance(v,str) and v for v in (thread,turn,item)) or type(started) not in (int,float):return {}
        if started>time.time()*1000+5000:return {}
        timeout=600-max(0,time.time()-started/1000)
        with self.lock:
            registered=self.desktop_relays.get(relay)
            if timeout<=0 or not registered or time.monotonic()-registered['at']>=8 or thread not in registered['sessions']:return {}
        if method=='item/permissions/requestApproval':
            command,project,scope,can_allow,grant=permission_display(params)
            allow={'permissions':grant,'scope':'turn'};deny={'permissions':{},'scope':'turn'}
        else:
            view=hook_display({'tool_name':'Bash','cwd':params.get('cwd'),
                'tool_input':{'command':params.get('command'),'sandbox_permissions':'require_escalated'}}) if method=='item/commandExecution/requestApproval' else {}
            can_allow=bool(view.get('can_allow')) and params.get('environmentId') is None and not params.get('networkApprovalContext') and params.get('kind','command')=='command'
            if params.get('additionalPermissions') is not None:can_allow=False
            available=params.get('availableDecisions')
            if available is not None and (not isinstance(available,list) or 'accept' not in available):can_allow=False
            command=view.get('command','文件修改 · 请在 Mac 查看');project=view.get('project','')
            scope=view.get('scope','修改内容请在 Mac 审阅')
            allow={'decision':'accept'};deny={'decision':'decline'}
        normalized={'hook_event_name':'DesktopApproval','session_id':thread,'turn_id':turn,
            'tool_use_id':relay+':'+json.dumps(event['native_id']),'tool_name':method,
            'tool_input':params}
        view={'command':command.replace('CLI','Mac'),'project':project,'scope':scope.replace('CLI','Mac'),
            'can_allow':can_allow,'can_deny':True,'allow_result':allow,'deny_result':deny,
            'relay':relay,'native_item':item,'native_method':method}
        # Old firmware keeps its bounded, single-screen policy. Only an explicit
        # capability handshake enables full, paged review and long approvals.
        if self.review_protocol == 1:
            view.update(native_view(method,params))
        return self.wait_hook(normalized,view,'desktop',timeout,alive)

    def observe_user_input(self,event):
        name=str(event.get('tool_name','')).rsplit('.',1)[-1].rsplit('__',1)[-1]
        if event.get('hook_event_name')!='PreToolUse' or name not in ('request_user_input_async','request_user_input'):return
        args=event.get('tool_input');questions=args.get('questions') if isinstance(args,dict) else None
        if not isinstance(questions,list):return
        texts=[]
        for question in questions:
            if not isinstance(question,dict):continue
            value=question.get('title') or question.get('question')
            if isinstance(value,str) and value.strip():texts.append(value.strip())
        if not texts:return
        session=event.get('session_id');call=event.get('tool_use_id')
        if call and any(n.get('tool_use_id')==call and n.get('session')==session for n in self.input_notices):return
        self.input_notices.append({'id':str(uuid.uuid4()),'session':session,'tool_use_id':call,
            'turn':event.get('turn_id'),'deadline':time.monotonic()+110,
            'command':'等待你回复','project':'\n'.join(texts),'scope':'请在 Mac 查看完整问题并回复',
            'digest':hashlib.sha256(json.dumps(event,sort_keys=True).encode()).hexdigest(),
            'request_kind':'user_input','can_allow':False,'can_deny':False})
        self.input_notices=self.input_notices[-8:]
        if self.review_protocol==1:
            self.input_notices[-1].update(review_pages=review_pages('\n'.join(texts)),
                review_index=0,review_furthest=0,review_delivered=-1)
        self.history.insert(0,'需要你操作或回复');self.history=self.history[:20]

    def set_state(self, state):
        """Completion is a short presentation state, never a delayed callback."""
        if state == 'completed':
            if self.state != 'completed' or not self.completed_until:
                self.completed_until = time.monotonic() + 3
        else:
            self.completed_until = 0
        self.state = state

    def note_hook(self, event):
        if not self.hook_count:
            print('Codex 会话事件已接入：'+str(event.get('hook_event_name','事件')),flush=True)
        self.hook_count += 1
        self.last_hook = time.monotonic()
        name = str(event.get('hook_event_name',''))[:40]
        if name not in self.event_counts and len(self.event_counts) >= 16:name='other'
        self.event_counts[name] = self.event_counts.get(name,0)+1
        if name in ('PreToolUse','PostToolUse','PermissionRequest'):
            tool = str(event.get('tool_name',''))[:100]
            if tool not in self.tool_counts and len(self.tool_counts) >= 32:tool='other'
            self.tool_counts[tool] = self.tool_counts.get(tool,0)+1

    def status(self):
        with self.lock:
            return {'online':self.online(),'transport':self.transport,'firmware':self.firmware,'battery':self.battery,
                    'bridge_revision':'0.2.4-app-relay-preview-human1',
                    'review_protocol':self.review_protocol,
                    'review_format':'中文说明',
                    'last_device_decision':self.last_device_decision,
                    'hook_count':self.hook_count,'hook_age':round(time.monotonic()-self.last_hook,1) if self.last_hook else None,
                    'permission_pending':bool(self.request),'directory_notice_pending':bool(self.notice),
                    'permission_notice_pending':bool(self.notice),'notification_version':3,
                    'hook_pending':len(self.hook_pending),'completion_hold_seconds':3,
                    'approval_capabilities':{'permission_hook':'allow_deny',
                        'builtin_permission_pre_hook':'continue_on_mac_or_deny' if self.prehook_review else 'notify_only'},
                    'desktop':{'connected':any(time.monotonic()-r['at']<8 for r in self.desktop_relays.values()),
                        'session_count':len({s for r in self.desktop_relays.values() if time.monotonic()-r['at']<8 for s in r['sessions']})},
                    'input_notice_count':len(self.input_notices),
                    'event_counts':dict(self.event_counts),'tool_counts':dict(self.tool_counts),'audio':dict(self.audio),
                    'native':{'thread':self.native_session,'connected':self.native_connected,'error':self.native_error}}

    def observe_permission_request(self, event):
        if (self.native_session and event.get('session_id')==self.native_session) or self.desktop_session(event.get('session_id')):return
        if not permission_tool(event):
            return
        if event.get('hook_event_name') == 'PostToolUse':
            if self.notice and event.get('session_id') == self.notice['session'] and event.get('tool_use_id') == self.notice['tool_use_id']:
                self.notice = None
                self.receipt = '权限请求已返回，结果以 Mac 为准'
            return
        summary=permission_summary(event)
        if summary is None:return
        # PreToolUse only observes this built-in tool. Returning Hook "allow"
        # cannot grant its requested network/filesystem permissions. Native UI decides.
        key=(event.get('session_id'),event.get('tool_use_id'))
        if self.notice and key==(self.notice['session'],self.notice['tool_use_id']):return
        heading,details=summary
        self.notice={'id':str(uuid.uuid4()),'session':key[0],'tool_use_id':key[1],
                     'turn':event.get('turn_id'),
                     'deadline':time.monotonic()+110,'command':heading+' · 在 Mac 确认',
                     'project':details,'scope':'详情与授权范围请在 Mac 查看',
                     'digest':hashlib.sha256(json.dumps(event,sort_keys=True).encode()).hexdigest()}
        print('检测到'+heading+'：设备提醒，授权在 Mac 完成。',flush=True)

    def online(self):
        return bool(self.boot) and time.monotonic() - self.last_seen < 5

    def event(self, event):
        with self.lock:
            if self.native_session and event.get('session_id')!=self.native_session:return {}
            self.note_hook(event)
            name = event.get('hook_event_name')
            self.observe_user_input(event)
            if name=='UserPromptSubmit':
                self.input_notices=[n for n in self.input_notices if n['session']!=event.get('session_id')]
            if name in ('PreToolUse','PostToolUse'):self.observe_permission_request(event)
            if name in ('Stop','Interrupt','SessionEnd') and self.notice and event.get('session_id')==self.notice['session'] and (name=='SessionEnd' or not event.get('turn_id') or self.notice.get('turn')==event.get('turn_id')):
                self.notice=None
            labels={'UserPromptSubmit':'开始处理新请求','PreToolUse':'正在调用工具','PostToolUse':'工具已返回','PermissionRequest':'等待权限确认','Stop':'本轮响应已结束','Interrupt':'操作已中断','SessionEnd':'会话已结束'}
            self.history.insert(0, labels.get(name,str(name or '事件')))
            self.history = self.history[:20]
            session = event.get('session_id')
            if name in ('Stop','Interrupt','SessionEnd'):
                for pending in self.hook_pending:
                    if pending['session']==session and (name=='SessionEnd' or not event.get('turn_id') or pending.get('turn')==event.get('turn_id')):
                        pending['cancelled']=True
            pending_native=self.native_awaiting
            if name=='PostToolUse' and pending_native and time.monotonic()<pending_native['until'] and session==pending_native['session'] and event.get('tool_use_id')==pending_native['item'] and event.get('turn_id')==pending_native['turn']:
                outcome=event.get('permission_outcome')
                if outcome in ('granted','denied','partial'):
                    self.native_awaiting=None
                    self.set_state('denied' if outcome=='denied' else 'working')
                    self.expression='delight' if outcome=='granted' else 'crying' if outcome=='denied' else ''
                    self.expression_until=time.monotonic()+(1.2 if outcome=='granted' else 2.5)
                    self.receipt='权限已授予' if outcome=='granted' else '权限未授予' if outcome=='denied' else '仅部分权限授予 · 请在 CLI 查看'
                    return {}
            if name in ('UserPromptSubmit', 'PreToolUse'):
                self.set_state('working')
                self.active_session = session
            elif session == self.active_session and name == 'Stop' and not self.native_session and not self.desktop_session(session):
                self.set_state('completed')
                self.receipt = '本轮响应已结束'
            elif session == self.active_session and name == 'Interrupt':
                self.set_state('idle')
                if self.request:
                    self.request['cancelled'] = True
            elif session == self.active_session and name == 'SessionEnd':
                self.set_state('idle')
                if self.request:
                    self.request['cancelled'] = True
            # A failed shell command is not necessarily a failed Codex turn.
            # PostToolUse is execution evidence, never a synthetic permission ack.
            elif name == 'PostToolUse':
                self.receipt = 'Tool returned on Mac'
                pending = self.awaiting_execution
                digest = hashlib.sha256(json.dumps(event.get('tool_input'), sort_keys=True).encode()).hexdigest()
                if pending and time.monotonic() < pending['until'] and session == pending['session'] and event.get('tool_name') == pending['tool'] and digest == pending['digest']:
                    self.set_state('working')
                    self.expression = 'delight'; self.expression_until = time.monotonic() + 1.2
                    self.receipt = '已观察到该命令执行返回'
                    self.awaiting_execution = None
            return {}

    def handle_hook(self,event,alive=lambda:True):
        if event.get('hook_event_name') in ('PreToolUse','PermissionRequest') and event.get('tool_use_id'):
            digest=hashlib.sha256(json.dumps(event,sort_keys=True).encode()).hexdigest()
            with self.lock:
                cached=self.hook_results.get(digest)
                if cached and cached[0]>time.monotonic():return cached[1]
        if event.get('hook_event_name')=='PermissionRequest':return self.permission(event,alive=alive)
        if event.get('hook_event_name')=='PreToolUse' and permission_tool(event) and event.get('passport_hook_version')==3:
            return self.pre_permission(event,alive=alive)
        return self.event(event)

    def pre_permission(self,event,timeout=110,alive=lambda:True):
        # This blocks the *tool invocation* before the native grant dialog.
        # It cannot grant filesystem/network permissions. Returning {} hands
        # off to the Mac immediately when no device is available.
        self.event(event)
        with self.lock:
            summary=permission_summary(event)
            if not summary or self.native_session or self.desktop_session(event.get('session_id')) or not self.prehook_review:return {}
            heading,details=summary
            if self.notice and self.notice['session']==event.get('session_id') and self.notice['tool_use_id']==event.get('tool_use_id'):
                self.notice=None
        view={'command':heading,'project':details,
              'scope':'批准在 Mac · 下键拒绝','can_allow':True,'can_deny':True,'action_mode':'mac_confirm'}
        return self.wait_hook(event,view,'prehook',timeout,alive)

    def permission(self, event, timeout=110,alive=lambda:True):
        with self.lock:
            if self.native_session:return {} # Native App Server owns CLI approvals in this mode.
            self.note_hook(event)
        view=hook_display(event)
        if self.review_protocol==1:
            # This is the official PermissionRequest hook, not PreToolUse.
            # Its allow applies to this invocation only; show the full input.
            view={'command':'操作审批','project':'','scope':'仅本次操作 · 不记住批准',
                  'can_allow':True,'can_deny':True,
                  'review_pages':review_pages(hook_text(event))}
        return self.wait_hook(event,view,'hook',timeout,alive)

    def wait_hook(self,event,view,source,timeout,alive):
        digest=hashlib.sha256(json.dumps(event,sort_keys=True).encode()).hexdigest()
        with self.lock:
            if not self.online():return {}
            identifiable=isinstance(event.get('tool_use_id'),str) and bool(event['tool_use_id'])
            self.hook_results={k:v for k,v in self.hook_results.items() if v[0]>time.monotonic()}
            if identifiable and digest in self.hook_results:return self.hook_results[digest][1]
            req=next((r for r in self.hook_pending if identifiable and r['digest']==digest and not r['cancelled']),None)
            if req is None:
                if len(self.hook_pending)>=8:return {}
                req=dict(view,id=str(uuid.uuid4()),deadline=time.monotonic()+timeout,digest=digest,
                         choice=None,cancelled=False,boot=self.boot,session=event.get('session_id'),
                         turn=event.get('turn_id'),source=source,result=None,waiters=0)
                if 'review_pages' in req:
                    req.update(review_index=0,review_furthest=0,review_delivered=-1)
                self.hook_pending.append(req)
            req['waiters']+=1
        try:
            while time.monotonic() < req['deadline']:
                if not alive():return {}
                with self.lock:
                    if req['result'] is not None:return req['result']
                    if req['cancelled'] or not self.online() or self.boot != req['boot']:
                        return {}
                    if self.request is None and self.hook_pending and self.hook_pending[0] is req:
                        self.request=req
                    if req['choice'] in ('allow','deny'):
                        if source=='prehook' and req['choice']=='allow':
                            # Continue the original invocation; the Mac still
                            # asks for the actual grant. Never return Hook allow.
                            self.set_state('working');self.receipt='请在 Mac 确认权限'
                            self.notice=dict(req,can_allow=False,can_deny=False,command=req['command']+' · 在 Mac 确认',
                                             tool_use_id=event.get('tool_use_id'),action_mode='')
                            self.expression='';req['result']={}
                            return {}
                        self.receipt = '已向 Codex 提交' + ('批准' if req['choice']=='allow' else '拒绝')
                        self.set_state('approval_sent' if req['choice']=='allow' else 'denied')
                        self.expression='' if req['choice']=='allow' else 'crying'
                        self.expression_until=time.monotonic()+2.5
                        if req['choice']=='allow':
                            self.awaiting_execution={'session':req['session'],'tool':event.get('tool_name'),'digest':hashlib.sha256(json.dumps(event.get('tool_input'),sort_keys=True).encode()).hexdigest(),'until':time.monotonic()+120}
                        if source=='desktop':
                            if req['choice']=='allow' and req.get('native_method')=='item/permissions/requestApproval':
                                self.native_awaiting={'session':req['session'],'turn':req['turn'],
                                    'item':req['native_item'],'until':time.monotonic()+120}
                            req['result']={'type':'desktop_decision','result':req['allow_result'] if req['choice']=='allow' else req['deny_result']}
                        elif source=='prehook':
                            req['result']={'hookSpecificOutput':{'hookEventName':'PreToolUse',
                                'permissionDecision':'deny','permissionDecisionReason':'用户在 AI Passport 拒绝本次权限请求'}}
                        else:
                            req['result']={'hookSpecificOutput': {'hookEventName': 'PermissionRequest',
                                'decision': {'behavior': req['choice']}}}
                        return req['result']
                time.sleep(.05)
            return {}
        finally:
            with self.lock:
                req['waiters']-=1
                # Matching hooks run concurrently. A short-lived duplicate
                # must not cancel another still-connected hook's review.
                if req['waiters']==0:
                    if req['result'] is None:req['result']={}
                    if identifiable and req['choice'] is not None and not req['cancelled']:
                        if len(self.hook_results)>=64:self.hook_results.pop(next(iter(self.hook_results)))
                        self.hook_results[digest]=(time.monotonic()+120,req['result'])
                    if self.request is req:self.request=None
                    if req in self.hook_pending:self.hook_pending.remove(req)

    def decision(self, message):
        with self.lock:
            req = self.request
            if not req or not self.online() or req['cancelled'] or time.monotonic() >= req['deadline']:
                return False
            if any(message.get(k) != v for k, v in (
                ('boot', req['boot']), ('epoch', self.epoch), ('id', req['id']), ('digest', req['digest']))):
                return False
            if 'review_pages' in req:
                final=len(req['review_pages'])
                if (self.review_protocol!=1 or req.get('review_index')!=final or
                    req.get('review_delivered')!=final or message.get('review_page')!=final):
                    return False
            if message.get('choice') not in ('allow','deny') or (message.get('choice')=='allow' and not req['can_allow']) or (message.get('choice')=='deny' and not req.get('can_deny',True)) or req['choice'] is not None:
                return False
            req['choice'] = message['choice']
            self.last_device_decision={'id':req['id'],'source':req['source'],
                'choice':message['choice'],'at':int(time.time()),
                'review_page':message.get('review_page')}
            return True

    def review_page(self,message):
        """A bound request can move one page at a time, or jump back to start."""
        with self.lock:
            req=self.request
            if not req and not self.notice and self.input_notices:
                req=self.input_notices[0]
            if not req or 'review_pages' not in req or self.review_protocol!=1:return False
            if req.get('cancelled') or req.get('choice') is not None or not self.online() or time.monotonic()>=req['deadline']:return False
            if any(message.get(k)!=v for k,v in (('boot',req.get('boot',self.boot)),('epoch',self.epoch),('id',req['id']),('digest',req['digest']))):return False
            index=message.get('review_page');current=req['review_index']
            if type(index) is not int or not 0<=index<=len(req['review_pages']):return False
            if index not in (0,current,current-1,current+1) or index>req['review_furthest']+1:return False
            # Do not move past a page that was never sent to the device.
            if index>current and req['review_delivered']!=current:return False
            req['review_index']=index;req['review_furthest']=max(req['review_furthest'],index)
            return True

    def add_review(self,data,req):
        if 'review_pages' not in req:return
        index=req['review_index'];total=len(req['review_pages'])
        req['review_delivered']=index
        data.update(review_protocol=1,review_page=index,review_total=total,
                    review_text=req['review_pages'][index] if index<total else '',
                    can_allow=req.get('can_allow',False) and index==total,
                    can_deny=req.get('can_deny',True) and index==total)

    def snapshot(self):
        with self.lock:
            if self.state == 'completed' and self.completed_until and time.monotonic() >= self.completed_until:
                self.set_state('idle')
                if self.receipt == '本轮响应已结束':self.receipt = ''
            if self.notice and time.monotonic()>=self.notice['deadline']:self.notice=None
            self.input_notices=[n for n in self.input_notices if time.monotonic()<n['deadline']]
            self.seq += 1
            usage = self.usage if time.monotonic()-self.usage_at < 120 else {}
            # Preserve all buckets in account.py; device currently shows codex only.
            limits = [w for w in usage.get('limits', []) if w['bucket'] == 'codex']
            first = next((w for w in limits if w['role'] == 'primary'), {})
            second = next((w for w in limits if w['role'] == 'secondary'), {})
            state = 'exhausted' if usage.get('ordinaryUsageAllowed') is False else self.state
            data = {'type': 'snapshot', 'boot': self.boot, 'epoch': self.epoch, 'seq': self.seq,
                    'utc': int(time.time()), 'utc_offset': int(datetime.datetime.now().astimezone().utcoffset().total_seconds()), 'state': state,
                    'primary': first.get('remaining'), 'secondary': second.get('remaining'),
                    'primary_mins': first.get('minutes'), 'secondary_mins': second.get('minutes'),
                    'primary_reset': first.get('resets'), 'secondary_reset': second.get('resets'),
                    'resets': usage.get('resets'), 'receipt': self.receipt, 'history':self.history[:8],
                    'usage_status':self.usage_status, 'transport':self.transport, 'reset_status':self.reset_status,
                    'reset_id':self.offer_reset(usage), 'face':self.expression if time.monotonic()<self.expression_until else '',
                    'hook_status':(('App 实体审批已接入' if any(time.monotonic()-r['at']<8 and r['sessions'] for r in self.desktop_relays.values()) else 'App 已连接 · 等待会话' if any(time.monotonic()-r['at']<8 for r in self.desktop_relays.values()) else 'App 审批尚未连接') if self.desktop_mode else
                                  ('CLI 审批已接入' if self.native_connected else 'CLI 审批连接失败' if self.native_error else 'CLI 审批连接中') if self.native_session else
                                   ('已收到事件 · '+str(int(time.monotonic()-self.last_hook))+'秒前') if self.hook_count else '未收到事件，请检查 Hooks')}
            req = self.request
            if req and not req['cancelled']:
                # Only excerpts, explicitly non-approvable. No raw Hook payload/secrets.
                data.update(req_id=req['id'], digest=req['digest'],
                            ttl=max(0, min(120,int(req['deadline']-time.monotonic()))),
                            command=excerpt(req['command'],150),
                            project=excerpt(req['project'],90), scope=excerpt(req['scope'],120), can_allow=req['can_allow'],can_deny=req.get('can_deny',True),
                            action_mode=req.get('action_mode',''))
                self.add_review(data,req)
            elif self.notice and self.readonly_notices:
                n=self.notice
                data.update(req_id=n['id'],digest=n['digest'],ttl=max(0,int(n['deadline']-time.monotonic())),
                            command=excerpt(n['command'],150),project=excerpt(n['project'],90),scope=excerpt(n['scope'],120),
                            can_allow=False,can_deny=False)
            elif self.input_notices and self.readonly_notices:
                n=self.input_notices[0]
                data.update(req_id=n['id'],digest=n['digest'],ttl=max(0,int(n['deadline']-time.monotonic())),
                    command=n['command'],project=excerpt(n['project'],90),scope=n['scope'],
                    request_kind='user_input',can_allow=False,can_deny=False)
                self.add_review(data,n)
            return data

    def offer_reset(self, usage):
        if not self.account_binding or not self.online() or self.request or self.notice or not usage.get('resets') or self.reset_busy:
            return ''
        if not self.reset_offer or self.reset_offer['binding']!=self.account_binding or self.reset_offer['boot']!=self.boot or time.monotonic()>self.reset_offer['expires']:
            journal=ROOT/'private/reset-journal.json'
            old=json.loads(journal.read_text()) if journal.exists() else {}
            operation=old.get('id') if old.get('status') in ('pending','uncertain') and old.get('binding')==self.account_binding else str(uuid.uuid4())
            self.reset_offer={'id':operation,'boot':self.boot,'binding':self.account_binding,'expires':time.monotonic()+300}
        return self.reset_offer['id']

    def reset_request(self, message):
        with self.lock:
            offer=self.reset_offer
            if not offer or self.reset_busy or not self.online() or self.request or time.monotonic()>offer['expires']:return False
            if message.get('boot')!=offer['boot'] or message.get('epoch')!=self.epoch or message.get('id')!=offer['id']:return False
            self.reset_busy=True; self.reset_status='正在请求重置'; offer=dict(offer)
        def consume():
            client=None; journal=ROOT/'private/reset-journal.json'
            try:
                client=AccountClient(); usage=client.read()
                if client.account_binding!=offer['binding']:raise RuntimeError('账户已变更')
                if not usage.get('resets'):raise RuntimeError('没有可用重置')
                journal.parent.mkdir(exist_ok=True)
                save_journal(journal,{'id':offer['id'],'binding':offer['binding'],'status':'pending'})
                outcome=client.consume_once(offer['id']).get('outcome')
                labels={'reset':'重置成功','alreadyRedeemed':'已完成该次重置','nothingToReset':'当前无需重置','noCredit':'没有可用重置'}
                if outcome not in labels:raise RuntimeError('未知结果')
                with self.lock:
                    self.reset_status=labels[outcome]; self.reset_offer=None
                    self.history.insert(0,self.reset_status)
                save_journal(journal,{'id':offer['id'],'binding':offer['binding'],'status':'done','outcome':outcome})
                updated=client.read()
                with self.lock:self.usage=updated; self.usage_at=time.monotonic()
            except Exception:
                with self.lock:self.reset_status='结果未确认，可重试同一次'
            finally:
                if client:client.close()
                with self.lock:self.reset_busy=False
        threading.Thread(target=consume,daemon=True).start(); return True

    def device_message(self,message,transport):
        with self.lock:
            if message.get('type')=='hello' and isinstance(message.get('boot'),str):
                if not self.online() or self.boot!=message['boot']:
                    print('设备已握手：'+('Wi-Fi 加密连接' if transport=='wifi' else 'USB 连接')+'；固件 '+str(message.get('firmware','未知'))+'；空闲堆 '+str(message.get('free_heap','—'))+' / 最大连续块 '+str(message.get('largest_heap','—')),flush=True)
                if self.boot!=message['boot']:
                    if self.request:self.request['cancelled']=True
                    for pending in self.hook_pending:pending['cancelled']=True
                    self.hook_results.clear()
                    self.notice=None
                self.boot=message['boot']; self.last_seen=time.monotonic(); self.transport=transport
                self.firmware=str(message.get('firmware',''))
                self.readonly_notices=message.get('readonly_notices') is True
                self.prehook_review=message.get('prehook_review') is True
                self.review_protocol=1 if message.get('review_protocol')==1 else 0
                value=message.get('battery')
                self.battery=value if type(value) is int and 0<=value<=100 else None
                self.audio={key:message[key] for key in ('audio_state','audio_error','audio_samples','audio_played','sound_enabled','sound_volume','audio_start_delay_ms','audio_max_feed_gap_ms')
                            if key in message and isinstance(message[key],(str,int,bool))}
            elif message.get('type')=='decision':self.decision(message)
            elif message.get('type')=='review_page':self.review_page(message)
            elif message.get('type')=='dismiss':
                if message.get('boot')==self.boot and message.get('epoch')==self.epoch:
                    self.input_notices=[n for n in self.input_notices if not (n['id']==message.get('id') and n['digest']==message.get('digest'))]
            elif message.get('type')=='reset':self.reset_request(message)


def save_journal(path, value):
    temporary=path.with_suffix('.tmp')
    with temporary.open('w') as file:
        json.dump(value,file); file.flush(); os.fsync(file.fileno())
    os.replace(temporary,path)


def project_label(cwd):
    if not isinstance(cwd,str) or not cwd.isascii() or any(ord(c)<32 for c in cwd):return None
    if len(cwd)<=72:return cwd
    # The device may show the project name (as specified), instead of a clipped path.
    parts=Path(cwd).parts
    label='/'.join(parts[-2:])
    return 'Project: '+label if len(label)<=63 else None


def review_policy(event):
    """Only complete, bounded ordinary commands; complex/high-risk requests stay native."""
    view=hook_display(event)
    return view['can_allow'],view['scope']


def serve(port,native_socket=None,thread_id=None,desktop=False):
    import serial
    os.umask(0o077)
    lease = acquire_endpoint()
    broker = Broker()
    broker.native_session=thread_id
    broker.desktop_mode=desktop
    stopping = threading.Event()

    class Handler(socketserver.StreamRequestHandler):
        def handle(self):
            self.connection.settimeout(115)
            try:
                line = self.rfile.readline(65537)
                if len(line) > 65536:
                    return
                event = json.loads(line)
                if event.get('type')=='status':result=broker.status()
                elif event.get('type')=='desktop_request':
                    result=desktop_reply(broker,event,self.connection,self.wfile)
                elif event.get('type')=='desktop_event':result=broker.desktop_event(event)
                else:
                    def alive():
                        readable,_,_=select.select([self.connection],[],[],0)
                        # One request per connection. EOF (including a killed
                        # hook) cancels its hardware prompt immediately.
                        return not readable
                    result=broker.handle_hook(event,alive)
                self.wfile.write(json.dumps(result).encode() + b'\n')
            except (ValueError, OSError):
                pass

    class Server(socketserver.ThreadingUnixStreamServer):
        daemon_threads = True

    server = Server(str(SOCKET), Handler)
    os.chmod(SOCKET, 0o600)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    native=None
    if native_socket:
        from native_approvals import NativeApprovals
        native=NativeApprovals(broker,native_socket,thread_id,review_policy);native.start()

    def account_worker():
        while not stopping.is_set():
            client = None
            try:
                client = AccountClient()
                usage = client.read()
                with broker.lock:
                    broker.usage = usage
                    broker.usage_at = time.monotonic()
                    broker.account_binding=client.account_binding
                    broker.usage_status='额度已同步'
                print('ChatGPT account verified; usage refreshed (no model task).', flush=True)
            except Exception as e:
                print('Account unavailable:', type(e).__name__, flush=True)
                with broker.lock:broker.usage_status='账户暂不可用，正在重试'
            finally:
                if client:
                    client.close()
            stopping.wait(60)

    threading.Thread(target=account_worker, daemon=True).start()
    https=start_https(broker)
    print('桌面 App 实体审批模式：等待启动适配接入实际 App 会话。' if desktop else 'CLI 实体审批模式：原生请求由设备或 CLI 处理。' if native_socket else
          '权限接入 v3：Hook 支持设备审批；原生网络 / 目录请求可在调用前拒绝，批准仍在 Mac。',flush=True)
    print('Bridge 已启动，等待设备连接。Control+C 停止。',flush=True)
    try:
        while True:
            if not port:
                stopping.wait(1); continue
            try:
                with serial.Serial(port, 115200, timeout=.1, write_timeout=1, exclusive=True) as device:
                    print('USB port opened; waiting for firmware hello...', flush=True)
                    buf = b''
                    sent = 0
                    while True:
                        buf += device.read(512)
                        if len(buf) > 8192:
                            buf = b''
                        while b'\n' in buf:
                            line, buf = buf.split(b'\n', 1)
                            if not line.startswith(b'PC1 '):
                                continue
                            try:
                                message = json.loads(line[4:])
                            except ValueError:
                                continue
                            first=not broker.online()
                            broker.device_message(message,'usb')
                            if first and broker.online():print('设备已握手，正在同步数据。',flush=True)
                        if broker.online() and time.monotonic()-sent >= .5:
                            frame = b'PC1 ' + json.dumps(broker.snapshot(), separators=(',', ':')).encode() + b'\n'
                            device.write(frame)
                            sent = time.monotonic()
            except (serial.SerialException, OSError) as error:
                print('USB unavailable:', str(error), flush=True)
                with broker.lock:
                    broker.last_seen = 0
                    if broker.request:
                        broker.request['cancelled'] = True
                time.sleep(2)
    finally:
        stopping.set()
        if native:native.close()
        if https:https.shutdown(); https.server_close()
        server.shutdown()
        server.server_close()
        SOCKET.unlink(missing_ok=True)
        lease.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port',default='')
    parser.add_argument('--native-socket')
    parser.add_argument('--thread')
    parser.add_argument('--desktop',action='store_true')
    args = parser.parse_args()
    if bool(args.native_socket)!=bool(args.thread):parser.error('--native-socket and --thread are required together')
    if args.desktop and args.native_socket:parser.error('Desktop and CLI ownership modes cannot be combined')
    try:
        serve(args.port,args.native_socket,args.thread,args.desktop)
    except KeyboardInterrupt:
        pass
