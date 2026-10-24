"""Transparent App↔official App Server relay with physical approval arbitration.

Only recognized server-initiated approval messages may receive a hardware reply.
All other protocol lines are forwarded unchanged. No model turns are generated.
"""
import argparse
import json
import os
from pathlib import Path
import queue
import socket
import subprocess
import sys
import threading
import time
import uuid

from ipc_path import check_directory

APPROVALS={'item/permissions/requestApproval','item/commandExecution/requestApproval',
           'item/fileChange/requestApproval'}
MAX_LINE=16*1024*1024


class Arbitration:
    """One response per outstanding server request; serialize both input paths."""
    def __init__(self,write):
        self.lock=threading.RLock();self.write=write;self.pending={};self.resolved=set()

    @staticmethod
    def key(identifier):
        return json.dumps(identifier,ensure_ascii=True,separators=(',',':'))

    def offer(self,message):
        if message.get('method') not in APPROVALS or type(message.get('id')) not in (str,int):return None
        key=self.key(message['id'])
        with self.lock:
            if key in self.pending or len(self.pending)>=32:return None
            self.resolved.discard(key)
            pending={'message':message,'connection':None}
            self.pending[key]=pending
            return pending

    def cancel_connection(self,pending):
        connection=pending.get('connection')
        if connection:
            try:connection.shutdown(socket.SHUT_RDWR)
            except OSError:pass

    def resolve(self,identifier):
        with self.lock:
            key=self.key(identifier);pending=self.pending.pop(key,None)
            if pending:self.cancel_connection(pending)
            if len(self.resolved)>=256:self.resolved.clear()
            self.resolved.add(key)

    def from_app(self,line,message):
        with self.lock:
            if isinstance(message,dict) and 'id' in message and 'method' not in message:
                key=self.key(message['id'])
                if key in self.resolved:return False
                if key in self.pending:self.resolve(message['id'])
            self.write(line)
            return True

    def from_device(self,pending,result):
        message=pending['message'];key=self.key(message['id'])
        if not isinstance(result,dict) or result.get('type')!='desktop_decision':return False
        decision=result.get('result')
        if not valid_response(message,decision):return False
        with self.lock:
            if self.pending.get(key) is not pending:return False
            self.write((json.dumps({'id':message['id'],'result':decision})+'\n').encode())
            self.resolve(message['id'])
            return True

    def close(self):
        with self.lock:
            for pending in self.pending.values():self.cancel_connection(pending)
            self.pending.clear()


def valid_response(message,result):
    if not isinstance(result,dict):return False
    if message.get('method')=='item/permissions/requestApproval':
        if set(result)!={'permissions','scope'} or result['scope']!='turn':return False
        grant=result['permissions'];requested=message.get('params',{}).get('permissions')
        if not isinstance(grant,dict) or not isinstance(requested,dict):return False
        # The Bridge may deny everything or grant only exact, requested fields.
        def subset(value,original):
            if isinstance(value,dict):
                return isinstance(original,dict) and all(key in original and subset(v,original[key]) for key,v in value.items())
            return type(value) is type(original) and value==original
        return subset(grant,requested)
    return set(result)=={'decision'} and result['decision'] in ('accept','decline')


class Relay:
    def __init__(self,child,app_in,app_out):
        self.child=child;self.app_in=app_in;self.app_out=app_out
        self.id=str(uuid.uuid4());self.sessions=set();self.client_calls={}
        self.stopping=threading.Event();self.events=queue.Queue(maxsize=128)
        self.arbiter=Arbitration(self.write_child)

    def write_child(self,line):
        self.child.stdin.write(line);self.child.stdin.flush()

    def event(self,value):
        try:self.events.put_nowait(value)
        except queue.Full:pass

    def ipc(self,value,timeout=1):
        with socket.socket(socket.AF_UNIX) as connection:
            connection.settimeout(timeout);connection.connect(str(check_directory()))
            connection.sendall(json.dumps(value).encode()+b'\n')
            with connection.makefile('rb') as stream:
                return json.loads(stream.readline(65537))

    def event_worker(self):
        while not self.stopping.is_set():
            try:event=self.events.get(timeout=2)
            except queue.Empty:event={'kind':'heartbeat'}
            try:
                with self.arbiter.lock:sessions=sorted(self.sessions)
                self.ipc({'type':'desktop_event','relay':self.id,'sessions':sessions,'approval_receipts':1,**event})
            except (OSError,ValueError):pass

    def review(self,pending):
        message=pending['message'];connection=None
        try:
            with self.arbiter.lock:sessions=sorted(self.sessions)
            self.ipc({'type':'desktop_event','relay':self.id,'sessions':sessions,'approval_receipts':1,'kind':'heartbeat'})
            encoded=json.dumps({'type':'desktop_request','relay':self.id,
                'method':message['method'],'native_id':message['id'],'params':message.get('params')}).encode()+b'\n'
            if len(encoded)>65536:return
            connection=socket.socket(socket.AF_UNIX);connection.settimeout(602)
            connection.connect(str(check_directory()))
            with self.arbiter.lock:
                if self.arbiter.pending.get(self.arbiter.key(message['id'])) is not pending:return
                pending['connection']=connection
            connection.sendall(encoded)
            with connection.makefile('rb') as stream:result=json.loads(stream.readline(65537))
            with self.arbiter.lock:
                if self.arbiter.from_device(pending,result):
                    decision=result['result'];params=message.get('params') or {}
                    allow=bool(decision.get('permissions')) if message['method']=='item/permissions/requestApproval' else decision.get('decision')=='accept'
                    self.event({'kind':'approval/submitted','thread':params.get('threadId'),
                        'turn':params.get('turnId'),'item':params.get('itemId'),
                        'request_id':result.get('request_id'),'choice':'allow' if allow else 'deny'})
        except (OSError,ValueError,TypeError):pass # App's own approval remains available.
        finally:
            if connection:connection.close()

    def app_worker(self):
        try:
            while not self.stopping.is_set():
                line=self.app_in.readline(MAX_LINE+1)
                if not line:break
                if len(line)>MAX_LINE:raise ValueError('Oversized App protocol line')
                try:message=json.loads(line)
                except ValueError:message=None
                with self.arbiter.lock:
                    if isinstance(message,dict) and 'id' in message and message.get('method') in ('thread/start','thread/resume','thread/fork'):
                        if len(self.client_calls)<256:self.client_calls[self.arbiter.key(message['id'])]=message['method']
                    self.arbiter.from_app(line,message)
        except (OSError,ValueError):pass
        finally:
            self.stopping.set();self.arbiter.close()
            try:self.child.stdin.close()
            except OSError:pass

    def server_line(self,line):
        try:message=json.loads(line)
        except ValueError:message=None
        if not isinstance(message,dict):
            self.app_out.write(line);self.app_out.flush();return
        with self.arbiter.lock:
            method=message.get('method');params=message.get('params') or {}
            if 'id' in message and 'method' not in message:
                origin=self.client_calls.pop(self.arbiter.key(message['id']),None)
                if origin:
                    thread=(message.get('result') or {}).get('thread') or {}
                    for key in ('id','sessionId'):
                        if isinstance(thread.get(key),str):self.sessions.add(thread[key])
                    self.event({'kind':'attached'})
            if method=='serverRequest/resolved':self.arbiter.resolve(params.get('requestId'))
            elif method in ('turn/started','turn/completed'):
                thread_id=params.get('threadId')
                if isinstance(thread_id,str):self.sessions.add(thread_id)
                turn=params.get('turn') or {}
                self.event({'kind':method,'thread':thread_id,'turn':turn.get('id'),'status':turn.get('status')})
            if method in APPROVALS and isinstance(params.get('threadId'),str):self.sessions.add(params['threadId'])
            pending=self.arbiter.offer(message)
            # Register before releasing the lock, so an immediate App answer
            # cannot race ahead of the pending entry or create a ghost prompt.
            self.app_out.write(line);self.app_out.flush()
            if pending:threading.Thread(target=self.review,args=(pending,),daemon=True).start()

    def run(self):
        threading.Thread(target=self.event_worker,daemon=True).start()
        threading.Thread(target=self.app_worker,daemon=True).start()
        try:
            while True:
                line=self.child.stdout.readline(MAX_LINE+1)
                if not line:break
                if len(line)>MAX_LINE:raise ValueError('Oversized server protocol line')
                self.server_line(line)
        finally:
            self.stopping.set();self.arbiter.close()
            try:self.ipc({'type':'desktop_event','relay':self.id,'kind':'disconnected','sessions':[]},timeout=.5)
            except (OSError,ValueError):pass


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--real',required=True)
    parser.add_argument('args',nargs=argparse.REMAINDER)
    args=parser.parse_args();command=args.args
    if command[:1]==['--']:command=command[1:]
    real=Path(args.real).resolve(strict=True)
    if not real.is_file() or not os.access(real,os.X_OK):raise ValueError('Official Codex executable missing')
    # Version, login and other CLI utility calls remain exact passthroughs.
    if 'app-server' not in command or any(v in command for v in ('daemon','proxy','generate-ts','generate-json-schema')):
        os.execv(str(real),[str(real),*command])
    if '--listen' in command and command[command.index('--listen')+1]!='stdio://':
        os.execv(str(real),[str(real),*command])
    child=subprocess.Popen([str(real),*command],stdin=subprocess.PIPE,stdout=subprocess.PIPE,
        stderr=sys.stderr.buffer)
    try:Relay(child,sys.stdin.buffer,sys.stdout.buffer).run()
    finally:
        if child.poll() is None:
            child.terminate()
            try:child.wait(timeout=3)
            except subprocess.TimeoutExpired:child.kill();child.wait()
    return child.returncode


if __name__=='__main__':
    try:sys.exit(main())
    except (OSError,ValueError) as error:
        print('Passport App relay: '+str(error),file=sys.stderr);sys.exit(1)
