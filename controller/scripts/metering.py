#!/usr/bin/env python3
"""Inspect/reset this project's local meter; never call a model or billing API."""
import argparse
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bridge'))
from meter_client import request, summary


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reset',action='store_true')
    args=parser.parse_args()
    status=request({'type':'status'})
    print(summary(status))
    if not args.reset:return
    meter=status.get('metering')
    if not meter:raise ValueError('请先更新正在运行的 Bridge。')
    print('\n只清零控制器的累计 Token 与估价；不会删除聊天或改变服务商账单。')
    if input('输入 RESET 确认；其他输入取消：').strip()!='RESET':
        print('已取消。');return
    result=request({'type':'meter_reset','meter_id':meter['usage']['meter_id']})
    if not result.get('cleared'):raise ValueError('计数未清零：状态已变化或存储失败，请重新检查。')
    print('计数已清零，已保存到本机；设备下次同步后更新。')


if __name__=='__main__':
    try:main()
    except (OSError,ValueError) as error:sys.exit('无法读取计量状态：'+str(error))
