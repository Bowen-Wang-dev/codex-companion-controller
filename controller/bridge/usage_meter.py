"""Validate App Server token totals and local per-model price cards.

The controller never receives model credentials, raw prompts, or response text.
Only numeric usage breakdowns and the selected model label reach the device.
"""
import json
import math
from pathlib import Path

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
    if result['reasoningOutputTokens'] > result['outputTokens']:
        return None
    if result['totalTokens'] < result['inputTokens'] + result['outputTokens']:
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
    uncached = max(0, tokens['inputTokens'] - tokens['cachedInputTokens'])
    amount = uncached * rates['input'] + tokens['cachedInputTokens'] * rates['cached_input']
    amount += tokens['outputTokens'] * rates['output']
    if write_tokens:
        amount += write_tokens * write_rate
    return amount / 1_000_000
