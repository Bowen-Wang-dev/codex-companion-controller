#!/usr/bin/env python3
"""Read-only, time-bounded audit of completed local response usage."""
import argparse
import datetime
import json
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'bridge'))
from meter_client import request
from response_usage import ResponseUsageReader
from usage_meter import UsageLedger, load_rates, plus, zero


def timestamp(value):
    parsed=datetime.datetime.fromisoformat(value.replace('Z','+00:00'))
    if parsed.tzinfo is None:raise argparse.ArgumentTypeError('时间必须包含时区，例如 +11:00')
    return parsed.timestamp()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--since',type=timestamp)
    parser.add_argument('--until',type=timestamp)
    parser.add_argument('--json',action='store_true')
    parser.add_argument('--provider-log',type=Path,help='Read-only comparison with a CSV/TSV billing export')
    args=parser.parse_args()
    end=args.until if args.until is not None else time.time()
    start=args.since if args.since is not None else end-3600
    if start>=end:parser.error('统计起点必须早于终点')
    ledger=UsageLedger(ROOT/'private/token-ledger.json')
    if ledger.blocked:raise ValueError('本地计量文件不可读；没有修改文件')
    threads=set(ledger.threads)
    try:
        status=request({'type':'status'})
        for relay in status.get('desktop',{}).get('relays',[]):
            if isinstance(relay,dict):threads.update(relay.get('sessions',[]))
    except (OSError,ValueError):pass
    reader=ResponseUsageReader();records=[]
    # Bound initial history scanning; return completeness rather than silently
    # treating a partially read large rollout as a final total.
    for _ in range(64):
        records.extend(reader.read(threads))
        if all(v['offset']>=v['path'].stat().st_size for v in reader.files.values()):break
    complete=not reader.missing and all(v['offset']>=v['path'].stat().st_size for v in reader.files.values())
    book=load_rates(ROOT/'private/token_rates.json');seen=set();totals=zero();groups={};turns={}
    for record in records:
        if not start<=record['at']<end or record['id'] in seen:continue
        seen.add(record['id']);totals=plus(totals,record['usage'])
        model=record['model'];groups[model]=plus(groups.get(model,zero()),record['usage'])
        key=UsageLedger.turn_key(record['thread'],record['turn'])
        turn=turns.setdefault(key,{'first':record['at'],'last':record['at'],'usage':zero(),'responses':0})
        turn['last']=max(turn['last'],record['at']);turn['first']=min(turn['first'],record['at'])
        turn['usage']=plus(turn['usage'],record['usage']);turn['responses']+=1
    request_groups={}
    for record in records:
        if start<=record['at']<end:
            request_groups.setdefault(record['model'],{})[record['id']]=record['usage']
    cost,reason=UsageLedger.cost(groups,book,'',{m:list(rows.values()) for m,rows in request_groups.items()})
    if not groups:cost,reason=0.0,''
    def local(at):return datetime.datetime.fromtimestamp(at).astimezone().isoformat(timespec='seconds')
    result={'since':local(start),'until':local(end),'source':'local_completed_response_records',
        'account_wide':False,'scan_complete':complete,'reader_issue':reader.issue,
        'responses':len(seen),'total':totals,
        'uncached_input':totals['inputTokens']-totals['cachedInputTokens']-totals['cacheWriteInputTokens'],
        'currency':book['currency'],'estimated_cost':cost,'cost_issue':reason,
        'turns':[dict(v,first=local(v['first']),last=local(v['last'])) for v in turns.values()],
        'limitation':'Provider charges without a completed local usage record are not visible.'}
    if args.provider_log:
        from provider_billing import parse_export, reconcile
        provider=[r for r in parse_export(args.provider_log.read_text()) if start<=r['at']<end]
        result['provider_comparison']=reconcile(provider,[r for r in records if start<=r['at']<end],book)
    if args.json:print(json.dumps(result,ensure_ascii=False,indent=2));return
    print('统计时间：'+result['since']+' → '+result['until'])
    print('范围：本项目已知聊天的本机完成请求；含压缩，不是账户账单。')
    print('完成请求：',len(seen),'扫描完整：',complete)
    print('非缓存输入：',result['uncached_input'],'缓存读取：',totals['cachedInputTokens'],
          '缓存写入：',totals['cacheWriteInputTokens'],'输出（含推理）：',totals['outputTokens'])
    print('总计：',totals['totalTokens'],'估价：',('$' if book['currency']=='USD' else book['currency']+' ')+format(cost,'.6f') if cost is not None else reason)
    for index,turn in enumerate(result['turns'],1):
        print('轮次',index,turn['first'],'→',turn['last'],'请求',turn['responses'],'Token',turn['usage']['totalTokens'])
    if reader.issue:print('读取提示：'+reader.issue)
    if args.provider_log:
        comparison=result['provider_comparison']
        print('后台请求：',comparison['provider_rows'],'本机匹配：',comparison['matched_rows'])
        print('后台 Token：',comparison['provider_total']['totalTokens'],'后台已折扣费用：$'+comparison['provider_billed_cost'])
        for row in comparison['missing_local']:
            print('后台存在、本机缺少：',local(row['at']),row['model'],'Token',row['usage']['totalTokens'],'费用 $'+row['billed_cost'])
    print('后台重试／未返回完成用量的收费请求可能无法在此核对。')


if __name__=='__main__':
    try:main()
    except (OSError,ValueError) as error:sys.exit('核对未完成：'+str(error))
