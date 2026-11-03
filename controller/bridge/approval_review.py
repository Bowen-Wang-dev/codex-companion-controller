"""Lossless, bounded pages of the original approval; no model summarization.

Only one page crosses the device transport. The complete review stays on the host
and is bound to the request's original digest. Unknown glyphs use visible Unicode
escapes rather than disappearing on the device's subset font.
"""
import copy
from functools import lru_cache
import json
from pathlib import Path
from device_i18n import dt, DeviceText, render, localized_join, device_string
import unicodedata

PROTOCOL = 1
ROWS = 7  # ui_font line_height=20 plus 2px leading: 7*20+6*2=152px.
COLUMNS = 13  # At most 13 full-em glyphs fit the 210px, 16px-font body.
PAGE_BYTES = 512


@lru_cache(maxsize=1)
def glyphs():
    path = Path(__file__).resolve().parents[1] / 'docs/ui-font.json'
    try:
        return set(json.loads(path.read_text(encoding='utf-8'))['characters'])
    except (OSError, ValueError, KeyError):
        return set()


def visible_text(value):
    result = []
    available = glyphs()
    for char in device_string(value):
        code = ord(char)
        if char == '\n' or 32 <= code <= 126 or (char in available and unicodedata.category(char)[0] not in 'CMZ'):
            result.append(char)
        else:
            result.append(('\\u%04x' if code <= 0xffff else '\\U%08x') % code)
    return ''.join(result)


def pages(text, language="zh-CN"):
    """Conservative full-em wrapping; concatenating lines loses no characters."""
    lines = []
    for original in visible_text(render(text, language)).split('\n'):
        if original:
            lines.extend(original[start:start+COLUMNS] for start in range(0, len(original), COLUMNS))
        else:
            lines.append('')
    result = [localized_join('\n',lines[start:start+ROWS]) for start in range(0, len(lines), ROWS)]
    return result or ['']


LABELS = {'enabled':dt('是否启用'),'network':dt('网络权限'),'fileSystem':dt('文件权限'),
          'read':dt('读取路径'),'write':dt('写入路径'),'entries':dt('路径规则'),'access':dt('访问方式'),
          'path':dt('路径'),'pattern':dt('匹配规则'),'type':dt('路径类型'),'value':dt('范围'),
          'globScanMaxDepth':dt('规则扫描深度'),'host':dt('主机'),'protocol':dt('网络协议'),
          'kind':dt('操作类型'),'subpath':dt('子路径'),'additionalPermissions':dt('附加权限'),
          'grantRoot':dt('写入根目录'),'name':dt('名称'),'query':dt('搜索内容')}
OPAQUE = {'threadId','turnId','itemId','startedAtMs','approvalId'}


def describe(value,label):
    """Readable fallback for new fields, retaining every value without JSON."""
    if isinstance(value,dict):
        result=[label+dt('：')]
        for key,child in value.items():result.extend(describe(child,LABELS.get(key,dt('其他参数 ')+key)))
        if not value:result.append(dt('无'))
        return result
    if isinstance(value,list):
        result=[label+'('+device_string(len(value))+dt('项)：')]
        for index,child in enumerate(value,1):result.extend(describe(child,device_string(index)))
        return result
    text=dt('未提供') if value is None else dt('是') if value is True else dt('否') if value is False else device_string(value)
    return [label+dt('：')+text]


def permission_lines(profile):
    result=[]
    network=profile.get('network')
    if isinstance(network,dict) and set(network)=={'enabled'}:
        if network['enabled'] is True:result.append(dt('网络：申请联网'))
        elif network['enabled'] is False:result.append(dt('网络：不申请联网'))
        else:result.append(dt('网络：未指定'))
    elif network is not None:result.extend(describe(network,dt('网络权限')))
    fs=profile.get('fileSystem')
    if isinstance(fs,dict):
        for key,label in (('read',dt('申请读取')),('write',dt('申请写入'))):
            values=fs.get(key)
            if values is not None:result.extend(describe(values,label))
        entries=fs.get('entries')
        if isinstance(entries,list):
            for index,entry in enumerate(entries,1):
                if not isinstance(entry,dict):result.extend(describe(entry,dt('路径规则 ')+device_string(index)));continue
                access={'read':dt('申请读取'),'write':dt('申请写入'),'deny':dt('拒绝访问')}.get(entry.get('access'),dt('访问方式 ')+device_string(entry.get('access')))
                path=entry.get('path')
                if isinstance(path,dict) and path.get('type')=='path' and set(path)=={'type','path'}:
                    result.append(access+dt('：')+device_string(path['path']))
                elif isinstance(path,dict) and path.get('type')=='glob_pattern' and set(path)=={'type','pattern'}:
                    result.append(access+dt('匹配路径：')+device_string(path['pattern']))
                else:
                    result.append(access)
                    result.extend(describe(path,dt('路径范围')))
                for key,child in entry.items():
                    if key not in ('access','path'):result.extend(describe(child,dt('其他参数 ')+key))
        elif entries is not None:result.extend(describe(entries,dt('路径规则')))
        for key,child in fs.items():
            if key not in ('read','write','entries'):result.extend(describe(child,LABELS.get(key,dt('其他参数 ')+key)))
    elif fs is not None:result.extend(describe(fs,dt('文件权限')))
    for key,child in profile.items():
        if key not in ('network','fileSystem'):result.extend(describe(child,dt('其他权限 ')+key))
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
        lines.append(dt('请求新增以下权限'))
        lines.extend(permission_lines(profile) if isinstance(profile,dict) else describe(profile,dt('权限范围')))
    elif command:
        lines.extend([dt('请求执行以下命令'),device_string(params.get('command') or dt('未提供命令'))])
        if params.get('kind')=='writeStdin':lines.append(dt('操作：向运行中的终端输入内容'))
    else:
        lines.extend([dt('请求修改文件'),dt('未提供修改明细，请在 PC 端审阅。')])
    if params.get('reason'):lines.extend([dt('申请原因：'),device_string(params['reason'])])
    if params.get('cwd'):lines.extend([dt('工作目录：'),device_string(params['cwd'])])
    if params.get('environmentId') is not None:lines.extend(describe(params['environmentId'],dt('执行环境')))
    if params.get('networkApprovalContext') is not None:
        lines.extend(describe(params['networkApprovalContext'],dt('网络连接范围')))
    handled=OPAQUE|{'reason','cwd','environmentId','networkApprovalContext'}
    if permission:handled.add('permissions')
    if command:
        handled|={'command','commandActions','proposedExecpolicyAmendment',
                  'proposedNetworkPolicyAmendments','availableDecisions'}
    if command and params.get('kind','command') in ('command','writeStdin'):handled.add('kind')
    for key,value in params.items():
        if key not in handled:lines.extend(describe(value,LABELS.get(key,dt('其他参数 ')+key)))
    lines.extend([dt('授权有效期：'),scope])
    return localized_join('\n',lines)


def hook_text(event):
    lines=[dt('请求执行以下操作'),device_string(event.get('tool_name') or dt('未命名操作'))]
    if event.get('cwd'):lines.extend([dt('工作目录：'),device_string(event['cwd'])])
    args=event.get('tool_input')
    if isinstance(args,dict):
        for key,value in args.items():
            if key in ('command','cmd'):lines.extend([dt('执行命令：'),device_string(value)])
            elif key in ('description','justification'):lines.extend([dt('申请原因：'),device_string(value)])
            else:lines.extend(describe(value,LABELS.get(key,dt('操作参数 ')+key)))
    else:lines.extend(describe(args,dt('操作内容')))
    lines.append(dt('仅本次操作，不保存长期权限'))
    return localized_join('\n',lines)


def native_view(method, params, language="zh-CN"):
    """Exact native request and one-shot response, independent of text length."""
    permission = method == 'item/permissions/requestApproval'
    command = method == 'item/commandExecution/requestApproval'
    title = dt('权限申请') if permission else dt('命令执行审批') if command else dt('文件修改审批')
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
        scope = dt('仅本轮，不保存长期权限')
        title = dt('目录与网络权限') if grant.get('network') and grant.get('fileSystem') else dt('目录权限请求') if grant.get('fileSystem') else dt('网络权限请求') if grant.get('network') else title
    else:
        allow = {'decision': 'accept'}
        deny = {'decision': 'decline'}
        # File approval callbacks do not include the diff. Keep them reviewable
        # and deniable here; do not present missing changes as a complete review.
        allowed = command and isinstance(params.get('command'), str) and bool(params['command'])
        if command and params.get('kind','command') not in ('command','writeStdin'):allowed=False
        # Unknown extra-grant semantics remain on PC 端 until supported explicitly.
        if params.get('additionalPermissions') is not None:
            allowed = False
        decisions = params.get('availableDecisions')
        if decisions is not None and (not isinstance(decisions, list) or 'accept' not in decisions):
            allowed = False
        scope = dt('仅本次操作，不记住批准')
    body = native_text(method,params,scope)
    return {'command': title, 'project': '', 'scope': scope,
            'can_allow': allowed, 'can_deny': True,
            'allow_result': allow, 'deny_result': deny,
            'review_pages': pages(body, language)}
