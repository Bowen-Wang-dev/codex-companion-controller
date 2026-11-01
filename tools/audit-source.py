#!/usr/bin/env python3
"""Audit Git-indexed publication bytes without reading runtime credentials."""
import hashlib
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
blocked_parts = {'private', '.codex', '.git', '.venv', '__pycache__', 'managed_components', 'dist', 'node_modules'}
blocked_names = {'auth.json', 'wireless.json', 'wireless-pending.json', 'pet_assets.h', '.env', 'sdkconfig'}
blocked_suffixes = {'.pem', '.key', '.p12', '.pfx', '.bin', '.elf', '.map', '.zip', '.png', '.jpg', '.jpeg', '.heic', '.webp', '.pyc', '.log'}
wheels = {
    Path('controller/vendor/websockets-17.3-py3-none-any.whl'): 'dc2b495a92b3971966bf102e73589f950db3ec1ca6713265355ce7771d97b199',
    Path('controller/vendor/pyserial-3.5-py2.py3-none-any.whl'): 'c4451db6ba391ca6ca299fb3ec7bae67a5c55dde170964c7a14ceefec02f2cf0',
}
patterns = [
    re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH |ENCRYPTED )?PRIVATE KEY-----'),
    re.compile(r'gh[pousr]_[A-Za-z0-9]{30,}'),
    re.compile(r'github_pat_[A-Za-z0-9_]{30,}'),
    re.compile(r'sk-(?:proj-)?[A-Za-z0-9_-]{24,}'),
]


def indexed_blobs(root):
    """Read staged blobs, including content hidden by an unstaged edit."""
    listing = subprocess.check_output(['git', '-C', str(root), 'ls-files', '--stage', '-z'])
    entries = []
    for record in listing.split(b'\0'):
        if not record:
            continue
        metadata, name = record.split(b'\t', 1)
        mode, identifier, stage = metadata.split()
        entries.append((Path(name.decode()), mode, identifier, stage))
    if not entries:
        raise ValueError('Stage source files before auditing.')
    # Object IDs come from Git, not filenames or shell interpolation.
    result = subprocess.run(['git', '-C', str(root), 'cat-file', '--batch'],
                            input=b''.join(entry[2] + b'\n' for entry in entries),
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    offset = 0
    for path, mode, identifier, stage in entries:
        end = result.stdout.index(b'\n', offset)
        object_id, kind, size = result.stdout[offset:end].split()
        size = int(size)
        raw = result.stdout[end + 1:end + 1 + size]
        if object_id != identifier or len(raw) != size:
            raise ValueError('Git object response does not match the index')
        offset = end + 2 + size
        yield path, mode, stage, kind, raw


def audit(root=ROOT):
    failures = []
    count = 0
    for relative, mode, stage, kind, raw in indexed_blobs(root):
        count += 1
        if (stage != b'0' or mode not in (b'100644', b'100755') or kind != b'blob'
                or blocked_parts.intersection(relative.parts)
                or relative.name in blocked_names or relative.suffix.lower() in blocked_suffixes):
            failures.append(str(relative) + ': forbidden publication path or index mode')
            continue
        if relative in wheels:
            if hashlib.sha256(raw).hexdigest() != wheels[relative]:
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
        raise ValueError('\n'.join(failures))
    return count


if __name__ == '__main__':
    try:
        count = audit()
    except (ValueError, subprocess.SubprocessError) as error:
        sys.exit(str(error))
    print(f'PASS: {count} indexed source files; no forbidden assets, runtime files or credential patterns.')
    print('Heuristic index audit only; unstaged/untracked changes require separate review.')
