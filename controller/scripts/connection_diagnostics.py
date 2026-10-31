"""Credential-free checks for the local controller, pairing address and App build."""
import ipaddress
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'bridge'))
from meter_client import request


def local_ipv4():
    try:
        result = subprocess.run(['/sbin/ifconfig'], capture_output=True, text=True, timeout=3)
    except (OSError, subprocess.TimeoutExpired):
        return []
    addresses = []
    for raw in re.findall(r'\binet (\d+\.\d+\.\d+\.\d+)\b', result.stdout):
        address = ipaddress.IPv4Address(raw)
        if not address.is_loopback and not address.is_link_local and not address.is_unspecified:
            if raw not in addresses: addresses.append(raw)
    return addresses


def inspect(root=ROOT):
    paired = None
    problem = ''
    try:
        paired = json.loads((root/'private/wireless.json').read_text()).get('ip')
        if not isinstance(paired, str): paired = None
    except FileNotFoundError: pass
    except (OSError, ValueError, AttributeError): problem = '本机无线配对记录无法读取；保留原文件，勿删除。'
    addresses = local_ipv4()
    try:
        status = request({'type':'status'})
    except (OSError, ValueError) as error:
        status = None
        bridge_error = type(error).__name__
    else: bridge_error = ''
    return {'local_ips': addresses, 'paired_ip': paired,
            'address_changed': bool(paired and addresses and paired not in addresses),
            'pairing_problem': problem, 'status':status, 'bridge_error':bridge_error}


def show(report):
    status = report['status']
    print('Bridge：'+('运行中' if status else '未运行或本机接口不可达（'+report['bridge_error']+'）'), flush=True)
    if status:
        print('设备：'+('在线 / '+str(status.get('transport','')) if status.get('online') else '离线'), flush=True)
        print('App 实体审批：'+('已接入' if status.get('desktop',{}).get('connected') else '尚未接入；设备链路与 App 审批是两项检查'), flush=True)
    print('Mac 当前 IPv4：'+(', '.join(report['local_ips']) or '未检测到'), flush=True)
    print('设备配对的 Mac IPv4：'+str(report['paired_ip'] or '未配置'), flush=True)
    if report['address_changed']:
        print('配对地址已不属于当前 Mac。重配无线需更新设备地址和证书；只重启 Bridge 无法修正。USB 可先恢复使用。', flush=True)
    if report['pairing_problem']: print(report['pairing_problem'], flush=True)


if __name__ == '__main__': show(inspect())
