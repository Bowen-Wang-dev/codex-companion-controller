"""Validate App Server token totals and local per-model price cards.

The controller never receives model credentials, raw prompts, or response text.
Only numeric usage breakdowns and the selected model label reach the device.
"""
import json
import math
import os
from pathlib import Path
import time
import uuid

TOKEN_FIELDS = (
    'inputTokens', 'cachedInputTokens', 'cacheWriteInputTokens',
    'outputTokens', 'reasoningOutputTokens', 'totalTokens',
)
MAX_TOKENS = 10**12


def breakdown(value):
    if not isinstance(value, dict):
        return None
    result = {}
    for key in TOKEN_FIELDS:
        amount = value.get(key, 0 if key == 'cacheWriteInputTokens' else None)
        if type(amount) is not int or not 0 <= amount <= MAX_TOKENS:
            return None
        result[key] = amount
    if result['cachedInputTokens'] > result['inputTokens']:
        return None
    if result['cachedInputTokens'] + result['cacheWriteInputTokens'] > result['inputTokens']:
        return None
    if result['reasoningOutputTokens'] > result['outputTokens']:
        return None
    if result['totalTokens'] != result['inputTokens'] + result['outputTokens']:
        return None
    return result


def normalize_notification(params):
    if not isinstance(params, dict):
        return None
    thread = params.get('threadId')
    turn = params.get('turnId')
    usage = params.get('tokenUsage')
    if not isinstance(thread, str) or not thread or len(thread) > 128:
        return None
    if not isinstance(turn, str) or not turn or len(turn) > 128:
        return None
    if not isinstance(usage, dict):
        return None
    last = breakdown(usage.get('last'))
    total = breakdown(usage.get('total'))
    if last is None or total is None:
        return None
    if difference(total, last) is None:
        return None
    context = usage.get('modelContextWindow')
    if type(context) is not int or not 0 <= context <= MAX_TOKENS:
        context = None
    return {'thread': thread, 'turn': turn, 'last': last, 'total': total,
            'context_window': context}


def _price(value):
    if type(value) not in (int, float) or not math.isfinite(value) or value < 0 or value > 1_000_000:
        return None
    return float(value)


def load_rates(path):
    """Read local rates: {currency, models: {id: {input,cached_input,output,cache_write}}}."""
    try:
        data = json.loads(Path(path).read_text())
    except (OSError, ValueError, TypeError):
        return {'currency': '', 'models': {}}
    if not isinstance(data, dict) or not isinstance(data.get('models'), dict):
        return {'currency': '', 'models': {}}
    currency = data.get('currency')
    if not isinstance(currency, str) or not currency.isascii() or not 1 <= len(currency) <= 8:
        currency = ''
    models = {}
    for model, rates in data['models'].items():
        if not isinstance(model, str) or not 1 <= len(model) <= 96 or not isinstance(rates, dict):
            continue
        normalized = {key: _price(rates.get(key)) for key in ('input', 'cached_input', 'output', 'cache_write')}
        # An estimate is only enabled when all standard token types have rates.
        if all(normalized[k] is not None for k in ('input', 'cached_input', 'output')):
            models[model] = normalized
    return {'currency': currency, 'models': models}


def estimate(tokens, rates):
    """Return None when a billed token type has no configured rate."""
    if not isinstance(tokens, dict) or not isinstance(rates, dict):
        return None
    write_tokens = tokens.get('cacheWriteInputTokens', 0)
    write_rate = rates.get('cache_write')
    if write_tokens and write_rate is None:
        return None
    uncached = max(0, tokens['inputTokens'] - tokens['cachedInputTokens'] - write_tokens)
    amount = uncached * rates['input'] + tokens['cachedInputTokens'] * rates['cached_input']
    amount += tokens['outputTokens'] * rates['output']
    if write_tokens:
        amount += write_tokens * write_rate
    return amount / 1_000_000


def zero():
    return dict.fromkeys(TOKEN_FIELDS, 0)


def plus(left, right):
    return {key: left[key] + right[key] for key in TOKEN_FIELDS}


def difference(current, previous):
    result = {key: current[key] - previous[key] for key in TOKEN_FIELDS}
    return breakdown(result)


def rate_for(book, model):
    """Match full model IDs, never silently substitute a related model's price."""
    rows = book.get('models', {})
    model = model.strip() if isinstance(model, str) else ''
    if model in rows:
        return rows[model]
    # Whitespace/case are spelling, not permission to merge model variants.
    matches = [rates for name, rates in rows.items() if name.strip().casefold() == model.casefold()]
    return matches[0] if model and len(matches) == 1 else None


def private_json(path, data):
    path = Path(path)
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    with temporary.open('w', encoding='utf-8') as stream:
        os.chmod(temporary, 0o600)
        json.dump(data, stream, ensure_ascii=False, separators=(',', ':'))
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


class UsageLedger:
    """Count cumulative deltas once; keep turns, models and local resets separate.

    App Server 'last' describes one response, not one user turn. The first
    observed response is counted; pre-observation history is never assigned
    today's model price. Thread totals remain a replay baseline, including
    after a local reset. Only numeric counters/model IDs are persisted.
    """
    def __init__(self, path=None):
        self.path = Path(path) if path else None
        self.reset_id = str(uuid.uuid4())
        self.reset_at = int(time.time())
        self.groups = {}
        self.threads = {}
        self.turns = {}
        self.active_thread = ''
        self.response_turns = {}
        self.provider_turns = {}
        self.unassigned = {}
        self.response_ids = set()
        self.response_revision = 0
        self._effective_cache = None
        self.issue = ''
        self.blocked = False
        self._load()

    def _load(self):
        if not self.path or not self.path.exists():
            return
        try:
            saved = json.loads(self.path.read_text())
            if saved.get('version') not in (1, 2) or not isinstance(saved.get('reset_id'), str):
                raise ValueError('Unsupported ledger')
            groups = saved['groups']
            threads = saved['threads']
            turns = saved['turns']
            if not isinstance(groups, dict) or not isinstance(threads, dict) or not isinstance(turns, dict):
                raise ValueError('Malformed ledger')
            if len(threads) > 256 or len(turns) > 4096 or len(groups) > 256:
                raise ValueError('Ledger limit')
            def valid_groups(rows):
                return isinstance(rows, dict) and all(isinstance(k, str) and len(k) <= 96 and breakdown(v) is not None for k, v in rows.items())
            def valid_turn(key):
                try:
                    parts=json.loads(key)
                    return isinstance(parts,list) and len(parts)==2 and all(isinstance(v,str) and len(v)<=128 for v in parts)
                except (TypeError,ValueError):return False
            if not valid_groups(groups):
                raise ValueError('Malformed groups')
            for key, value in threads.items():
                if not isinstance(key, str) or not isinstance(value, dict) or breakdown(value['total']) is None:
                    raise ValueError('Malformed baseline')
            for key, value in turns.items():
                if not valid_turn(key) or not valid_groups(value):
                    raise ValueError('Malformed turn')
            response_turns = saved.get('response_turns', {})
            response_ids = saved.get('response_ids', [])
            provider_turns = saved.get('provider_turns', {})
            unassigned = saved.get('unassigned', {})
            if (not isinstance(response_turns, dict) or len(response_turns) > 4096 or
                    not all(valid_turn(k) and valid_groups(v) for k, v in response_turns.items()) or
                    not isinstance(response_ids, list) or len(response_ids) > 100000 or
                    not all(isinstance(k, str) and len(k) == 64 for k in response_ids)):
                raise ValueError('Malformed response accounting')
            if (not isinstance(provider_turns,dict) or len(provider_turns)>4096 or
                    not all(valid_turn(k) and valid_groups(v) for k,v in provider_turns.items())):
                raise ValueError('Malformed billing supplement')
            if (not isinstance(unassigned,dict) or len(unassigned)>256 or
                    not all(isinstance(k,str) and valid_groups(v) for k,v in unassigned.items())):
                raise ValueError('Malformed unassigned counters')
            self.groups, self.threads, self.turns = groups, threads, turns
            self.response_turns, self.response_ids = response_turns, set(response_ids)
            self.provider_turns = provider_turns
            self.unassigned = unassigned
            self.reset_id = saved['reset_id']
            self.reset_at = float(saved['reset_at'])
            if not math.isfinite(self.reset_at) or self.reset_at<0:raise ValueError('Invalid reset boundary')
            self.active_thread = str(saved.get('active_thread', ''))
        except (OSError, ValueError, TypeError, KeyError):
            self.issue = 'ledger_unreadable'
            self.blocked = True

    def save(self):
        if self.path:
            try:
                private_json(self.path, {'version': 2, 'reset_id': self.reset_id,
                    'reset_at': self.reset_at, 'groups': self.groups,
                    'threads': self.threads, 'turns': self.turns,
                    'response_turns': self.response_turns, 'response_ids': sorted(self.response_ids),
                    'provider_turns': self.provider_turns,
                    'unassigned': self.unassigned,
                    'active_thread': self.active_thread})
            except OSError:
                self.issue = 'ledger_save_failed'
                return False
        return True

    @staticmethod
    def turn_key(thread, turn):
        return json.dumps([thread, turn], separators=(',', ':'))

    def begin_turn(self, thread, turn):
        if not isinstance(thread, str) or not isinstance(turn, str) or not turn:
            return
        self.active_thread = thread
        self.turns.setdefault(self.turn_key(thread, turn), {})
        self._bound()

    def _bound(self):
        # Retain per-turn fallback counts: response reconciliation must subtract
        # the exact fallback, even for old turns. Never evict a counted baseline.
        if len(self.turns) > 4096:
            self.issue = 'turn_limit'
        # Keep counted threads' baselines. Dropping a baseline would count a
        # replay twice; fail explicitly instead of evicting accounting state.

    def _record(self, model, tokens, turn_key=None, thread=None):
        if not tokens['totalTokens']:
            return
        if model not in self.groups and len(self.groups) >= 255:
            model = ''
        self.groups[model] = plus(self.groups.get(model, zero()), tokens)
        self._effective_cache = None
        if turn_key:
            rows = self.turns.setdefault(turn_key, {})
            rows[model] = plus(rows.get(model, zero()), tokens)
        elif thread:
            rows = self.unassigned.setdefault(thread, {})
            rows[model] = plus(rows.get(model,zero()),tokens)

    def observe(self, value, model='', baseline_only=False):
        if self.blocked:
            return False
        thread, turn = value['thread'], value['turn']
        current, last = value['total'], value['last']
        old = self.threads.get(thread)
        model = model.strip()[:96] if isinstance(model, str) else ''
        if old and current == old['total']:
            return False
        if old is None and len(self.threads) >= 256:
            self.issue = 'thread_limit'
            return False
        if self.turn_key(thread, turn) not in self.turns and len(self.turns) >= 4096:
            self.issue = 'turn_limit'
            return False
        if baseline_only and old is None:
            self.threads[thread] = {'total':dict(current),'turn':turn,'model':model,
                                   'context_window':value['context_window']}
            self.active_thread=thread
            self.save()
            # Initial attach replays history, not new spend. For an existing
            # baseline, however, a larger replay can recover a dropped final
            # event. Let the normal cumulative-delta path below account for it.
            return False
        delta = difference(current, old['total']) if old else last
        if delta is None:
            # Counter regressions can be compaction/restore/replay, not spend.
            # Keep the high-water baseline; a restart must not duplicate spend.
            self.issue = 'counter_regressed'
            return False
        key = self.turn_key(thread, turn)
        if old and (old.get('model', '') != model or old.get('turn') != turn) and delta != last:
            remainder = difference(delta, last)
            if remainder is not None:
                self._record(model, last, key)
                # Missing events across a model/turn boundary cannot be priced
                # reliably. Preserve the count with an explicitly unknown model.
                self._record(model if old.get('model')==model else '', remainder, thread=thread)
            else:
                self._record('', delta, thread=thread)
        else:
            self._record(model, delta, key)
        self.threads[thread] = {'total': dict(current), 'turn': turn, 'model': model,
                                'context_window': value['context_window']}
        self.active_thread = thread
        if self.issue == 'counter_regressed':
            self.issue = ''
        self._bound()
        self.save()
        return True

    def clear(self, expected_id):
        if expected_id != self.reset_id:
            return False
        previous=(self.groups,self.turns,self.reset_id,self.reset_at,self.issue,self.blocked,
                  self.response_turns,self.response_ids,self.provider_turns,self.unassigned)
        self.groups = {}
        self.turns = {key: {} for key in self.turns}
        self.response_turns = {}
        self.response_ids = set()
        self.provider_turns = {}
        self.unassigned = {}
        self._effective_cache = None
        # Keep raw cumulative baselines, so the next duplicate/heartbeat cannot
        # restore the old displayed count. Does not touch Codex/provider usage.
        self.reset_id = str(uuid.uuid4())
        self.reset_at = time.time()
        self.issue = ''
        self.blocked = False
        if not self.save():
            (self.groups,self.turns,self.reset_id,self.reset_at,_,self.blocked,
             self.response_turns,self.response_ids,self.provider_turns,self.unassigned)=previous
            self.issue='ledger_save_failed'
            return False
        return True

    def observe_responses(self, records):
        """Reconcile completed response records, including compaction calls.

        These counters and normal App Server totals have different histories.
        Never subtract one cumulative source from the other or add both sums.
        Keep sources separate and replace only a fully covered per-turn fallback.
        """
        if self.blocked:
            return False
        changed = False
        for record in records:
            if record['at'] < self.reset_at or record['id'] in self.response_ids:
                continue
            key = self.turn_key(record['thread'], record['turn'])
            if (len(self.response_ids) >= 100000 or
                    (key not in self.response_turns and len(self.response_turns) >= 4096)):
                self.issue = 'response_limit'
                break
            rows = self.response_turns.setdefault(key, {})
            model = record['model']
            rows[model] = plus(rows.get(model, zero()), record['usage'])
            self.response_ids.add(record['id'])
            changed = True
        if changed:
            self.response_revision += 1
            self._effective_cache = None
            self.save()
        return changed

    def reconcile_provider(self, records):
        if self.blocked:
            return False
        groups={}
        for record in records:
            if record['at']<self.reset_at:
                continue
            key=self.turn_key(record['thread'],record['turn']);model=record['model']
            rows=groups.setdefault(key,{})
            rows[model]=plus(rows.get(model,zero()),record['usage'])
        if groups==self.provider_turns:
            return False
        self.provider_turns=groups
        self._effective_cache=None
        self.save()
        return True

    def effective(self, key=None):
        """Return reconciled groups without changing App Server replay baselines."""
        if self._effective_cache is not None:
            groups, turns, correction = self._effective_cache
            return groups, turns.get(key, self.turns.get(key, {})), correction
        groups = {m: dict(v) for m, v in self.groups.items()}
        turns = {}
        correction = zero()
        response_turns={key:{m:dict(v) for m,v in rows.items()} for key,rows in self.response_turns.items()}
        for key,rows in self.provider_turns.items():
            target=response_turns.setdefault(key,{})
            for model,usage in rows.items():target[model]=plus(target.get(model,zero()),usage)
        fallback_threads={thread:{m:dict(v) for m,v in rows.items()} for thread,rows in self.unassigned.items()}
        record_threads={}
        def merge(target,rows):
            for model,tokens in rows.items():target[model]=plus(target.get(model,zero()),tokens)
        for turn_key,rows in self.turns.items():
            thread=json.loads(turn_key)[0]
            merge(fallback_threads.setdefault(thread,{}),rows)
        assigned={}
        for rows in fallback_threads.values():merge(assigned,rows)
        legacy={m:difference(v,assigned.get(m,zero())) for m,v in self.groups.items()}
        legacy={m:v for m,v in legacy.items() if v and v['totalTokens']}
        if legacy and len(self.threads)==1:
            # Old v1 files did not retain the thread for cross-turn gaps.
            # A single known thread is unambiguous; multiple threads are not.
            merge(fallback_threads.setdefault(next(iter(self.threads)),{}),legacy)
        for turn_key,records in response_turns.items():
            thread=json.loads(turn_key)[0]
            merge(record_threads.setdefault(thread,{}),records)
            fallback = self.turns.get(turn_key, {})
            delta = difference(self.aggregate(records), self.aggregate(fallback))
            if delta is not None:turns[turn_key]=records
        for thread,records in record_threads.items():
            if legacy and len(self.threads)!=1:
                self.issue='legacy_unattributed'
                continue
            fallback=fallback_threads.get(thread,{})
            delta=difference(self.aggregate(records),self.aggregate(fallback))
            if delta is None:continue
            remainder = {m: dict(v) for m, v in groups.items()}
            for model, tokens in fallback.items():
                rest = difference(remainder.get(model, zero()), tokens)
                if rest is None:
                    break
                remainder[model] = rest
            else:
                for model, tokens in records.items():
                    remainder[model] = plus(remainder.get(model, zero()), tokens)
                groups = remainder
                correction = plus(correction, delta)
        self._effective_cache = groups, turns, correction
        return groups, turns.get(key, self.turns.get(key, {})), correction

    @staticmethod
    def aggregate(groups):
        result = zero()
        for value in groups.values():
            result = plus(result, value)
        return result

    @staticmethod
    def cost(groups, book, fallback_model):
        if not groups:
            return (0.0, '') if rate_for(book, fallback_model) else (None, 'model_rate_missing' if fallback_model else 'model_unknown')
        amount = 0.0
        for model, tokens in groups.items():
            if not tokens['totalTokens']:
                continue
            if not model:
                return None, 'model_unknown'
            rates = rate_for(book, model)
            if not rates:
                return None, 'model_rate_missing'
            part = estimate(tokens, rates)
            if part is None:
                return None, 'cache_write_rate_missing'
            amount += part
        return amount, ''

    def view(self, thread, turn, model, book):
        baseline = self.threads.get(thread, {})
        turn = turn or baseline.get('turn', '')
        groups, rows, correction = self.effective(self.turn_key(thread, turn))
        configured = rate_for(book, model) is not None
        last_cost, last_reason = self.cost(rows, book, model)
        total_cost, total_reason = self.cost(groups, book, model)
        known = bool(baseline) or bool(rows)
        return {'usage': {'last': self.aggregate(rows) if known else None,
                'total': self.aggregate(groups) if self.threads or self.response_turns else None,
                'context_window': baseline.get('context_window'), 'model': model,
                'updated': known, 'total_updated': bool(self.threads or self.response_turns),
                'meter_id': self.reset_id, 'reset_at': self.reset_at,
                'scope': 'since_reset', 'turn': turn, 'issue': self.issue,
                'source': 'response_records+provider_export' if self.provider_turns else 'response_records' if self.response_turns else 'app_server',
                'recovered_tokens': correction['totalTokens'], 'account_wide': False,
                'input_includes_cache': True, 'output_includes_reasoning': True},
            'cost': {'currency': book['currency'], 'last': last_cost if known else None,
                'total': total_cost if self.threads or self.response_turns else None, 'priced': configured,
                'status': ('waiting_usage' if not known and configured else
                           last_reason or total_reason or 'ready'),
                'last_status': last_reason or ('ready' if known else 'waiting_usage'),
                'total_status': total_reason or 'ready', 'rate_model': model,
                'known_models': sorted(book['models'])}}
