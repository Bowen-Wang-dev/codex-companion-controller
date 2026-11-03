"""Exercise host languages without granting permissions or changing a device."""
import ast
import contextlib
import copy
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'bridge'))
sys.path.insert(0, str(ROOT/'scripts'))
import console_i18n
import controller_console
import firmware_update
import meter_client
import metering
import setup_windows


def has_han(text):
    return any('\u4e00' <= c <= '\u9fff' for c in text)


class ConsoleLanguageTests(unittest.TestCase):
    def test_default_and_unknown_language_preserve_chinese(self):
        for setting in ('', 'zh-CN', 'unexpected'):
            with self.subTest(setting=setting), mock.patch.dict(os.environ, COMPANION_LANGUAGE=setting):
                self.assertEqual(console_i18n.tr('选择：'), '选择：')

    def test_error_translation_preserves_user_data_and_core_provider_error(self):
        from provider_billing import parse_export
        with mock.patch.dict(os.environ, COMPANION_LANGUAGE='en'):
            self.assertEqual(console_i18n.tr('后台明细第 12 行无效'), 'Invalid provider export row 12')
            path='D:/我的目录/未知-选择：.json'
            self.assertEqual(console_i18n.tr(path),path)
            with self.assertRaisesRegex(ValueError,'后台明细缺少') as caught:
                parse_export('not,a,billing,export\n')
            self.assertFalse(has_han(console_i18n.tr(str(caught.exception))))

    def test_catalog_covers_all_literal_host_translations(self):
        # Audit real callers; this also catches new untranslated catalog entries.
        catalog=console_i18n._ENGLISH
        for folder in ('scripts','bridge'):
            for path in (ROOT/folder).glob('*.py'):
                for node in ast.walk(ast.parse(path.read_text(encoding='utf-8'))):
                    if (isinstance(node,ast.Call) and isinstance(node.func,ast.Name)
                            and node.func.id=='tr' and node.args
                            and isinstance(node.args[0],ast.Constant)
                            and isinstance(node.args[0].value,str)):
                        key=node.args[0].value
                        if has_han(key):self.assertIn(key,catalog,str(path))
        for key,value in catalog.items():
            self.assertTrue(value,key)
            self.assertFalse(has_han(value),key)

    def test_real_console_processes_are_single_language(self):
        for language,expected in (('zh-CN','Codex Companion 控制台'),('en','Codex Companion Console')):
            with self.subTest(language=language):
                result=subprocess.run([sys.executable,str(ROOT/'scripts/controller_console.py')],
                    input='invalid\nq\n',text=True,encoding='utf-8',capture_output=True,
                    env=dict(os.environ,COMPANION_LANGUAGE=language,PYTHONIOENCODING='utf-8'),timeout=10)
                self.assertEqual(result.returncode,0,result.stderr)
                self.assertIn(expected,result.stdout)
                self.assertEqual(has_han(result.stdout),language=='zh-CN')

    def test_submenus_cancel_without_side_effects_in_english(self):
        report={'status':None,'local_ips':[],'paired_ip':None,'address_changed':False,
                'pairing_problem':'','bridge_error':'Fixture'}
        output=io.StringIO()
        with mock.patch.dict(os.environ,COMPANION_LANGUAGE='en'),contextlib.redirect_stdout(output),\
                mock.patch.object(controller_console,'inspect',return_value=report),\
                mock.patch('builtins.input',return_value='q'),\
                mock.patch.object(controller_console,'run') as run,\
                mock.patch.object(controller_console.subprocess,'run') as execute:
            controller_console.device_bridge_menu()
            controller_console.usage_menu()
            controller_console.hooks_menu()
            firmware_update.main()
        run.assert_not_called();execute.assert_not_called()
        self.assertFalse(has_han(output.getvalue()),output.getvalue())

    def test_bootstrap_propagates_language_and_exit_status(self):
        for language in ('zh-CN','en'):
            env=dict(os.environ,COMPANION_LANGUAGE=language)
            with self.subTest(language=language),mock.patch.dict(os.environ,env),\
                    mock.patch.object(sys,'argv',['setup_windows.py','--restart-app']),\
                    mock.patch.object(setup_windows,'prepare',return_value=(Path('fixture-python'),env)),\
                    mock.patch.object(setup_windows.subprocess,'run',return_value=mock.Mock(returncode=7)) as run:
                self.assertEqual(setup_windows.main(),7)
                self.assertEqual(run.call_args.kwargs['env']['COMPANION_LANGUAGE'],language)
                self.assertEqual(run.call_args.args[0][-1],'--restart-app')

    def test_english_reset_still_requires_exact_reset_token(self):
        status={'metering':{'usage':{'meter_id':'fixture-meter'}}}
        output=io.StringIO()
        with mock.patch.dict(os.environ,COMPANION_LANGUAGE='en'),contextlib.redirect_stdout(output),\
                mock.patch.object(sys,'argv',['metering.py','--reset']),\
                mock.patch.object(metering,'request',return_value=status) as request,\
                mock.patch.object(metering,'summary',return_value='Fixture totals'),\
                mock.patch('builtins.input',return_value='reset'):
            metering.main()
        request.assert_called_once_with({'type':'status'})
        self.assertIn('Cancelled.',output.getvalue())
        self.assertFalse(has_han(output.getvalue()))

    def test_english_flash_confirmation_cancel_does_not_stop_or_write(self):
        manifest={'version':'fixture','sha256':'fixture-digest'}
        output=io.StringIO()
        with mock.patch.dict(os.environ,COMPANION_LANGUAGE='en'),contextlib.redirect_stdout(output),\
                mock.patch.object(firmware_update,'validate_image',return_value=manifest),\
                mock.patch.object(firmware_update,'flash_python',return_value='fixture-python'),\
                mock.patch('host_platform.usb_ports',return_value=['COM-fixture']),\
                mock.patch('builtins.input',return_value='flash'),\
                mock.patch('recover_bridge.stop_idle_bridge') as stop,\
                mock.patch.object(firmware_update.subprocess,'run') as execute:
            firmware_update.update()
        stop.assert_not_called();execute.assert_not_called()
        self.assertFalse(has_han(output.getvalue()))

    def test_summary_localizes_at_display_time_without_mutating_data(self):
        status={'bridge_revision':'fixture','firmware':'fixture','project_root':'/fixture',
            'metering':{'usage':{'reader_issue':'后台明细第 12 行无效'},
                        'cost':{'status':'request_boundaries_missing'}}}
        original=copy.deepcopy(status)
        for language in ('en','zh-CN','en'):
            with mock.patch.dict(os.environ,COMPANION_LANGUAGE=language):
                output=meter_client.summary(status)
                self.assertEqual(has_han(output),language=='zh-CN')
        self.assertEqual(status,original)

    def test_english_logs_leave_device_request_and_snapshot_in_chinese(self):
        from service import Broker
        output=io.StringIO()
        with mock.patch.dict(os.environ,COMPANION_LANGUAGE='en'),contextlib.redirect_stdout(output):
            broker=Broker()
            broker.device_message({'type':'hello','boot':'fixture-boot','firmware':'0.2.13',
                                   'readonly_notices':True},'wifi')
            broker.event({'hook_event_name':'PreToolUse','tool_name':'request_permissions',
                'session_id':'fixture-session','tool_use_id':'fixture-request','turn_id':'fixture-turn',
                'cwd':'/fixture','tool_input':{'permissions':{'network':{'enabled':True}}}})
            snapshot=broker.snapshot()
        self.assertFalse(has_han(output.getvalue()),output.getvalue())
        self.assertIn('网络',snapshot['command'])
        self.assertIn('网络',snapshot['project'])
        self.assertFalse(snapshot['can_allow'])


class RateEditorLanguageTests(unittest.TestCase):
    def test_utf8_rate_and_override_files_keep_model_names(self):
        import token_rates_gui as gui
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'private').mkdir()
            rates=root/'private/token_rates.json'
            rates.write_text(json.dumps({'models':{'模型-测试':{'input':1}}},ensure_ascii=False),encoding='utf-8')
            (root/'private/model_override.json').write_text(json.dumps({'model_id':'模型-校准'},ensure_ascii=False),encoding='utf-8')
            editor=gui.RateEditor.__new__(gui.RateEditor)
            editor.currency=mock.Mock();editor.model_override=mock.Mock()
            with mock.patch.object(gui,'ROOT',root),mock.patch.object(gui,'RATE_FILE',rates):
                editor._read()
            self.assertEqual(editor.rates,{'模型-测试':{'input':1}})
            editor.model_override.set.assert_called_once_with('模型-校准')

    def test_real_hidden_editor_english_text_save_and_validation(self):
        import tkinter as tk
        import token_rates_gui as gui
        try:
            window=tk.Tk();window.withdraw()
        except tk.TclError as error:
            self.skipTest('Tk display unavailable: '+str(error))
        self.addCleanup(window.destroy)
        with tempfile.TemporaryDirectory() as folder,mock.patch.dict(os.environ,COMPANION_LANGUAGE='en'),\
                mock.patch.object(gui.RateEditor,'_read'),\
                mock.patch.object(gui,'RATE_FILE',Path(folder)/'rates.json'),\
                mock.patch.object(gui,'FIELDS',tuple((key,console_i18n.tr(label)) for key,label in gui.FIELDS)):
            editor=gui.RateEditor(window)
            window.update_idletasks()
            texts=[window.title(),editor.status.get()]
            def collect(widget):
                try:texts.append(str(widget.cget('text')))
                except tk.TclError:pass
                for child in widget.winfo_children():collect(child)
            collect(window)
            self.assertFalse(has_han('\n'.join(texts)),texts)
            viewport=next(w for w in window.winfo_children() if isinstance(w,tk.Canvas))
            content=viewport.winfo_children()[0]
            self.assertLessEqual(content.winfo_reqwidth(),1100)
            editor.model.set('fixture-model')
            for value in editor.values.values():value.set('1')
            editor._save()
            saved=json.loads(gui.RATE_FILE.read_text(encoding='utf-8'))
            self.assertEqual(saved['models']['fixture-model']['rate_source'],'custom')
            self.assertEqual(saved['models']['fixture-model']['input'],1)
            editor.multiplier.set('-1')
            before=gui.RATE_FILE.read_bytes()
            with mock.patch.object(gui.messagebox,'showerror') as error:
                editor._save()
            self.assertIn('allowed range',error.call_args.args[1])
            self.assertEqual(gui.RATE_FILE.read_bytes(),before)


@unittest.skipUnless(sys.platform=='win32','real Windows CMD launchers')
class WindowsLanguageLauncherTests(unittest.TestCase):
    def test_both_launchers_pin_language_forward_arguments_and_exit_code(self):
        with tempfile.TemporaryDirectory(prefix='Companion 中文 ') as folder:
            root=Path(folder);(root/'scripts').mkdir()
            (root/'scripts/setup_windows.py').write_text(
                'import json,os,sys\nprint(json.dumps([os.environ.get("COMPANION_LANGUAGE"),sys.argv[1:]]))\nsys.exit(7)\n',encoding='utf-8')
            for name,language in (('Codex Companion 控制台.cmd','zh-CN'),('Codex Companion Console.cmd','en')):
                with self.subTest(language=language):
                    path=root/name;path.write_bytes((ROOT/name).read_bytes())
                    result=subprocess.run('cmd.exe /d /s /c ""'+str(path)+'" --fixture"',
                        input='\n',text=True,encoding='utf-8',capture_output=True,timeout=10,
                        env=dict(os.environ,CONTROLLER_MODERN_PYTHON=sys.executable,
                                 COMPANION_LANGUAGE='wrong-inherited-language'))
                    self.assertEqual(result.returncode,7,result.stderr)
                    self.assertIn(json.dumps([language,['--fixture']]),result.stdout)
                    self.assertEqual(has_han(result.stdout),language=='zh-CN')


if __name__=='__main__':
    unittest.main()
