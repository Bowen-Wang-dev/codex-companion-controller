"""Official Codex account client: reads usage; consumes only via explicit consume_once. Never opens a thread."""
import hashlib
import json
import os
import queue
import shutil
import subprocess
import threading


class AccountClient:
    def __init__(self, binary=None):
        binary = binary or os.environ.get('COMPANION_CODEX') or shutil.which('codex')
        if not binary:
            raise RuntimeError('Codex CLI not found; set COMPANION_CODEX to its executable')
        self.process = subprocess.Popen([binary, 'app-server', '--stdio'], stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        self.messages = queue.Queue()
        self.counter = 0
        threading.Thread(target=self._read, daemon=True).start()
        try:
            self.rpc('initialize', {'clientInfo': {'name': 'passport_usage', 'version': '0.1.0'},
                                    'capabilities': None})
        except Exception:
            self.close()
            raise
        self.process.stdin.write(json.dumps({'method': 'initialized'}) + '\n')
        self.process.stdin.flush()

    def _read(self):
        for line in self.process.stdout:
            try:
                self.messages.put(json.loads(line))
            except ValueError:
                pass
        self.messages.put({'fatal': True})

    def rpc(self, method, params=None, timeout=30):
        if method not in {'initialize', 'account/read', 'account/rateLimits/read'}:
            raise ValueError('This provider is read-only')
        return self._rpc(method,params,timeout)

    def consume_once(self, idempotency_key):
        if not isinstance(idempotency_key,str) or len(idempotency_key)!=36: raise ValueError('UUID required')
        return self._rpc('account/rateLimitResetCredit/consume',{'idempotencyKey':idempotency_key})

    def _rpc(self, method, params=None, timeout=30):
        self.counter += 1
        request_id = self.counter
        self.process.stdin.write(json.dumps({'id': request_id, 'method': method, 'params': params}) + '\n')
        self.process.stdin.flush()
        import time
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            message = self.messages.get(timeout=max(.01, deadline - time.monotonic()))
            if message.get('fatal'):
                raise RuntimeError('Codex exited; verify CLI permissions and login status')
            if message.get('id') != request_id:
                continue
            if 'error' in message:
                raise RuntimeError('Codex RPC failed: ' + str(message['error'].get('code', 'unknown')))
            return message['result']
        raise TimeoutError(method)

    def read(self):
        account = self.rpc('account/read', {'refreshToken': False}).get('account')
        if not account or account.get('type') != 'chatgpt':
            raise RuntimeError('ChatGPT login required. Run codex login on the Mac; API keys use different billing.')
        usage = self.rpc('account/rateLimits/read')
        self.account_binding=hashlib.sha256(str(usage.get('accountId') or account.get('email') or '').encode()).hexdigest() if (usage.get('accountId') or account.get('email')) else None
        # Only forward display data, never email, account IDs, credit IDs or tokens.
        buckets = usage.get('rateLimitsByLimitId')
        if buckets:
            entries = list(buckets.items())
        else:
            legacy = usage.get('rateLimits') or {}
            entries = [(legacy.get('limitId') or 'codex', legacy)]
        limits = []
        for key, bucket in entries:
            for role in ('primary', 'secondary'):
                window = bucket.get(role)
                if not window:
                    continue
                used = window.get('usedPercent')
                limits.append({'bucket': key, 'role': role,
                               'remaining': max(0, min(100, 100 - used)) if isinstance(used, (int, float)) else None,
                               'minutes': window.get('windowDurationMins'), 'resets': window.get('resetsAt')})
        return {'auth': 'chatgpt', 'plan': account.get('planType'), 'limits': limits,
                'resets': (usage.get('rateLimitResetCredits') or {}).get('availableCount'),
                'ordinaryUsageAllowed': usage.get('ordinaryUsageAllowed')}

    def close(self):
        self.process.terminate()
        try:
            self.process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait()


if __name__ == '__main__':
    client = AccountClient()
    try:
        print(json.dumps(client.read(), ensure_ascii=False, indent=2))
    finally:
        client.close()
