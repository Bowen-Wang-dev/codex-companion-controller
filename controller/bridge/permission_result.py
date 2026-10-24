"""Reduce documented PostToolUse.tool_response to an outcome, never raw output."""
import json


def permission_outcome(event):
    if event.get('hook_event_name')!='PostToolUse':return None
    tool=str(event.get('tool_name','')).rsplit('.',1)[-1].rsplit('__',1)[-1]
    if tool!='request_permissions':return None
    args=event.get('tool_input');response=event.get('tool_response')
    if isinstance(response,str):
        try:response=json.loads(response)
        except ValueError:return None
    if not isinstance(args,dict) or not isinstance(response,dict):return None
    requested=args.get('permissions');granted=response.get('permissions')
    if not isinstance(requested,dict) or not isinstance(granted,dict):return None
    if set(requested)-{'network','file_system'}:return None
    tests=[];any_received=False
    network=requested.get('network')
    if network is not None:
        if not isinstance(network,dict) or network.get('enabled') is not True:return None
        tests.append(isinstance(granted.get('network'),dict) and granted['network'].get('enabled') is True)
        any_received=tests[-1]
    fs=requested.get('file_system')
    if fs is not None:
        if not isinstance(fs,dict) or set(fs)-{'read','write'}:return None
        actual=granted.get('file_system') or {}
        if not isinstance(actual,dict):return None
        for mode in ('read','write'):
            paths=fs.get(mode) or []
            received=actual.get(mode) or []
            if not isinstance(paths,list) or not isinstance(received,list):return None
            if any(not isinstance(p,str) for p in paths+received):return None
            any_received=any_received or bool(received)
            if paths:tests.append(set(paths)<=set(received))
    if not tests:return None
    return 'granted' if all(tests) else 'partial' if any_received else 'denied'
