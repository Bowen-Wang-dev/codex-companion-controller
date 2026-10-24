import copy
import json
from pathlib import Path
import sys
import socket
import threading
import time
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bridge'))
from approval_review import native_view,native_text,hook_text,pages,visible_text,COLUMNS,ROWS,PAGE_BYTES
from service import Broker,desktop_reply


def params():
    return {'threadId':'thread','turnId':'turn','itemId':'item','environmentId':None,
        'startedAtMs':int(time.time()*1000),'cwd':'/Users/developer/很长的项目名称',
        'reason':'只申请测试权限，不会创建或修改文件。'*8,
        'permissions':{'network':{'enabled':True},'fileSystem':{'read':None,
            'write':['/Users/developer/Documents/'+'long-folder-name/'*14+'folder',
                     '/Users/developer/另一个测试目录']}}}


class LayoutTests(unittest.TestCase):
    def test_normal_permission_display_is_chinese_not_a_json_dump(self):
        p=params();body=native_text('item/permissions/requestApproval',p,'仅本轮有效')
        for text in ('网络：申请联网','申请写入(2项)','工作目录：','申请原因：','授权有效期：'):
            self.assertIn(text,body)
        for text in ('{','}','[',']','threadId','turnId','startedAtMs','fileSystem','null'):
            self.assertNotIn(text,body)
        self.assertIn(p['reason'],body)
        for path in p['permissions']['fileSystem']['write']:self.assertIn(path,body)

    def test_exact_command_is_preserved_even_if_it_contains_json(self):
        p=params();p['command']='printf \'{"keys":[1,2]}\''
        body=native_text('item/commandExecution/requestApproval',p,'仅本次操作')
        self.assertIn(p['command'],body)
        self.assertIn('请求执行以下命令',body)

    def test_path_rules_and_unknown_fields_remain_visible_without_structural_braces(self):
        p=params();p['permissions']['fileSystem']={'entries':[
            {'access':'read','path':{'type':'path','path':'/path/full.txt'}},
            {'access':'deny','path':{'type':'glob_pattern','pattern':'/path/private/*'}}],
            'globScanMaxDepth':4}
        p['newFutureField']={'networkHost':'example.test','flag':True}
        body=native_text('item/permissions/requestApproval',p,'仅本轮')
        for text in ('申请读取：/path/full.txt','拒绝访问匹配路径：/path/private/*','规则扫描深度：4',
                     'newFutureField','example.test','flag：是'):
            self.assertIn(text,body)
        self.assertNotIn('{',body)
        p['command']='pwd';p['permissions']={'fileSystem':{'write':['/future-extra-path']}}
        self.assertIn('/future-extra-path',native_text('item/commandExecution/requestApproval',p,'仅本次'))

    def test_permission_hook_uses_human_labels_and_hides_routing_fields(self):
        body=hook_text({'tool_name':'Bash','tool_input':{'command':'cat full.txt','justification':'查看文件'},
                        'session_id':'private-id','cwd':'/project'})
        self.assertIn('执行命令：\ncat full.txt',body);self.assertIn('申请原因：\n查看文件',body)
        self.assertNotIn('private-id',body);self.assertNotIn('{',body)

    def test_top_level_null_permissions_are_not_sent_as_grants(self):
        p=params();p['permissions']['fileSystem']=None
        view=native_view('item/permissions/requestApproval',p)
        self.assertEqual(view['allow_result'],{'permissions':{'network':{'enabled':True}},'scope':'turn'})
    def test_long_exact_request_is_reviewable_and_grant_not_summarized(self):
        original=params();before=copy.deepcopy(original)
        view=native_view('item/permissions/requestApproval',original)
        self.assertTrue(view['can_allow']);self.assertGreater(len(view['review_pages']),3)
        self.assertEqual(view['allow_result'],{'permissions':original['permissions'],'scope':'turn'})
        self.assertEqual(original,before)
        for page in view['review_pages']:
            self.assertLess(len(page.encode()),PAGE_BYTES)
            self.assertLessEqual(len(page.split('\n')),ROWS)
            self.assertTrue(all(len(line)<=COLUMNS for line in page.split('\n')))
        # No ellipsis, deleted path, shortened reason, or altered policy.
        rendered=''.join(''.join(p.split('\n')) for p in view['review_pages'])
        for value in original['permissions']['fileSystem']['write']:
            self.assertIn(visible_text(value),rendered)

    def test_arbitrary_width_wrapping_keeps_each_character(self):
        value=('Wm@中文/[]-=0123456789'*80)+'尾'
        self.assertEqual(''.join(p.replace('\n','') for p in pages(value)),visible_text(value))

    def test_invisible_or_unsupported_characters_are_visible_escapes(self):
        self.assertEqual(visible_text('a\u202eb\x1bc🤔'),'a\\u202eb\\u001bc\\U0001f914')
        self.assertEqual(visible_text('检查脚本'),'检查脚本')

    def test_long_command_no_longer_uses_readonly_command_whitelist(self):
        p=params();p['command']='python3 -c '+repr('print("hello")\n'*40)
        view=native_view('item/commandExecution/requestApproval',p)
        self.assertTrue(view['can_allow']);self.assertEqual(view['allow_result'],{'decision':'accept'})
        p['additionalPermissions']={'unknown_scope':True}
        self.assertFalse(native_view('item/commandExecution/requestApproval',p)['can_allow'])

    def test_missing_file_diff_is_not_mistaken_for_complete_review(self):
        self.assertFalse(native_view('item/fileChange/requestApproval',params())['can_allow'])


class BrokerPagesTests(unittest.TestCase):
    def setUp(self):
        self.b=Broker();self.workers=[];self.results=[]
        self.b.device_message({'type':'hello','boot':'boot','firmware':'0.2.4',
            'review_protocol':1,'readonly_notices':True},'wifi')
        self.b.desktop_event({'relay':'relay','sessions':['thread'],'kind':'heartbeat'})
        self.p=params()
        worker=threading.Thread(target=lambda:self.results.append(self.b.desktop_request({
            'relay':'relay','method':'item/permissions/requestApproval','native_id':'native',
            'params':self.p})),daemon=True)
        self.workers.append(worker);worker.start()
        deadline=time.monotonic()+1
        while self.b.request is None and time.monotonic()<deadline:time.sleep(.005)
        self.assertIsNotNone(self.b.request)

    def tearDown(self):
        self.b.device_message({'type':'hello','boot':'reboot'},'wifi')
        for worker in self.workers:worker.join(timeout=1)

    def message(self,**extra):
        r=self.b.request
        return dict(boot='boot',epoch=self.b.epoch,id=r['id'],digest=r['digest'],**extra)

    def advance(self):
        view=self.b.snapshot()
        self.assertFalse(self.b.decision(self.message(choice='allow',review_page=view['review_total'])))
        for index in range(1,view['review_total']+1):
            self.assertTrue(self.b.review_page(self.message(review_page=index)))
            view=self.b.snapshot()
        return view

    def test_must_read_pages_cannot_skip_or_use_stale_identity(self):
        view=self.b.snapshot();self.assertFalse(view['can_allow']);self.assertFalse(view['can_deny'])
        self.assertFalse(self.b.review_page(self.message(review_page=view['review_total'])))
        self.assertFalse(self.b.review_page(self.message(review_page=True)))
        self.assertFalse(self.b.review_page(dict(self.message(review_page=1),digest='wrong')))
        self.assertTrue(self.b.review_page(self.message(review_page=1)))
        self.assertFalse(self.b.review_page(self.message(review_page=2))) # Not sent page 1 yet.

    def test_final_page_bound_choice_returns_exact_native_grant(self):
        view=self.advance();self.assertTrue(view['can_allow']);self.assertEqual(view['review_text'],'')
        self.assertFalse(self.b.decision(self.message(choice='allow',review_page=0)))
        self.assertTrue(self.b.decision(self.message(choice='allow',review_page=view['review_total'])))
        self.assertEqual(self.b.status()['last_device_decision']['source'],'desktop')
        self.assertEqual(self.b.status()['last_device_decision']['choice'],'allow')
        self.workers[0].join(timeout=1)
        self.assertEqual(self.results,[{'type':'desktop_decision','result':{
            'permissions':self.p['permissions'],'scope':'turn'}}])

    def test_return_to_first_page_relocks_decision_and_reboot_invalidates(self):
        view=self.advance();total=view['review_total']
        self.assertTrue(self.b.review_page(self.message(review_page=0)))
        self.assertFalse(self.b.decision(self.message(choice='allow',review_page=total)))
        self.assertFalse(self.b.snapshot()['can_allow'])
        message=self.message(review_page=1)
        self.b.device_message({'type':'hello','boot':'new-boot','review_protocol':1},'wifi')
        self.assertFalse(self.b.review_page(message))

    def test_snapshot_fits_real_transport_and_only_contains_one_page(self):
        view=self.b.snapshot()
        self.assertLess(len(json.dumps(view,separators=(',',':')).encode()),4096)
        self.assertNotIn('review_pages',view)
        self.assertLess(len(view['review_text'].encode()),PAGE_BYTES)

    def test_long_user_question_can_be_paged_but_not_approved(self):
        self.b.request['cancelled']=True;self.workers[0].join(timeout=1)
        self.b.event({'hook_event_name':'PreToolUse','session_id':'thread','tool_use_id':'question',
            'tool_name':'request_user_input_async','tool_input':{'questions':[{'title':'请检查脚本并回复。'*40}]}})
        view=self.b.snapshot();self.assertEqual(view['request_kind'],'user_input')
        notice=self.b.input_notices[0]
        for index in range(1,view['review_total']+1):
            message={'boot':'boot','epoch':self.b.epoch,'id':notice['id'],'digest':notice['digest'],'review_page':index}
            self.assertTrue(self.b.review_page(message));view=self.b.snapshot()
        self.assertFalse(view['can_allow']);self.assertFalse(view['can_deny'])
        self.assertFalse(self.b.decision(dict(message,choice='allow')))

    def test_final_page_can_deny_and_never_grants_on_invalid_connection(self):
        view=self.advance()
        self.assertTrue(self.b.decision(self.message(choice='deny',review_page=view['review_total'])))
        self.workers[0].join(timeout=1)
        self.assertEqual(self.results,[{'type':'desktop_decision','result':{'permissions':{},'scope':'turn'}}])


class LongReplyTests(unittest.TestCase):
    def test_existing_relay_can_read_one_json_line_across_multiple_idle_timeouts(self):
        release=threading.Event();finished=threading.Event()
        class Stub:
            def desktop_request(self,event,alive):
                while not release.wait(.005):
                    if not alive():return {}
                return {'type':'desktop_decision','result':{'permissions':{},'scope':'turn'}}
        left,right=socket.socketpair()
        def serve():
            with left,left.makefile('wb') as stream:
                result=desktop_reply(Stub(),{},left,stream,interval=.01)
                stream.write(json.dumps(result).encode()+b'\n');stream.flush();finished.set()
        worker=threading.Thread(target=serve,daemon=True);worker.start()
        try:
            right.settimeout(.1)
            # A pre-upgrade relay still has a short per-read timeout. Multiple
            # whitespace chunks remain part of one valid response, not events.
            self.assertEqual(right.recv(1),b' ')
            self.assertEqual(right.recv(1),b' ')
            release.set()
            with right.makefile('rb') as stream:response=json.loads(stream.readline())
            self.assertEqual(response['result']['permissions'],{})
        finally:
            release.set();right.close();worker.join(timeout=1)
        self.assertTrue(finished.is_set())


if __name__=='__main__':unittest.main()
