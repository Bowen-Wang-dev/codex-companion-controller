"""Incrementally read numeric completed-response records from local Codex rollouts.

The installed Codex version records compaction responses here even when the
normal thread/tokenUsage event omits them. This is a version-dependent local
supplement, not a provider billing API. No prompts or response text are retained.
"""
import datetime
import hashlib
import json
import os
from pathlib import Path
import re

from usage_meter import TOKEN_FIELDS, breakdown

FIELDS = ('input_tokens', 'cached_input_tokens', 'cache_write_input_tokens',
          'output_tokens', 'reasoning_output_tokens', 'total_tokens')
THREAD = re.compile(r'[0-9a-fA-F-]{36}\Z')
MAX_LINE = 2 * 1024 * 1024
READ_BUDGET = 8 * 1024 * 1024


class ResponseUsageReader:
    def __init__(self, directory=None):
        home = Path(os.environ.get('CODEX_HOME') or Path.home() / '.codex')
        self.directory = Path(directory or home / 'sessions').resolve()
        self.files = {}
        self.issue = ''
        self.missing = set()
        self.records = {}

    def _find(self, thread):
        # The Bridge's attached session IDs cannot become arbitrary file paths.
        if not isinstance(thread, str) or not THREAD.fullmatch(thread):
            return None
        paths = self.directory.glob('*/*/*/rollout-*' + thread + '.jsonl')
        for path in paths:
            resolved = path.resolve()
            if self.directory in resolved.parents and not path.is_symlink():
                return path
        return None

    def read(self, threads):
        records = []
        for thread in sorted(set(threads))[:256]:
            state = self.files.get(thread)
            path = state['path'] if state else self._find(thread)
            if path is None:
                if isinstance(thread,str) and THREAD.fullmatch(thread):self.missing.add(thread)
                continue
            self.missing.discard(thread)
            try:
                info = path.stat()
                signature = (info.st_dev, info.st_ino)
                if not state or state['file'] != signature or info.st_size < state['offset']:
                    state = {'path': path, 'file': signature, 'offset': 0,
                             'models': {}, 'model': '', 'skip': False, 'verified': False}
                    self.files[thread] = state
                with path.open('rb') as stream:
                    stream.seek(state['offset'])
                    start = stream.tell()
                    while stream.tell() - start < READ_BUDGET:
                        position = stream.tell()
                        line = stream.readline(MAX_LINE + 1)
                        if not line:
                            break
                        if len(line) > MAX_LINE or state['skip']:
                            state['skip'] = not line.endswith(b'\n')
                            state['offset'] = stream.tell()
                            continue
                        if not line.endswith(b'\n'):
                            # A concurrent append may leave a partial last line.
                            state['offset'] = position
                            break
                        state['offset'] = stream.tell()
                        if not any(name in line for name in (b'"session_meta"', b'"turn_context"', b'"token_usage_record"')):
                            continue
                        try:
                            event = json.loads(line)
                            kind = event.get('type')
                            value = event.get('payload') or {}
                            if kind == 'session_meta':
                                state['verified'] = value.get('id') == thread
                            if not state['verified']:
                                continue
                            if kind == 'turn_context':
                                model = value.get('model')
                                if isinstance(model, str) and len(model) <= 96:
                                    state['model'] = model
                                    state['models'][value.get('turn_id')] = model
                                continue
                            if kind != 'token_usage_record' or value.get('thread_id') != thread:
                                continue
                            usage = value.get('usage')
                            if not isinstance(usage, dict):
                                continue
                            normalized = breakdown(dict(zip(TOKEN_FIELDS, (usage.get(k, 0) for k in FIELDS))))
                            response = value.get('response_id')
                            turn = value.get('turn_id')
                            if (normalized is None or not isinstance(response, str) or not response or
                                    len(response) > 256 or not isinstance(turn, str) or not turn or len(turn) > 128):
                                continue
                            at = datetime.datetime.fromisoformat(event['timestamp'].replace('Z', '+00:00'))
                            if at.tzinfo is None:
                                continue
                            records.append({'thread': thread, 'turn': turn, 'at': at.timestamp(),
                                'id': hashlib.sha256((thread + '\0' + response).encode()).hexdigest(),
                                'model': state['models'].get(turn, ''), 'usage': normalized})
                        except (ValueError, TypeError, KeyError, AttributeError):
                            self.issue = 'response_record_invalid'
            except OSError:
                self.issue = 'response_file_unavailable'
        for record in records:
            if len(self.records)<100000 or record['id'] in self.records:
                self.records[record['id']]=record
        if self.missing and not self.issue:self.issue='response_file_unavailable'
        elif not self.missing and self.issue=='response_file_unavailable':self.issue=''
        return records
