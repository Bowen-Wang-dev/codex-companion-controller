"""Private local IPC for numeric usage diagnostics and explicit counter resets."""
import json
import socket
import datetime
from ipc_path import check_directory


def request(message):
    with socket.socket(socket.AF_UNIX) as client:
        client.settimeout(3)
        client.connect(str(check_directory()))
        client.sendall(json.dumps(message).encode()+b'\n')
        with client.makefile('rb') as stream:
            response=stream.readline(65537)
    if len(response)>65536:
        raise ValueError('Bridge response too large')
    data=json.loads(response)
    if not isinstance(data,dict):raise ValueError('Invalid Bridge response')
    return data


REASONS={'ready':'费率已匹配', 'waiting_usage':'费率已匹配，等待当前聊天用量',
    'model_unknown':'用量模型未识别', 'model_rate_missing':'部分用量的模型费率未配置',
    'cache_write_rate_missing':'缓存写入费率未配置'}


def summary(status):
    meter=status.get('metering')
    if not isinstance(meter,dict):
        return '运行中的 Bridge 尚未更新；请重新运行桌面 App 实体审批入口。'
    usage=meter['usage'];cost=meter['cost']
    total=usage.get('total');last=usage.get('last')
    def cost_text(value):
        if value is None:return '暂不可用'
        return ('$' if cost.get('currency')=='USD' else cost.get('currency','')+' ')+format(value,'.6f')
    reset_at=usage.get('reset_at')
    since=datetime.datetime.fromtimestamp(reset_at).astimezone().isoformat(timespec='seconds') if reset_at else '未知'
    return '\n'.join((
        'Bridge：'+str(status.get('bridge_revision','未知')),
        '设备：'+str(status.get('firmware','未知')),
        '当前模型：'+(usage.get('model') or '尚未收到'),
        '已配费率：'+(', '.join(cost.get('known_models',[])) or '无'),
        '费用状态：'+REASONS.get(cost.get('status'),str(cost.get('status'))),
        '本轮 Token：'+(str(last['totalTokens']) if last else '等待用量'),
        '累计 Token：'+(str(total['totalTokens']) if total else '等待用量'),
        '累计估价：'+cost_text(cost.get('total')),
        '本地统计起点：'+since,
        '数据来源：'+('逐响应记录 + 已导入后台明细' if usage.get('source')=='response_records+provider_export' else '逐响应记录（含压缩）' if usage.get('source')=='response_records' else 'App Server 用量事件'),
        '补回的 Token：'+str(usage.get('recovered_tokens',0)),
        '输入包含缓存；输出包含推理，细目不要重复相加。',
        '此计数不是服务商账单；后台重试等未返回用量的请求可能未包含。',
        '计量问题：'+(usage.get('issue') or '无'),
        '文件核对：'+(usage.get('reader_issue') or '无'),
        '程序目录：'+str(status.get('project_root','未知'))))
