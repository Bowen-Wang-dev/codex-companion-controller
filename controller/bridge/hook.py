#!/usr/bin/env python3
"""Official lifecycle hook client. Fail back to native approval on every error."""
import json
from pathlib import Path
import socket
import sys
from ipc_path import check_directory
from permission_result import permission_outcome
from hook_policy import permission_tool


def main():
    try:
        raw = sys.stdin.buffer.read(65537)
        if len(raw) > 65536:
            return
        event = json.loads(raw)
        outcome=permission_outcome(event)
        # Never forward prompt bodies or tool outputs to the display broker.
        event = {k: v for k, v in event.items() if k in (
            'hook_event_name', 'session_id', 'turn_id', 'cwd', 'tool_name', 'tool_input', 'tool_use_id')}
        if outcome:event['permission_outcome']=outcome
        event['passport_hook_version']=3
        address = check_directory()
        with socket.socket(socket.AF_UNIX) as sock:
            blocking=event.get('hook_event_name')=='PermissionRequest' or (event.get('hook_event_name')=='PreToolUse' and permission_tool(event))
            sock.settimeout(112 if blocking else .5)
            sock.connect(str(address))
            sock.sendall(json.dumps(event).encode() + b'\n')
            with sock.makefile('rb') as f:
                result = json.loads(f.readline(4096))
            # PermissionRequest can decide an approval. PreToolUse can block
            # the permission tool, but can never grant its requested scope.
            out = result.get('hookSpecificOutput', {})
            if event.get('hook_event_name') == 'PermissionRequest' and out.get('decision', {}).get('behavior') in ('allow','deny'):
                print(json.dumps(result))
                return
            if event.get('hook_event_name')=='PreToolUse' and permission_tool(event) and out.get('hookEventName')=='PreToolUse' and out.get('permissionDecision')=='deny':
                print(json.dumps(result));return
    except (ValueError, OSError, TypeError, AttributeError):
        pass
    print('{}')


if __name__ == '__main__':
    main()
