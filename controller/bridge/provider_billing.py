"""Read provider-exported CSV/TSV locally; never infer missing billed usage.

Only numeric usage, model and timestamp survive parsing. API key names, IPs and
endpoints are deliberately excluded from stored reports and device transport.
Provider input tokens here mean uncached input, unlike Responses input_tokens.
"""
import csv
import datetime
from decimal import Decimal, InvalidOperation
import hashlib
import io

from usage_meter import breakdown, estimate, plus, rate_for, zero


def parse_export(text):
    first = text.splitlines()[0] if text.splitlines() else ''
    delimiter = '\t' if '\t' in first else ','
    rows = csv.DictReader(io.StringIO(text.lstrip('\ufeff')), delimiter=delimiter)
    required={'Time','Model','Input Tokens','Output Tokens','Cache Read Tokens',
              'Cache Creation Tokens','Billed Cost'}
    if not required.issubset(rows.fieldnames or []):
        raise ValueError('后台明细缺少时间、模型、Token 或 Billed Cost 列')
    result=[];seen=set()
    for index,row in enumerate(rows,2):
        if not any(row.values()):continue
        try:
            at=datetime.datetime.fromisoformat(row['Time'].replace('Z','+00:00'))
            if at.tzinfo is None:raise ValueError('Timezone required')
            uncached,output,cached,write=(int(row[k]) for k in ('Input Tokens','Output Tokens','Cache Read Tokens','Cache Creation Tokens'))
            usage=breakdown({'inputTokens':uncached+cached+write,'cachedInputTokens':cached,
                'cacheWriteInputTokens':write,'outputTokens':output,
                'reasoningOutputTokens':0,'totalTokens':uncached+cached+write+output})
            cost=Decimal(row['Billed Cost'])
            model=row['Model'].strip()
            if (min(uncached,output,cached,write)<0 or usage is None or not model or len(model)>96 or
                    not cost.is_finite() or cost<0):raise ValueError('Invalid numeric value')
        except (TypeError,ValueError,InvalidOperation) as error:
            raise ValueError('后台明细第 '+str(index)+' 行无效') from error
        identifier=hashlib.sha256(('\0'.join((at.isoformat(),model,str(uncached),str(output),
                            str(cached),str(write),str(cost)))).encode()).hexdigest()
        if identifier in seen:raise ValueError('后台明细包含重复行，无法安全区分重复导出与真实请求')
        seen.add(identifier)
        result.append({'id':identifier,'at':at.timestamp(),'model':model,'usage':usage,'billed_cost':str(cost)})
    return result


def reconcile(provider,local,book):
    remaining=list(local);matches=[];missing=[];total=zero();billed=Decimal(0)
    # Reasoning is a subset not exposed by this billing export; match the four
    # billed categories and model, then time. A unique nearest match is required.
    fields=('inputTokens','cachedInputTokens','cacheWriteInputTokens','outputTokens')
    for row in sorted(provider,key=lambda x:x['at']):
        total=plus(total,row['usage']);billed+=Decimal(row['billed_cost'])
        candidates=[(abs(item['at']-row['at']),i,item) for i,item in enumerate(remaining)
                    if item['model']==row['model'] and abs(item['at']-row['at'])<=180 and
                    all(item['usage'][k]==row['usage'][k] for k in fields)]
        candidates.sort(key=lambda x:x[0])
        if not candidates or (len(candidates)>1 and candidates[0][0]==candidates[1][0]):
            missing.append(row)
        else:
            _,index,item=candidates[0];remaining.pop(index);matches.append((row,item))
    estimated=0.0;price_complete=True
    for row in provider:
        rates=rate_for(book,row['model']);cost=estimate(row['usage'],rates) if rates else None
        if cost is None:price_complete=False
        else:estimated+=cost
    return {'provider_rows':len(provider),'matched_rows':len(matches),'provider_total':total,
        'provider_uncached_input':total['inputTokens']-total['cachedInputTokens']-total['cacheWriteInputTokens'],
        'provider_billed_cost':str(billed),'local_rate_estimate':estimated if price_complete else None,
        'missing_local':missing,'unmatched_local_count':len(remaining),
        'note':'Billed Cost is already discounted; do not apply Rate Multiplier again.'}


def supplements(provider,local):
    """Assign only unmatched billed requests enclosed by one known turn.

    Do not guess a thread from the current UI or a nearest unrelated request.
    Recompute from both complete sources, so a late local record removes its
    imported supplement instead of double-counting it.
    """
    comparison=reconcile(provider,local,{'models':{},'currency':'USD'})
    windows={}
    for record in local:
        key=(record['thread'],record['turn'],record['model'])
        left,right=windows.get(key,(record['at'],record['at']))
        windows[key]=(min(left,record['at']),max(right,record['at']))
    result=[]
    for row in comparison['missing_local']:
        candidates=[key for key,(left,right) in windows.items()
                    if key[2]==row['model'] and left<=row['at']<=right]
        if len(candidates)==1:
            thread,turn,model=candidates[0]
            result.append(dict(row,thread=thread,turn=turn))
    return result
