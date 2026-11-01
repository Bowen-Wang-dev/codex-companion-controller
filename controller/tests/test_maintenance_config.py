"""Maintenance configuration checks never restart services or write live files."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
sys.path.insert(0,str(ROOT/'bridge'))
import enable_long_context
import install_hooks
import token_rates_gui


class MaintenanceConfigTests(unittest.TestCase):
    def test_long_context_normalized_readback_reaches_restart_only_after_validation(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            with mock.patch.object(enable_long_context,'ROOT',root),mock.patch.object(enable_long_context,'inspect',return_value={'status':None}),mock.patch.object(enable_long_context,'show'),mock.patch('builtins.input',return_value='YES'),mock.patch('builtins.print'),mock.patch.object(enable_long_context,'stop_idle_bridge') as stop,mock.patch.object(enable_long_context.os,'execv') as execute:
                enable_long_context.main()
            saved=json.loads((root/'private/token_rates.json').read_text())
            self.assertEqual(saved['models'][enable_long_context.MODEL],enable_long_context.CARD)
            stop.assert_called_once_with(None)
            execute.assert_called_once()

    def test_hook_installation_cleans_current_repository_copy(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)/'project';controller=root/'controller';controller.mkdir(parents=True)
            local=root/'.codex/hooks.json';local.parent.mkdir();local.write_text('{}')
            with mock.patch.object(install_hooks,'ROOT',controller),mock.patch.object(install_hooks,'save') as save,mock.patch.object(sys,'argv',['install_hooks.py','--user']),mock.patch('builtins.print'):
                install_hooks.main()
            self.assertEqual(save.call_count,2)
            self.assertEqual(save.call_args_list[1].args[0],local.resolve())

    def test_price_source_roundtrip_keeps_disabled_custom_long_tier_disabled(self):
        class Variable:
            def __init__(self,value):self.value=value
            def get(self):return self.value
            def set(self,value):self.value=value
        editor=token_rates_gui.RateEditor.__new__(token_rates_gui.RateEditor)
        editor.rate_source=Variable('openai');editor.previous_source='custom'
        editor.model=Variable(next(iter(token_rates_gui.OPENAI_PRICES)))
        editor.values={key:Variable('1') for key,_ in token_rates_gui.FIELDS}
        editor.long_values={key:Variable('') for key,_ in token_rates_gui.FIELDS}
        editor.long_enabled=Variable(False);editor.long_threshold=Variable('not-used')
        editor.base_entries={};editor.long_entries={};editor.status=Variable('')
        editor._source_changed()
        self.assertTrue(editor.long_enabled.get())
        editor.rate_source.set('custom');editor._source_changed()
        self.assertFalse(editor.long_enabled.get())
        self.assertEqual([v.get() for v in editor.values.values()],['1']*len(token_rates_gui.FIELDS))


if __name__=='__main__':unittest.main()
