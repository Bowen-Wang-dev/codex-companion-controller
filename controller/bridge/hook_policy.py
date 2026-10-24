"""Bounded device review for official Hooks; never grant new sandbox scopes."""
import json
from pathlib import Path
import shlex


def permission_tool(event):
    return str(event.get('tool_name','')).rsplit('.',1)[-1].rsplit('__',1)[-1]=='request_permissions'


def permission_summary(event):
    args=event.get('tool_input')
    permissions=args.get('permissions') if isinstance(args,dict) else None
    if not isinstance(permissions,dict):return None
    lines=[];network=permissions.get('network')
    if isinstance(network,dict) and network.get('enabled') is True:lines.append('网络连接权限')
    fs=permissions.get('file_system',permissions.get('fileSystem'))
    if isinstance(fs,dict):
        for mode,label in (('read','读取'),('write','写入')):
            paths=fs.get(mode)
            if isinstance(paths,list):lines.extend(label+' '+p for p in paths if isinstance(p,str))
        entries=fs.get('entries')
        if isinstance(entries,list):
            for entry in entries:
                if not isinstance(entry,dict):continue
                path=entry.get('path')
                if isinstance(path,dict) and isinstance(path.get('path'),str):
                    lines.append(('读取' if entry.get('access')=='read' else '写入')+' '+path['path'])
    if not lines:return None
    heading='权限请求' if len(lines)>1 else '网络权限请求' if lines[0]=='网络连接权限' else '目录权限请求'
    return heading,'\n'.join(lines)


def project_name(event):
    args=event.get('tool_input') or {}
    cwd=(args.get('workdir') or args.get('cwd') or event.get('cwd')) if isinstance(args,dict) else event.get('cwd')
    if not isinstance(cwd,str) or not cwd.startswith('/') or not cwd.isascii() or any(ord(c)<32 for c in cwd):return None
    name=Path(cwd).name or '/'
    return name if len(name)<=64 else None


def ordinary_path(value,cwd=None):
    if not isinstance(value,str) or not value or value.startswith('-') or not value.isascii():return False
    if any(c in value for c in '\\*?[]{}~#$`\n\r\t'):return False
    parts=Path(value).parts
    if '..' in parts or any(p.startswith('.') and p!='.' for p in parts):return False
    sensitive={'Library','System','etc','.ssh','.codex','.aws','.gnupg','id_rsa','id_ed25519'}
    if any(p in sensitive for p in parts):return False
    if cwd:
        resolved=Path(cwd,value).resolve()
        if any(p in sensitive or (p.startswith('.') and p!='.') for p in resolved.parts):return False
    return True


def ordinary_command(command,cwd=None):
    if not isinstance(command,str) or len(command)>90 or not command.isascii():return False
    if any(ord(c)<32 or c in ';|&<>`$\\*?[]{}~#()' for c in command):return False
    try:words=shlex.split(command)
    except ValueError:return False
    if not words:return False
    if words in (['pwd'],['/bin/pwd'],['git','status'],['git','status','--short'],
                 ['git','status','--porcelain'],['git','diff','--stat']):return True
    program=words[0]
    if program not in ('ls','/bin/ls','stat','/usr/bin/stat','cat','/bin/cat','head','/usr/bin/head'):return False
    rest=words[1:];name=Path(program).name
    if name=='ls':
        rest=[v for v in rest if v not in ('-a','-l','-la','-al','-1','-d','--')]
        return len(rest)<=1 and all(ordinary_path(v,cwd) for v in rest)
    if name=='head' and rest[:1]==['-n']:
        if len(rest)!=3 or not rest[1].isdigit() or not 1<=int(rest[1])<=1000:return False
        rest=rest[2:]
    return len(rest)==1 and ordinary_path(rest[0],cwd)


def display(event):
    """All approvable details fit the existing 2 / 6 / 2 line device layout."""
    tool=event.get('tool_name','Operation');args=event.get('tool_input')
    name=project_name(event)
    result={'command':'操作审批 · 在 Mac 查看','project':name or 'Unknown project',
            'scope':'复杂操作：请在 Mac 审阅','can_allow':False,'can_deny':True}
    if not isinstance(args,dict) or name is None:return result
    if tool=='Bash':
        command=args.get('command',args.get('cmd'))
        keys={'command','cmd','description','cwd','workdir','timeout_ms','timeout','sandbox_permissions',
              'justification','prefix_rule','yield_time_ms','max_output_tokens','max_output_chars','login','tty','shell'}
        if set(args)-keys or args.get('prefix_rule') or ('command' in args and 'cmd' in args and args['command']!=args['cmd']):return result
        if args.get('shell') not in (None,'/bin/bash','/bin/zsh'):return result
        cwd=args.get('workdir') or args.get('cwd') or event.get('cwd')
        if not ordinary_command(command,cwd):return result
        mode=args.get('sandbox_permissions','use_default')
        if mode not in ('use_default','require_escalated'):return result
        title='命令执行审批';body='项目：'+name+'\n'+command
        scope='沙箱外执行，仅当前命令' if mode=='require_escalated' else '本次命令，现有沙箱权限'
    elif isinstance(tool,str) and tool.startswith(('mcp__filesystem__','mcp__fs__')):
        operation=tool.rsplit('__',1)[-1]
        if operation not in ('read_file','list_directory','get_file_info') or set(args)!={'path'} or not ordinary_path(args['path'],event.get('cwd')):return result
        title='MCP '+operation;body='项目：'+name+'\n'+json.dumps(args,ensure_ascii=False,separators=(',',':'))
        scope='仅本次操作 · 现有权限'
    else:return result
    if len(body.encode())>90 or len(title)>48:return result
    return {'command':title,'project':body,'scope':scope,'can_allow':True,'can_deny':True}
