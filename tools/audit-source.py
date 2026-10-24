#!/usr/bin/env python3
"""Audit only Git-indexed publication files; never read runtime credentials."""
import hashlib
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
files = subprocess.check_output(['git', '-C', str(ROOT), 'ls-files', '-z']).decode().split('\0')
files = [Path(name) for name in files if name]
if not files:
    sys.exit('Stage source files before auditing.')
blocked_parts = {'private', '.codex', '.git', '.venv', '__pycache__', 'managed_components', 'dist', 'node_modules'}
blocked_names = {'auth.json', 'wireless.json', 'wireless-pending.json', 'pet_assets.h', '.env', 'sdkconfig'}
blocked_suffixes = {'.pem', '.key', '.p12', '.pfx', '.bin', '.elf', '.map', '.zip', '.png', '.jpg', '.jpeg', '.heic', '.webp', '.pyc', '.log'}
wheel = Path('controller/vendor/websockets-17.3-py3-none-any.whl')
wheel_sha = 'dc2b495a92b3971966bf102e73589f950db3ec1ca6713265355ce7771d97b199'
patterns = [
    re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH |ENCRYPTED )?PRIVATE KEY-----'),
    re.compile(r'gh[pousr]_[A-Za-z0-9]{30,}'),
    re.compile(r'github_pat_[A-Za-z0-9_]{30,}'),
    re.compile(r'sk-(?:proj-)?[A-Za-z0-9_-]{24,}'),
]
failures = []
for relative in files:
    path = ROOT / relative
    if path.is_symlink() or blocked_parts.intersection(relative.parts) or path.name in blocked_names or path.suffix.lower() in blocked_suffixes:
        failures.append(str(relative) + ': forbidden publication path')
        continue
    raw = path.read_bytes()
    if relative == wheel:
        if hashlib.sha256(raw).hexdigest() != wheel_sha:
            failures.append(str(relative) + ': vendor digest mismatch')
        continue
    try:
        content = raw.decode('utf-8')
    except UnicodeDecodeError:
        failures.append(str(relative) + ': unexpected binary')
        continue
    if any(pattern.search(content) for pattern in patterns):
        failures.append(str(relative) + ': possible secret; content suppressed')
if failures:
    sys.exit('\n'.join(failures))
print(f'PASS: {len(files)} indexed source files; no forbidden assets, runtime files or credential patterns.')
print('Heuristic audit only; it does not replace human review of publication contents.')
