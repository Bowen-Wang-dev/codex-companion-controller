"""Host UI language only; never translate device payloads or protocol identifiers."""
import json
import os
import re
from pathlib import Path

_ENGLISH = json.loads(Path(__file__).with_name('locale_en.json').read_text(encoding='utf-8'))


def language():
    """Chinese is the default, independently of the operating system locale."""
    return 'en' if os.environ.get('COMPANION_LANGUAGE') == 'en' else 'zh-CN'


def tr(message):
    if language() != 'en':
        return message
    if message in _ENGLISH:
        return _ENGLISH[message]
    # Core provider errors also feed device diagnostics. Localize only their
    # host presentation, with an anchored pattern rather than editing data.
    row = re.fullmatch(r'后台明细第 (\d+) 行无效', message)
    if row:
        return 'Invalid provider export row ' + row[1]
    return message
