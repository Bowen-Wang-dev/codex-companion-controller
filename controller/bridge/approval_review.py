"""Lossless, bounded pages of the original approval; no model summarization.

Only one page crosses the device transport. The complete review stays on Mac
and is bound to the request's original digest. Unknown glyphs use visible Unicode
escapes rather than disappearing on the device's subset font.
"""
import copy
from functools import lru_cache
import json
from pathlib import Path
import unicodedata

PROTOCOL = 1
ROWS = 7  # ui_font line_height=20 plus 2px leading: 7*20+6*2=152px.
COLUMNS = 13  # At most 13 full-em glyphs fit the 210px, 16px-font body.
PAGE_BYTES = 512


@lru_cache(maxsize=1)
def glyphs():
    path = Path(__file__).resolve().parents[1] / 'docs/ui-font.json'
    try:
        return set(json.loads(path.read_text())['characters'])
    except (OSError, ValueError, KeyError):
        return set()


def visible_text(value):
    result = []
    available = glyphs()
    for char in str(value):
        code = ord(char)
        if char == '\n' or 32 <= code <= 126 or (char in available and unicodedata.category(char)[0] not in 'CMZ'):
            result.append(char)
        else:
            result.append(('\\u%04x' if code <= 0xffff else '\\U%08x') % code)
    return ''.join(result)


def pages(text):
    """Conservative full-em wrapping; concatenating lines loses no characters."""
    lines = []
    for original in visible_text(text).split('\n'):
        if original:
            lines.extend(original[start:start+COLUMNS] for start in range(0, len(original), COLUMNS))
        else:
            lines.append('')
    result = ['\n'.join(lines[start:start+ROWS]) for start in range(0, len(lines), ROWS)]
    return result or ['']


LABELS = {'enabled':'是否启用','network':'网络权限','fileSystem':'文件权限',
          'read':'读取路径','write':'写入路径','entries':'路径规则','access':'访问方式',
          'path':'路径','pattern':'匹配规则','type':'路径类型','value':'范围',
          'globScanMaxDepth':'规则扫描深度','host':'主机','protocol':'网络协议',
          'kind':'操作类型','subpath':'子路径','additionalPermissions':'附加权限',
          'grantRoot':'写入根目录','name':'名称','query':'搜索内容'}
OPAQUE = {'threadId','turnId','itemId','startedAtMs','approvalId'}


def describe(value,label):
    """Readable fallback for new fields, retaining every value without JSON."""
    if isinstance(value,dict):
        result=[label+'：']
        for key,child in value.items():result.extend(describe(child,LABELS.get(key,'其他参数 '+key)))
        if not value:result.append('无')
        return result
    if isinstance(value,list):
        result=[label+'('+str(len(value))+'项)：']
        for index,child in enumerate(value,1):result.extend(describe(child,str(index)))
        return result
    text='未提供' if value is None else '是' if value is True else '否' if value is False else str(value)
    return [label+'：'+text]


def permission_lines(profile):
    result=[]
    network=profile.get('network')
    if isinstance(network,dict) and set(network)=={'enabled'}:
        if network['enabled'] is True:result.append('网络：申请联网')
        elif network['enabled'] is False:result.append('网络：不申请联网')
        else:result.append('网络：未指定')
    elif network is not None:result.extend(describe(network,'网络权限'))
    fs=profile.get('fileSystem')
    if isinstance(fs,dict):
        for key,label in (('read','申请读取'),('write','申请写入')):
            values=fs.get(key)
            if values is not None:result.extend(describe(values,label))
        entries=fs.get('entries')
        if isinstance(entries,list):
            for index,entry in enumerate(entries,1):
                if not isinstance(entry,dict):result.extend(describe(entry,'路径规则 '+str(index)));continue
                access={'read':'申请读取','write':'申请写入','deny':'拒绝访问'}.get(entry.get('access'),'访问方式 '+str(entry.get('access')))
                path=entry.get('path')
                if isinstance(path,dict) and path.get('type')=='path' and set(path)=={'type','path'}:
                    result.append(access+'：'+str(path['path']))
                elif isinstance(path,dict) and path.get('type')=='glob_pattern' and set(path)=={'type','pattern'}:
                    result.append(access+'匹配路径：'+str(path['pattern']))
                else:
                    result.append(access)
                    result.extend(describe(path,'路径范围'))
                for key,child in entry.items():
                    if key not in ('access','path'):result.extend(describe(child,'其他参数 '+key))
        elif entries is not None:result.extend(describe(entries,'路径规则'))
        for key,child in fs.items():
            if key not in ('read','write','entries'):result.extend(describe(child,LABELS.get(key,'其他参数 '+key)))
    elif fs is not None:result.extend(describe(fs,'文件权限'))
    for key,child in profile.items():
        if key not in ('network','fileSystem'):result.extend(describe(child,'其他权限 '+key))
    return result


def native_text(method,params,scope):
    """Translate known semantics, preserving complete commands/paths/reasons.

    Routing IDs/timestamps are verified out of band, not user decisions. Parsed
    commandActions and proposed long-term policies do not change our one-shot
    response; the exact command is shown instead of those redundant suggestions.
    """
    permission=method=='item/permissions/requestApproval'
    command=method=='item/commandExecution/requestApproval'
    lines=[]
    if permission:
        profile=params.get('permissions')
        lines.append('请求新增以下权限')
        lines.extend(permission_lines(profile) if isinstance(profile,dict) else describe(profile,'权限范围'))
    elif command:
        lines.extend(['请求执行以下命令',str(params.get('command') or '未提供命令')])
        if params.get('kind')=='writeStdin':lines.append('操作：向运行中的终端输入内容')
    else:
        lines.extend(['请求修改文件','未提供修改明细，请在 Mac 审阅。'])
    if params.get('reason'):lines.extend(['申请原因：',str(params['reason'])])
    if params.get('cwd'):lines.extend(['工作目录：',str(params['cwd'])])
    if params.get('environmentId') is not None:lines.extend(describe(params['environmentId'],'执行环境'))
    if params.get('networkApprovalContext') is not None:
        lines.extend(describe(params['networkApprovalContext'],'网络连接范围'))
    handled=OPAQUE|{'reason','cwd','environmentId','networkApprovalContext'}
    if permission:handled.add('permissions')
    if command:
        handled|={'command','commandActions','proposedExecpolicyAmendment',
                  'proposedNetworkPolicyAmendments','availableDecisions'}
    if command and params.get('kind','command') in ('command','writeStdin'):handled.add('kind')
    for key,value in params.items():
        if key not in handled:lines.extend(describe(value,LABELS.get(key,'其他参数 '+key)))
    lines.extend(['授权有效期：',scope])
    return '\n'.join(lines)


def hook_text(event):
    lines=['请求执行以下操作',str(event.get('tool_name') or '未命名操作')]
    if event.get('cwd'):lines.extend(['工作目录：',str(event['cwd'])])
    args=event.get('tool_input')
    if isinstance(args,dict):
        for key,value in args.items():
            if key in ('command','cmd'):lines.extend(['执行命令：',str(value)])
            elif key in ('description','justification'):lines.extend(['申请原因：',str(value)])
            else:lines.extend(describe(value,LABELS.get(key,'操作参数 '+key)))
    else:lines.extend(describe(args,'操作内容'))
    lines.append('仅本次操作，不保存长期权限')
    return '\n'.join(lines)


def native_view(method, params):
    """Exact native request and one-shot response, independent of text length."""
    permission = method == 'item/permissions/requestApproval'
    command = method == 'item/commandExecution/requestApproval'
    title = '权限申请' if permission else '命令执行审批' if command else '文件修改审批'
    allowed = False
    if permission:
        profile = params.get('permissions')
        # The official response accepts the requested profile. Preserve it
        # exactly, including entries/globs/nulls, and never add permissions.
        allowed = isinstance(profile, dict) and bool(profile) and not set(profile)-{'network', 'fileSystem'}
        grant = {key:copy.deepcopy(value) for key,value in profile.items() if value is not None} if allowed else {}
        allowed = allowed and bool(grant)
        allow = {'permissions': grant, 'scope': 'turn'}
        deny = {'permissions': {}, 'scope': 'turn'}
        scope = '仅本轮，不保存长期权限'
        title = '目录与网络权限' if grant.get('network') and grant.get('fileSystem') else '目录权限请求' if grant.get('fileSystem') else '网络权限请求' if grant.get('network') else title
    else:
        allow = {'decision': 'accept'}
        deny = {'decision': 'decline'}
        # File approval callbacks do not include the diff. Keep them reviewable
        # and deniable here; do not present missing changes as a complete review.
        allowed = command and isinstance(params.get('command'), str) and bool(params['command'])
        if command and params.get('kind','command') not in ('command','writeStdin'):allowed=False
        # Unknown extra-grant semantics remain on Mac until supported explicitly.
        if params.get('additionalPermissions') is not None:
            allowed = False
        decisions = params.get('availableDecisions')
        if decisions is not None and (not isinstance(decisions, list) or 'accept' not in decisions):
            allowed = False
        scope = '仅本次操作，不记住批准'
    body = native_text(method,params,scope)
    return {'command': title, 'project': '', 'scope': scope,
            'can_allow': allowed, 'can_deny': True,
            'allow_result': allow, 'deny_result': deny,
            'review_pages': pages(body)}
