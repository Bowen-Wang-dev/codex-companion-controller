#!/usr/bin/env python3
"""Read-only desktop App Server check, intended for a normal macOS Terminal."""
import argparse
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'bridge'))
from desktop_connection import probe,save_report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--socket',type=Path)
    parser.add_argument('--expected-thread',default=os.environ.get('CODEX_THREAD_ID'))
    args=parser.parse_args()
    print('只读检查桌面 App 的官方审批接口；请保持 App 打开。',flush=True)
    print('不启动会话、不发送任务、不批准请求、不改变账户或配网。',flush=True)
    report=probe(args.socket,args.expected_thread)
    save_report(ROOT/'private/desktop-probe.json',report)
    if report['connected']:
        print('官方 Unix WebSocket 握手成功。')
        print('已加载会话数量：'+str(len(report['thread_ids'])))
        if args.expected_thread:
            print('目标 App 会话：'+('在同一后端中找到' if report['expected_loaded'] else '尚未在此后端找到'))
        print('检查结果已保存在 private/desktop-probe.json，不含账户令牌或聊天内容。')
    else:
        print('尚未接通：'+report['error'])
        print('检查结果已保存；没有启动其他 App Server 冒充当前会话。')
    return 0 if report['connected'] else 1


if __name__=='__main__':
    sys.exit(main())
