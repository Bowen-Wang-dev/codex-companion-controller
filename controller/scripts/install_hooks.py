#!/usr/bin/env python3
"""Register official hooks without granting hook trust or replacing other hooks."""
import argparse
import json
import os
from pathlib import Path
import shlex
import shutil
import time

ROOT = Path(__file__).resolve().parents[1]
EVENTS = ['UserPromptSubmit', 'PreToolUse', 'PermissionRequest', 'PostToolUse', 'Stop', 'Interrupt', 'SessionEnd']
COMMAND = '/usr/bin/python3 ' + shlex.quote(str(ROOT / 'bridge' / 'hook.py'))


def merge(data, command=COMMAND):
    hooks = data.setdefault('hooks', {})
    if not isinstance(hooks, dict):
        raise ValueError('Existing hooks must be an object; refusing replacement')
    for event in EVENTS:
        entries = hooks.setdefault(event, [])
        if not isinstance(entries, list):
            raise ValueError('Existing event handlers must be arrays; refusing replacement')
        matching=[h for e in entries for h in e.get('hooks',[]) if h.get('command')==command]
        if matching:
            for h in matching:h['timeout']=115 if event in ('PreToolUse','PermissionRequest') else 1
            continue
        handler = {'type': 'command', 'command': command, 'timeout': 115 if event in ('PreToolUse','PermissionRequest') else 1}
        entries.append({'hooks': [handler]})
    return data


def remove_ours(data, command=COMMAND):
    hooks = data.get('hooks', {})
    for event, entries in list(hooks.items()):
        kept = []
        for group in entries:
            handlers = [h for h in group.get('hooks', []) if h.get('command') != command]
            if handlers:
                kept.append(dict(group, hooks=handlers))
        if kept:
            hooks[event] = kept
        else:
            hooks.pop(event)
    return data


def save(path, transform, backup_directory=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.loads(path.read_text()) if path.exists() else {}
    before = json.dumps(data, sort_keys=True)
    data = transform(data)
    if before == json.dumps(data, sort_keys=True):
        print('Already configured:', path)
        return
    if path.exists():
        backup_directory=backup_directory or path.parent
        backup_directory.mkdir(parents=True,exist_ok=True)
        shutil.copy2(path, backup_directory / ('hooks.backup-' + str(time.time_ns()) + '.json'))
    temporary = path.with_suffix('.tmp')
    with temporary.open('w') as output:
        os.chmod(temporary, 0o600)
        json.dump(data, output, indent=2, ensure_ascii=False)
        output.write('\n')
        output.flush()
        os.fsync(output.fileno())
    os.replace(temporary, path)
    print('Configured:', path)


def main():
    parser = argparse.ArgumentParser()
    scope = parser.add_mutually_exclusive_group(required=True)
    scope.add_argument('--project', type=Path)
    scope.add_argument('--user', action='store_true', help='Register for all local Codex chats')
    parser.add_argument('--output', type=Path, help='Write a review file without changing active configuration')
    parser.add_argument('--remove-project-copy', type=Path, action='append', default=[])
    args = parser.parse_args()
    if args.output:
        target = args.output
    elif args.user:
        target = Path(os.environ.get('CODEX_HOME', str(Path.home() / '.codex'))) / 'hooks.json'
    else:
        target = args.project.resolve() / '.codex' / 'hooks.json'
    backups=ROOT/'private'/'hook-backups' if args.user and not args.output else None
    save(target, merge, backups)
    if args.user and not args.output:
        # Source releases use repo/controller; the original local layout used
        # repo/outputs/PassportController. Clean only the corresponding project.
        project_root=ROOT.parent if (ROOT.parent/'mac-demo').is_dir() else ROOT.parents[1]
        projects={project_root.resolve(),*(p.resolve() for p in args.remove_project_copy)}
        for project in sorted(projects):
            local = project.resolve() / '.codex' / 'hooks.json'
            if local.exists():
                try:
                    save(local, remove_ours, backups)
                except PermissionError:
                    print('用户级注册已完成；项目副本受目录权限保护，未清理：',local)
    print('注册已完成，但尚未授予 Hook 信任。请在 Codex 审阅并信任这些 Hook；CLI 使用 /hooks。')
    print('常规 Hook 审批支持设备批准 / 拒绝；原生目录 / 网络请求可先在设备拒绝，或选择到 Mac 继续授权。')


if __name__ == '__main__':
    main()
