#!/usr/bin/env python3
"""Create separate local source and private recovery archives. Never upload."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import tarfile
import time
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'controller/bridge'))
from private_permissions import set_private
SKIP_DIRS = {'bridge-venv', 'bridge-venv-homebrew', 'bridge-venv-windows', 'flash-venv-windows', 'pycache', 'checks', 'component-cache', '__pycache__'}


def private_files(root):
    private = root / 'controller/private'
    if private.is_symlink():
        raise ValueError('Refusing symlink recovery directory')
    for directory, dirs, files in os.walk(private, followlinks=False):
        here = Path(directory)
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and not (here / d).is_symlink())
        for name in sorted(files):
            p = here / name
            if p.is_symlink() or name in ('auth.json', 'app-relay.exe', 'app-relay.json') or p.suffix in ('.log', '.pyc'):
                continue
            if p.is_file(): yield p, p.relative_to(root).as_posix()
    for relative in ('controller/dist',):
        base = root / relative
        if base.is_symlink():
            raise ValueError('Refusing symlink recovery directory')
        for p in sorted(base.rglob('*')):
            if p.is_symlink(): raise ValueError('Refusing symlink in recovery material')
            if p.is_file(): yield p, p.relative_to(root).as_posix()
    for relative in ('controller/firmware/main/pet_assets.h', 'controller/firmware/sdkconfig', 'controller/firmware/sdkconfig.old'):
        p = root / relative
        if p.is_file() and not p.is_symlink(): yield p, relative


def pack_private(destination, files):
    records = []
    # Protect even an interrupted/invalid archive before writing private bytes,
    # and never truncate a previous recovery archive or follow its symlink.
    with destination.open('xb') as output:
        if sys.platform == 'win32':set_private(destination, 0o600)
        else:os.fchmod(output.fileno(), 0o600)
        return _pack_private(destination, output, files, records)


def _pack_private(destination, output, files, records):
    with tarfile.open(fileobj=output, mode='w:gz') as archive:
        for source, name in files:
            if source.is_symlink(): raise ValueError('Refusing symlink')
            raw = source.read_bytes()
            # Each JSON is one coherent read; this is not a stopped-service snapshot.
            if source.suffix == '.json': json.loads(raw)
            info = tarfile.TarInfo(name); info.size = len(raw); info.mode = 0o600
            info.mtime = int(source.stat().st_mtime)
            archive.addfile(info, io.BytesIO(raw))
            records.append({'path': name, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()})
        manifest = {'snapshot': 'live per-file read; ledger JSON validated; not a global transactional snapshot', 'files': records}
        raw = (json.dumps(manifest, ensure_ascii=False, indent=2) + '\n').encode()
        info = tarfile.TarInfo('PRIVATE-MANIFEST.json'); info.size = len(raw); info.mode = 0o600
        archive.addfile(info, io.BytesIO(raw))
    output.flush()
    # Full readback verifies every archived byte against the per-file manifest.
    with tarfile.open(destination, 'r:gz') as archive:
        for record in records:
            raw = archive.extractfile(record['path']).read()
            if len(raw) != record['bytes'] or hashlib.sha256(raw).hexdigest() != record['sha256']:
                raise ValueError('Private archive verification failed')
    return len(records)


def archive(destination, root=ROOT, hooks=None):
    if subprocess.check_output(['git', '-C', str(root), 'status', '--porcelain']):
        raise ValueError('Commit source and documentation before archiving; worktree is not clean')
    destination = destination.expanduser().resolve()
    destination.mkdir(mode=0o700, parents=True, exist_ok=False)
    set_private(destination, 0o700)
    source = destination / 'source.tar.gz'
    subprocess.run(['git', '-C', str(root), 'archive', '--format=tar.gz', '-o', str(source), 'HEAD'], check=True)
    bundle = destination / 'source-history.bundle'
    subprocess.run(['git', '-C', str(root), 'bundle', 'create', str(bundle), '--all'], check=True, capture_output=True)
    subprocess.run(['git', '-C', str(root), 'bundle', 'verify', str(bundle)], check=True, capture_output=True)
    files = list(private_files(root))
    if hooks is not None and hooks.is_file(): files.append((hooks, 'host-config/hooks.json'))
    count = pack_private(destination / 'PRIVATE-RECOVERY.tar.gz', files)
    instructions = '''LOCAL ARCHIVE — DO NOT UPLOAD PRIVATE-RECOVERY.tar.gz.
source.tar.gz contains committed shareable source; source-history.bundle preserves Git history.
PRIVATE-RECOVERY.tar.gz contains pairing keys, device backups, billing and private artwork.
It excludes Codex auth.json, virtualenvs, runtime logs, caches and compiled checks.
Keep this directory private (0700), its files 0600. This is a same-disk backup, not offsite storage.
Restore source first, then privately restore recovery files to matching relative paths.
Do not restore host-config/hooks.json blindly: compare other plugins and replace only exact Passport paths.
Install Homebrew python@3.12 and python-tk@3.12, recreate the venv, and run scripts/setup_bridge.sh.
Review private/local-env.sh paths for the destination; do not copy an old venv.
The source vendor directory contains both pinned wheels and licenses; setup works offline.
Start only through controller/Codex Companion 控制台.command after closing the App yourself.
Never publish Apple artwork, image-bearing firmware, keys or pairing identities.
'''
    (destination / 'RESTORE.txt').write_text(instructions)
    receipt = {'created_at': time.strftime('%Y-%m-%dT%H:%M:%S%z'),
               'commit': subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip(),
               'private_files_verified': count, 'files': {}}
    for p in sorted(destination.iterdir()):
        if p.is_file():
            set_private(p, 0o600)
            receipt['files'][p.name] = {'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
    path = destination / 'ARCHIVE-RECEIPT.json'
    path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n', encoding='utf-8'); set_private(path, 0o600)
    return receipt


if __name__ == '__main__':
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination', type=Path, required=True)
    parser.add_argument('--include-hooks', action='store_true')
    args = parser.parse_args()
    hooks = Path(os.environ.get('CODEX_HOME', str(Path.home() / '.codex'))) / 'hooks.json' if args.include_hooks else None
    result = archive(args.destination, hooks=hooks)
    print('Archive verified:', args.destination)
    print('Commit:', result['commit'], '| private files verified:', result['private_files_verified'])
