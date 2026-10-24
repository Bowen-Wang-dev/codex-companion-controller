import tempfile
import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parents[1] / 'bridge'))
from provider_config import active_provider
from service import Broker


class ProviderConfigTests(unittest.TestCase):
    def test_custom_provider_does_not_read_or_expose_secret(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'config.toml'
            path.write_text('''model_provider = "custom"\nmodel = "gpt-5.6-sol"\n[model_providers.custom]\nname = "灵算"\nbase_url = "https://lingsuan.top/v1"\nwire_api = "responses"\nrequires_openai_auth = false\nexperimental_bearer_token = "sk-secret"\n''')
            provider = active_provider(path)
        self.assertFalse(provider.is_chatgpt)
        self.assertEqual(provider.provider_id, 'custom')
        self.assertEqual(provider.model, 'gpt-5.6-sol')
        self.assertEqual(provider.wire_api, 'responses')
        self.assertNotIn('secret', repr(provider.display()))
        self.assertEqual(provider.display()['limits'], [])
        self.assertIsNone(provider.display()['ordinaryUsageAllowed'])

    def test_chatgpt_fallback_keeps_builtin_mode(self):
        with tempfile.TemporaryDirectory() as folder:
            provider = active_provider(Path(folder) / 'missing.toml')
        self.assertTrue(provider.is_chatgpt)

    def test_python39_fallback_reads_provider_scalars_and_ignores_secrets(self):
        import provider_config
        original = provider_config.tomllib
        try:
            provider_config.tomllib = None
            with tempfile.TemporaryDirectory() as folder:
                path = Path(folder) / 'config.toml'
                path.write_text('''model_provider = "custom"
model = "gpt-5.6-sol"
[model_providers.custom]
name = "灵算"
base_url = "https://lingsuan.top/v1"
wire_api = "responses"
requires_openai_auth = false
experimental_bearer_token = "sk-hidden"
''')
                provider = active_provider(path)
        finally:
            provider_config.tomllib = original
        self.assertEqual(provider.provider_id, 'custom')
        self.assertEqual(provider.model, 'gpt-5.6-sol')
        self.assertFalse(provider.requires_openai_auth)

    def test_custom_provider_snapshot_does_not_show_subscription_quota(self):
        provider = active_provider()
        broker = Broker()
        broker.usage = provider.display()
        broker.usage_at = __import__('time').monotonic()
        broker.provider_info = {'id': provider.provider_id, 'name': provider.name,
                                'model': provider.model, 'billing': 'token'}
        broker.usage_status = '第三方 API 模式 · 按 Token 计费'
        snapshot = broker.snapshot()
        self.assertEqual(snapshot['provider']['billing'], 'token')
        self.assertIsNone(snapshot['primary'])
        self.assertIsNone(snapshot['secondary'])
        self.assertIsNone(snapshot['resets'])
        self.assertEqual(snapshot['usage_status'], '第三方 API 模式 · 按 Token 计费')


if __name__ == '__main__':
    unittest.main()
