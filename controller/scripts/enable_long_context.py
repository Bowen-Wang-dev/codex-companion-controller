#!/usr/bin/env python3
"""Apply user-provided Sol price card; restart only this project's idle Bridge."""
import datetime
import json
import os
from pathlib import Path
import shutil
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'bridge'))
from usage_meter import private_json, load_rates
from connection_diagnostics import inspect, show
from recover_bridge import stop_idle_bridge

MODEL='gpt-6.1-sol'
CARD={'input':.36,'cached_input':.018,'output':1.8,'cache_write':.45,
      'long_context':{'above_input_tokens':272000,'input':.72,'cached_input':.036,'output':2.7,'cache_write':.90}}


def main():
    report=inspect();show(report)
    print('将配置 gpt-6.1-sol：普通档 $0.36 / $0.018 / $1.80，长档 $0.72 / $0.036 / $2.70（输入／缓存读／输出，每百万）。')
    print('缓存写普通 $0.45，长档 $0.90；阈值为单次输入含缓存 >272000。这些已经乘过 0.18，不再重复打折。')
    print('保留其他模型、计数、账户及配网；不刷机、不关闭 App。')
    print('旧累计若缺少逐请求记录，将暂不猜费用；重新读取本机数字记录后可恢复，无法恢复的历史会明确标记。')
    if input('输入 YES 保存并重启本项目 Bridge；其他输入取消：').strip()!='YES':return
    status=report['status']
    if status and (status.get('permission_pending') or status.get('hook_pending')):
        raise RuntimeError('先完成待处理审批，再重新运行；未修改费率。')
    path=ROOT/'private/token_rates.json'
    if path.exists():
        data=json.loads(path.read_text())
        if not isinstance(data,dict) or not isinstance(data.get('models'),dict):raise ValueError('原费率文件格式无效，未覆盖。')
        backup=path.with_name('token_rates-before-long-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')+'.json')
        shutil.copyfile(path,backup);os.chmod(backup,0o600)
    else:data={'currency':'USD','models':{}}
    if data.get('currency')!='USD':raise ValueError('原费率不是 USD，请先在编辑器核对；未覆盖。')
    data['models'][MODEL]=CARD
    private_json(path,data)
    if load_rates(path)['models'].get(MODEL)!=CARD:raise ValueError('新费率校验失败；请保留备份继续排查。')
    print('已备份并保存；正在保持 App 打开重启 Bridge。',flush=True)
    stop_idle_bridge(status)
    os.execv(sys.executable,[sys.executable,str(ROOT/'bridge/service.py'),'--desktop'])


if __name__=='__main__':
    try:main()
    except (OSError,ValueError,RuntimeError) as error:sys.exit('未完成：'+str(error))
    except (EOFError,KeyboardInterrupt):sys.exit('已取消。')
