"""Device-owned language, independent of the PC console's language.

Only explicitly marked system text is localized. User commands, paths, reasons,
questions, protocol identifiers and permission results are never translated.
"""
import json
from pathlib import Path

_ENGLISH = json.loads(Path(__file__).with_name('device_locale_en.json').read_text(encoding='utf-8'))


class DeviceText(str):
    def __new__(cls, chinese, english):
        value = super().__new__(cls, chinese)
        value.english = english
        return value

    def __getnewargs__(self):
        return str(self), self.english

    def __add__(self, other):
        if not isinstance(other, str):
            return NotImplemented
        return DeviceText(str(self)+str(other), self.english+render(other, 'en'))

    def __radd__(self, other):
        if not isinstance(other, str):
            return NotImplemented
        return DeviceText(str(other)+str(self), render(other, 'en')+self.english)


def dt(message):
    return DeviceText(message, _ENGLISH[message])


def device_string(value):
    return value if isinstance(value, DeviceText) else str(value)


def localized_join(separator, values):
    values = list(values)
    chinese = separator.join(values)
    if not any(isinstance(value, DeviceText) for value in values):
        return chinese
    return DeviceText(chinese, separator.join(render(value, 'en') for value in values))


def render(value, language):
    if isinstance(value, DeviceText):
        return value.english if language == 'en' else str(value)
    if isinstance(value, dict):
        return {key: render(child, language) for key, child in value.items()}
    if isinstance(value, list):
        return [render(child, language) for child in value]
    return value
