"""Read the active Codex provider without exposing credentials.

The controller uses ChatGPT account/rate-limit RPCs only for the built-in
ChatGPT provider. Custom providers usually expose inference, not those account
APIs, so the Bridge reports custom-provider mode with token billing and usage unavailable until a provider usage signal is received.
"""
from dataclasses import dataclass
from pathlib import Path
import hashlib
import os
try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10 and the macOS system Python
    tomllib = None


@dataclass(frozen=True)
class Provider:
    provider_id: str
    name: str
    model: str
    base_url: str
    wire_api: str
    requires_openai_auth: bool

    @property
    def is_chatgpt(self):
        return self.provider_id in ('chatgpt', 'openai') and not self.base_url

    @property
    def binding(self):
        value = '\0'.join((self.provider_id, self.name, self.model, self.base_url))
        return hashlib.sha256(value.encode()).hexdigest()

    def display(self):
        return {
            'auth': 'provider', 'provider': self.provider_id,
            'providerName': self.name, 'model': self.model,
            'wireApi': self.wire_api, 'limits': [], 'resets': None,
            'ordinaryUsageAllowed': None,
        }


def config_path():
    home = Path(os.environ.get('CODEX_HOME') or Path.home() / '.codex')
    return home / 'config.toml'


def _fallback_toml(text):
    """Parse the small scalar subset needed here when tomllib is absent."""
    result = {}
    section = result
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        if line.startswith('[') and line.endswith(']'):
            section = result
            for part in line[1:-1].strip().split('.'):
                section = section.setdefault(part, {})
            continue
        if '=' not in line:
            continue
        key, value = (part.strip() for part in line.split('=', 1))
        if value.startswith('\"') and value.endswith('\"'):
            value = value[1:-1]
        elif value.lower() in ('true', 'false'):
            value = value.lower() == 'true'
        else:
            continue
        section[key] = value
    return result


def active_provider(path=None):
    """Return provider metadata only; never return token/header values."""
    path = Path(path or config_path())
    try:
        raw = path.read_text()
        if tomllib is not None:
            config = tomllib.loads(raw)
        else:
            config = _fallback_toml(raw)
    except (OSError, UnicodeError, ValueError):
        return Provider('chatgpt', 'ChatGPT', str(os.environ.get('CODEX_MODEL', '')), '', 'responses', True)
    provider_id = config.get('model_provider') or 'chatgpt'
    model = str(config.get('model') or '')
    table = config.get('model_providers') or {}
    detail = table.get(provider_id) if isinstance(table, dict) else None
    if not isinstance(detail, dict):
        detail = {}
    base_url = str(detail.get('base_url') or '')
    name = str(detail.get('name') or provider_id)
    wire_api = str(detail.get('wire_api') or 'responses')
    requires = bool(detail.get('requires_openai_auth', provider_id == 'chatgpt'))
    return Provider(str(provider_id), name, model, base_url, wire_api, requires)
