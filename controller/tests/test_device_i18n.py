"""Installed firmware owns language; localization never changes authorization."""
import contextlib
import copy
import io
import json
import os
import ast
import re
from pathlib import Path
import sys
import threading
import time
import unittest
from unittest import mock

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'bridge'))
from device_i18n import DeviceText,dt,render,localized_join
from approval_review import native_view,hook_text,pages,visible_text,ROWS,COLUMNS,PAGE_BYTES
from service import Broker


def hello(boot='test-boot',**extra):
    return dict(type='hello',boot=boot,firmware='0.2.14',review_protocol=1,
                review_jumps=True,readonly_notices=True,**extra)


class DeviceLanguageTests(unittest.TestCase):
    def test_worst_case_language_hello_fits_bounded_usb_and_network_tx(self):
        source=(ROOT/'firmware/main/main.c').read_text(encoding='utf-8')
        block=source[source.index('static void hello(void)'):source.index('static void action(')]
        keys=set(re.findall(r'cJSON_Add(?:String|Bool|Number|Item)ToObject\(o,"([^"]+)"',block))
        data=dict(type='hello',firmware='0.2.14',assets=True,ui_language_protocol=1,ui_language='zh-CN',
            readonly_notices=True,prehook_review=True,user_input_notices=True,review_protocol=1,review_jumps=True,
            battery=100,audio_state='starting',audio_error=-2147483648,audio_samples=4294967295,
            audio_played=4294967295,audio_start_delay_ms=4294967295,audio_max_feed_gap_ms=4294967295,
            sound_enabled=False,sound_volume=100,net=[2147483647]*4,net_io=[-2147483648,2147483647,2147483647],
            free_heap=4294967295,largest_heap=4294967295)
        self.assertEqual(set(data),keys)
        data['boot']='0123456789abcdef'
        limit=int(re.search(r'#define DEVICE_TX_BYTES (\d+)',(ROOT/'firmware/main/network.h').read_text()).group(1))
        wire=json.dumps(data,separators=(',',':')).encode('utf-8')
        self.assertLess(len(wire),limit)
        self.assertLess(len(b'PC1 '+wire+b'\n'),limit+8)

    def test_all_device_system_literals_have_english_and_c_table_matches(self):
        from device_i18n import _ENGLISH
        for name in ('service','approval_review','hook_policy','native_approvals'):
            for node in ast.walk(ast.parse((ROOT/'bridge'/f'{name}.py').read_text(encoding='utf-8'))):
                if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=='dt' and node.args and isinstance(node.args[0],ast.Constant):
                    key=node.args[0].value
                    self.assertIn(key,_ENGLISH)
                    self.assertFalse(any('\u4e00'<=c<='\u9fff' for c in _ENGLISH[key]),key)
        table=(ROOT/'firmware/main/ui_language.c').read_text(encoding='utf-8')
        pairs=re.findall(r'^ \{("(?:[^"\\]|\\.)*"),("(?:[^"\\]|\\.)*")\},$',table,re.M)
        self.assertEqual(len(pairs),126)
        for zh,en in pairs:self.assertEqual(_ENGLISH[json.loads(zh)],json.loads(en))
    def broker(self,**extra):
        broker=Broker()
        with contextlib.redirect_stdout(io.StringIO()):broker.device_message(hello(**extra),'wifi')
        return broker

    def test_installed_language_is_independent_of_pc_entry_and_legacy_defaults(self):
        for host in ('en','zh-CN'):
            for firmware,protocol,expected in [('en',1,'en'),('zh-CN',1,'zh-CN'),('en',True,'zh-CN'),('unknown',1,'zh-CN'),('en',None,'zh-CN')]:
                with self.subTest(host=host,firmware=firmware,protocol=protocol),mock.patch.dict(os.environ,COMPANION_LANGUAGE=host):
                    broker=self.broker(ui_language=firmware,ui_language_protocol=protocol)
                    self.assertEqual(broker.device_language,expected)
                    title=broker.snapshot()['history'][0]
                    self.assertEqual(title.startswith('Bridge started'),expected=='en')

    def test_same_boot_cannot_change_language_or_request_pagination(self):
        broker=self.broker(ui_language='en',ui_language_protocol=1)
        with contextlib.redirect_stdout(io.StringIO()):
            broker.device_message(hello(ui_language='zh-CN',ui_language_protocol=1),'wifi')
        self.assertEqual(broker.device_language,'en')
        with contextlib.redirect_stdout(io.StringIO()):
            broker.device_message(hello(boot='new-boot',ui_language='zh-CN',ui_language_protocol=1),'wifi')
        self.assertEqual(broker.device_language,'zh-CN')

    def test_only_marked_system_text_is_translated_and_metadata_survives_copy(self):
        # A user path/command deliberately includes an exact system phrase.
        user='D:/权限请求/无/Tool.txt'
        value=dt('申请原因：')+'\n'+user
        self.assertEqual(render(value,'en'),'Reason:\n'+user)
        self.assertEqual(render(user,'en'),user)
        self.assertEqual(render(copy.deepcopy(value),'en'),render(value,'en'))
        joined=localized_join('\n',[dt('工作目录：'),user])
        self.assertEqual(render(joined,'en'),'Working directory:\n'+user)

    def test_native_permissions_keep_exact_grants_and_every_user_character(self):
        params={'threadId':'thread','turnId':'turn','itemId':'item','startedAtMs':int(time.time()*1000),
                'cwd':'/项目/权限请求','reason':'User reason / 中文理由',
                'permissions':{'network':{'enabled':True},'fileSystem':{'write':['/项目/'+('long-path/'*60)+'文件.txt']}}}
        before=copy.deepcopy(params)
        chinese=native_view('item/permissions/requestApproval',params)
        english=native_view('item/permissions/requestApproval',params,'en')
        self.assertEqual(english['allow_result'],chinese['allow_result'])
        self.assertEqual(english['deny_result'],chinese['deny_result'])
        self.assertEqual(english['can_allow'],chinese['can_allow'])
        joined=''.join(p.replace('\n','') for p in english['review_pages'])
        for raw in [params['cwd'],params['reason'],*params['permissions']['fileSystem']['write']]:
            self.assertIn(visible_text(raw),joined)
        self.assertIn('Requestthesepermissions',joined.replace(' ',''))
        for page in english['review_pages']:
            self.assertLess(len(page.encode('utf-8')),PAGE_BYTES)
            self.assertLessEqual(len(page.split('\n')),ROWS)
            self.assertTrue(all(len(line)<=COLUMNS for line in page.split('\n')))
        self.assertEqual(params,before)

    def test_unknown_semantics_and_missing_diff_remain_nonapprovable(self):
        for method,params in [('item/fileChange/requestApproval',{'cwd':'/test'}),
                              ('item/commandExecution/requestApproval',{'command':'pwd','additionalPermissions':{'new':True}})]:
            view=native_view(method,params,'en')
            self.assertFalse(view['can_allow']);self.assertTrue(view['can_deny'])

    def test_hook_pages_preserve_raw_commands_and_localize_system_labels(self):
        raw='printf "申请原因：中文原文"'
        body=hook_text({'tool_name':'Bash','cwd':'/test','tool_input':{'command':raw}})
        english=''.join(p.replace('\n','') for p in pages(body,'en'))
        self.assertIn(raw,english)
        self.assertIn('Command:',english)
        self.assertNotIn('仅本次操作',english)

    def test_english_receipts_and_events_use_device_language(self):
        broker=self.broker(ui_language='en',ui_language_protocol=1)
        with contextlib.redirect_stdout(io.StringIO()):
            broker.event({'hook_event_name':'PostToolUse','session_id':'test'})
        data=broker.snapshot()
        self.assertEqual(data['receipt'],'Tool returned')
        self.assertEqual(data['history'][0],'Tool returned')
        self.assertLess(len(json.dumps(data,ensure_ascii=False).encode()),4096)

    def test_english_device_still_requires_delivered_last_page_before_allow(self):
        broker=self.broker(ui_language='en',ui_language_protocol=1)
        broker.desktop_event({'relay':'relay','sessions':['thread'],'kind':'heartbeat'})
        params={'threadId':'thread','turnId':'turn','itemId':'item','startedAtMs':int(time.time()*1000),
                'command':'pwd','cwd':'/test','reason':'Full review required'}
        result=[]
        worker=threading.Thread(target=lambda:result.append(broker.desktop_request(
            {'relay':'relay','method':'item/commandExecution/requestApproval','native_id':'native','params':params})),daemon=True)
        worker.start()
        try:
            deadline=time.monotonic()+2
            while broker.request is None and time.monotonic()<deadline:time.sleep(.005)
            self.assertIsNotNone(broker.request)
            request=broker.request
            def message(**extra):return dict(boot=broker.boot,epoch=broker.epoch,id=request['id'],digest=request['digest'],**extra)
            data=broker.snapshot();last=data['review_total']
            self.assertIn('Command',data['command'])
            self.assertFalse(broker.decision(message(choice='allow',review_page=last)))
            self.assertTrue(broker.review_page(message(review_page=last)))
            self.assertFalse(broker.decision(message(choice='allow',review_page=last)))
            self.assertTrue(broker.snapshot()['can_allow'])
            self.assertTrue(broker.decision(message(choice='allow',review_page=last)))
            worker.join(timeout=2)
            self.assertEqual(result[0]['result']['decision'],'accept')
        finally:
            with contextlib.redirect_stdout(io.StringIO()):broker.device_message(hello(boot='cleanup'),'wifi')
            worker.join(timeout=2)
