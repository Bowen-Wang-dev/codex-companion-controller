"""Private local IPC for numeric usage diagnostics and explicit counter resets."""
import json
import datetime
from ipc_path import connect


from console_i18n import tr
def request(message):
    with connect(timeout=3) as client:
        client.sendall(json.dumps(message).encode()+b'\n')
        with client.makefile('rb') as stream:
            response=stream.readline(65537)
    if len(response)>65536:
        raise ValueError('Bridge response too large')
    data=json.loads(response)
    if not isinstance(data,dict):raise ValueError('Invalid Bridge response')
    return data


REASONS={'request_boundaries_missing':'逐请求记录尚未齐全，无法安全判断长上下文费率', 'ready':'费率已匹配', 'waiting_usage':'费率已匹配，等待当前聊天用量',
    'model_unknown':'用量模型未识别', 'model_rate_missing':'部分用量的模型费率未配置',
    'cache_write_rate_missing':'缓存写入费率未配置'}


def summary(status):
    meter=status.get('metering')
    if not isinstance(meter,dict):
        return tr('运行中的 Bridge 尚未更新；请重新运行 PC 端 App 实体审批入口。')
    usage=meter['usage'];cost=meter['cost']
    total=usage.get('total');last=usage.get('last')
    def cost_text(value):
        if value is None:return tr('暂不可用')
        return ('$' if cost.get('currency')=='USD' else cost.get('currency','')+' ')+format(value,'.6f')
    reset_at=usage.get('reset_at')
    since=datetime.datetime.fromtimestamp(reset_at).astimezone().isoformat(timespec='seconds') if reset_at else tr('未知')
    return '\n'.join((
        'Bridge：'+str(status.get('bridge_revision',tr('未知'))),
        tr('设备：')+str(status.get('firmware',tr('未知'))),
        tr('当前模型：')+(usage.get('model') or tr('尚未收到')),
        tr('已配费率：')+(', '.join(cost.get('known_models',[])) or tr('无')),
        tr('费用状态：')+tr(REASONS.get(cost.get('status'),str(cost.get('status')))),
        tr('本轮 Token：')+(str(last['totalTokens']) if last else tr('等待用量')),
        tr('累计 Token：')+(str(total['totalTokens']) if total else tr('等待用量')),
        tr('累计估价：')+cost_text(cost.get('total')),
        tr('本地统计起点：')+since,
        tr('数据来源：')+(tr('逐响应记录 + 已导入后台明细') if usage.get('source')=='response_records+provider_export' else tr('逐响应记录（含压缩）') if usage.get('source')=='response_records' else tr('App Server 用量事件')),
        tr('补回的 Token：')+str(usage.get('recovered_tokens',0)),
        tr('输入包含缓存；输出包含推理，细目不要重复相加。'),
        tr('此计数不是服务商账单；后台重试等未返回用量的请求可能未包含。'),
        tr('计量问题：')+tr(usage.get('issue') or '无'),
        tr('文件核对：')+tr(usage.get('reader_issue') or '无'),
        tr('程序目录：')+str(status.get('project_root',tr('未知')))))
