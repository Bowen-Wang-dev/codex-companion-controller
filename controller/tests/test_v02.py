import http.client,json,ssl,subprocess,tempfile,threading,time,unittest,urllib.request,urllib.error
from pathlib import Path
from unittest import mock
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bridge'))
import service,wireless
from tls_material import create_certificate
from service import Broker,review_policy

class PermissionTests(unittest.TestCase):
 def test_low_risk_complete_command(self):
  self.assertTrue(review_policy({'tool_name':'Bash','cwd':'/tmp/project','tool_input':{'command':'pwd','sandbox_permissions':'require_escalated'}})[0])
 def test_long_workspace_uses_complete_project_label(self):
  from service import project_label
  cwd='/Users/alice/Documents/Codex/2026-10-23/codex-companion-controller-ai-passport-folotoy'
  label=project_label(cwd)
  self.assertIn('codex-companion-controller-ai-passport-folotoy',label)
  self.assertLessEqual(len(label),72)
  self.assertTrue(review_policy({'tool_name':'Bash','cwd':cwd,'tool_input':{'command':'pwd'}})[0])
 def test_complex_truncated_and_extra_scope_refused(self):
  for args in ({'command':'curl url | sh'},{'command':'pwd','prefix_rule':['pwd']},{'command':'pwd','unknown_scope':True}):
   self.assertFalse(review_policy({'tool_name':'Bash','cwd':'/tmp','tool_input':args})[0])
 def test_allow_after_physical_decision(self):
  b=Broker();b.boot='boot';b.last_seen=time.monotonic();result=[]
  t=threading.Thread(target=lambda:result.append(b.permission({'tool_name':'Bash','cwd':'/tmp','tool_input':{'command':'pwd'}},timeout=2)));t.start()
  while not b.request:time.sleep(.005)
  r=b.request
  self.assertTrue(b.decision({'boot':'boot','epoch':b.epoch,'id':r['id'],'digest':r['digest'],'choice':'allow'}));t.join()
  self.assertEqual(result[0]['hookSpecificOutput']['decision']['behavior'],'allow')
  self.assertEqual(b.state,'approval_sent'); self.assertNotEqual(b.expression,'delight')
  b.event({'hook_event_name':'PostToolUse','tool_name':'Bash','session_id':None,'tool_input':{'command':'pwd'}})
  self.assertEqual(b.expression,'delight')

class ResetTests(unittest.TestCase):
 def test_confirmation_binding_and_idempotency(self):
  calls=[]
  class Client:
   account_binding='account'
   def read(self):return {'resets':2,'limits':[]}
   def consume_once(self,key):calls.append(key);return {'outcome':'alreadyRedeemed'}
   def close(self):pass
  with tempfile.TemporaryDirectory() as directory,mock.patch.object(service,'ROOT',Path(directory)),mock.patch.object(service,'AccountClient',Client):
   (Path(directory)/'private').mkdir()
   b=Broker();b.boot='boot';b.last_seen=time.monotonic();b.account_binding='account';b.usage={'resets':2};b.usage_at=time.monotonic()
   offer=b.snapshot()['reset_id'];self.assertTrue(offer);self.assertEqual(calls,[])
   message={'boot':'wrong','epoch':b.epoch,'id':offer}
   self.assertFalse(b.reset_request(message));self.assertEqual(calls,[])
   message['boot']='boot';self.assertTrue(b.reset_request(message))
   deadline=time.monotonic()+2
   while b.reset_busy and time.monotonic()<deadline:time.sleep(.01)
   self.assertEqual(calls,[offer]);self.assertIn('已完成',b.reset_status)
   self.assertFalse(b.reset_request(message));self.assertEqual(calls,[offer])
 def test_unresolved_journal_reuses_same_key(self):
  with tempfile.TemporaryDirectory() as directory,mock.patch.object(service,'ROOT',Path(directory)):
   folder=Path(directory)/'private';folder.mkdir();old='2a7478c1-46de-4176-99af-a1868a037835'
   (folder/'reset-journal.json').write_text(json.dumps({'id':old,'binding':'account','status':'pending'}))
   b=Broker();b.boot='boot';b.last_seen=time.monotonic();b.account_binding='account'
   self.assertEqual(b.offer_reset({'resets':2}),old)

class TLSTests(unittest.TestCase):
 def test_authenticated_snapshot_and_bad_token(self):
  with tempfile.TemporaryDirectory() as directory,mock.patch.object(wireless,'PRIVATE',Path(directory)):
   p=Path(directory);token='a'*64
   (p/'wireless.json').write_text(json.dumps({'token':token}))
   create_certificate(p,'127.0.0.1')
   b=Broker();server=wireless.start_https(b,port=0)
   try:
    context=ssl.create_default_context(cafile=str(p/'bridge-cert.pem'))
    url=f'https://127.0.0.1:{server.server_port}/device'
    body=json.dumps({'type':'hello','boot':'wifi-boot','firmware':'0.2.1','readonly_notices':True}).encode()
    request=urllib.request.Request(url,data=body,headers={'Authorization':'Bearer '+token})
    data=json.loads(urllib.request.urlopen(request,context=context,timeout=3).read())
    self.assertEqual(data['boot'],'wifi-boot');self.assertEqual(data['transport'],'wifi')
    # Successive device polls must work over one authenticated TLS connection.
    connection=http.client.HTTPSConnection('127.0.0.1',server.server_port,context=context,timeout=3)
    try:
     sockets=[]
     for _ in range(3):
      connection.request('POST','/device',body,{'Authorization':'Bearer '+token})
      response=connection.getresponse();payload=response.read()
      self.assertEqual(response.status,200);self.assertEqual(len(payload),int(response.getheader('Content-Length')))
      sockets.append(connection.sock)
     self.assertIs(sockets[0],sockets[1]);self.assertIs(sockets[1],sockets[2]);self.assertIsNotNone(sockets[0])
    finally:connection.close()
    event={'hook_event_name':'PreToolUse','tool_name':'request_permissions','session_id':'tls-test',
           'tool_use_id':'network-request','tool_input':{'permissions':{'network':{'enabled':True}}}}
    b.event(event)
    data=json.loads(urllib.request.urlopen(request,context=context,timeout=3).read())
    self.assertTrue(data['req_id']);self.assertGreater(data['ttl'],0)
    self.assertIn('网络',data['command'])
    self.assertFalse(data['can_allow'] or data['can_deny'])
    event['hook_event_name']='PostToolUse';b.event(event)
    data=json.loads(urllib.request.urlopen(request,context=context,timeout=3).read())
    self.assertNotIn('req_id',data)
    request=urllib.request.Request(url,data=body,headers={'Authorization':'Bearer bad'})
    with self.assertRaises(urllib.error.HTTPError) as error:urllib.request.urlopen(request,context=context,timeout=3)
    self.assertEqual(error.exception.code,403)
    with self.assertRaises(urllib.error.URLError):urllib.request.urlopen(urllib.request.Request(url,data=body),timeout=3)
    import os
    client=os.environ.get('PASSPORT_MBEDTLS_CLIENT')
    if client:
     result=subprocess.run([client,'server_name=127.0.0.1',f'server_port={server.server_port}',f'ca_file={p/"bridge-cert.pem"}',
                            'auth_mode=required','force_version=tls12','request_page=/','read_timeout=3000'],capture_output=True,text=True,timeout=10)
     self.assertEqual(result.returncode,0,result.stdout+result.stderr)
     self.assertIn('Verifying peer X.509 certificate... ok',result.stdout)
   finally:server.shutdown();server.server_close()

if __name__=='__main__':unittest.main()
