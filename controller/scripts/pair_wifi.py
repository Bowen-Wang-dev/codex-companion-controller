#!/usr/bin/env python3
"""Keep USB open BEFORE asking for physical consent. Compatible with V0.2.0."""
import getpass
import glob
import ipaddress
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import time

import serial

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'bridge'))
from tls_material import certificate_is_named_p256, create_certificate


class PairingError(Exception):
    pass


def encode_config(message):
    """Check the actual UTF-8 byte limits used by network.c and main.c."""
    for field, lower, upper in [('ssid', 1, 32), ('password', 0, 64),
                                ('url', 1, 159), ('cert', 1, 2047)]:
        value = message.get(field)
        if not isinstance(value, str) or '\0' in value or not lower <= len(value.encode('utf-8')) <= upper:
            names = {'ssid': 'Wi-Fi 名称', 'password': 'Wi-Fi 密码', 'url': 'Bridge 地址', 'cert': '配对证书'}
            raise PairingError(f'{names[field]}格式或字节长度不符合设备限制；尚未发送。')
    if not message['url'].startswith('https://'):
        raise PairingError('Bridge 必须使用 HTTPS；尚未发送。')
    if '-----BEGIN CERTIFICATE-----' not in message['cert'] or '-----END CERTIFICATE-----' not in message['cert']:
        raise PairingError('配对证书格式无效；尚未发送。')
    token = message.get('token', '')
    if not isinstance(token, str) or len(token) != 64 or any(c not in '0123456789abcdef' for c in token):
        raise PairingError('本机配对密钥格式无效；尚未发送。')
    if message.get('type') != 'provision' or not isinstance(message.get('utc'), int) or message['utc'] < 1700000000:
        raise PairingError('配置类型或 Mac 系统时间无效；尚未发送。')
    frame = b'PC1 ' + json.dumps(message, ensure_ascii=False, separators=(',', ':')).encode('utf-8') + b'\n'
    if len(frame) > 4096:
        raise PairingError('配置超过设备接收缓冲区；尚未发送。')
    return frame


class Reader:
    def __init__(self, device):
        self.device = device
        self.buffer = b''

    def poll(self):
        self.buffer += self.device.read(512)
        messages = []
        while b'\n' in self.buffer:
            line, self.buffer = self.buffer.split(b'\n', 1)
            if not line.startswith(b'PC1 ') or len(line) > 4095:
                continue
            try:
                value = json.loads(line[4:])
            except (ValueError, UnicodeError):
                continue
            if isinstance(value, dict):
                messages.append(value)
        if len(self.buffer) > 4095:
            self.buffer = b''
        return messages


def open_device(port):
    # pySerial otherwise opens immediately with DTR/RTS active. Drivers may
    # still change these lines during open, so obtain a fresh hello afterwards.
    device = serial.Serial(port=None, baudrate=115200, timeout=.1, write_timeout=3, exclusive=True)
    device.dtr = False
    device.rts = False
    device.port = port
    try:
        device.open()
    except BaseException:
        device.close()
        raise
    return device


def wait_hello(reader, timeout=15):
    deadline = time.monotonic() + timeout
    previous = None
    while time.monotonic() < deadline:
        for message in reader.poll():
            if message.get('type') != 'hello' or not isinstance(message.get('boot'), str) or not message['boot']:
                continue
            version = message.get('firmware', '')
            try:
                compatible = tuple(int(x) for x in version.split('.')) >= (0, 2, 0)
            except (ValueError, AttributeError):
                compatible = False
            if not compatible:
                raise PairingError('设备报告的固件不支持本次无线配置（需要 V0.2 或更新版）。')
            # Two consecutive hellos avoid prompting during a port-open reboot.
            if previous == message['boot']:
                return message
            previous = message['boot']
    raise PairingError('USB 未收到稳定的固件握手。请检查数据线、设备是否开机，以及其他串口工具是否已关闭。')


def provision(device, message, ask=None, say=None, attempts=3):
    ask = ask or input
    say = say or print
    reader = Reader(device)
    hello = wait_hello(reader)
    boot = hello['boot']
    say(f'USB 已连接，固件 {hello["firmware"]}。现在还没有连接 Wi-Fi，这是正常的。')
    for attempt in range(attempts):
        say('在设备用方向键找到第六页「连接与配网」。')
        say('短按并松开确认键（不要长按，也不要按电源键）。')
        say('屏幕应变为「请在 Mac 运行无线配对」；从此时起 60 秒内回到终端。')
        answer = ask('看到上述提示后按回车发送；输入 q 取消：').strip().lower()
        if answer == 'q':
            raise PairingError('已取消，没有发送本次配置。')
        # Clear old frames without closing/reopening USB or resetting consent.
        deadline = time.monotonic() + .3
        restarted = False
        while time.monotonic() < deadline:
            for received in reader.poll():
                if received.get('type') == 'hello' and received.get('boot'):
                    if received['boot'] != boot:
                        restarted = True
                        boot = received['boot']
        if restarted:
            say('检测到设备刚刚重启，之前的配对许可已失效。USB 保持连接，请重新短按设备确认。')
            continue
        message = dict(message, utc=int(time.time()))
        frame = encode_config(message)
        if device.write(frame) != len(frame):
            raise PairingError('USB 未完整发送配置，未确认保存；请保持 USB 连接后重新运行配置。')
        deadline = time.monotonic() + 10
        rejected = False
        while time.monotonic() < deadline:
            for reply in reader.poll():
                if reply.get('type') == 'hello' and reply.get('boot') != boot:
                    raise PairingError('发送后设备重启，但未收到保存回执；无法确认是否完成。请重新运行无线配置。')
                if reply.get('type') != 'provisioned':
                    continue
                if reply.get('boot') != boot:
                    boot = reply.get('boot', boot)
                    say('设备重启使配对许可失效。请重新短按设备确认，再按终端回车。')
                    rejected = True
                    break
                if reply.get('ok') is True:
                    return
                say('设备未接受配置。请确认已短按并松开确认键，屏幕出现配对提示，且未超过 60 秒。')
                say('配置长度已在 Mac 检查通过；V0.2.0 回执不能区分未授权与设备存储失败。')
                rejected = True
                break
            if rejected:
                break
        if not rejected:
            # No automatic resend after a lost ACK: the device may have saved.
            raise PairingError('未收到保存回执，不能确认配对成功。请重新运行无线配置；本次配对密钥已保留在本机。')
        if attempt + 1 < attempts:
            say('无需重新输入 Wi-Fi 密码；USB 保持打开，重新确认后重试。')
    raise PairingError('本次未完成配对。若屏幕已出现许可提示仍被拒绝，请保留终端结果继续排查，不要反复重刷。')


def write_private_json(path, value):
    temporary = path.with_suffix('.tmp')
    with temporary.open('w') as output:
        os.chmod(temporary, 0o600)
        json.dump(value, output)
        output.flush()
        os.fsync(output.fileno())
    os.replace(temporary, path)


def main():
    os.umask(0o077)
    private = ROOT / 'private'
    private.mkdir(exist_ok=True)
    os.chmod(private, 0o700)
    ports = glob.glob('/dev/cu.usbmodem*')
    if len(ports) != 1:
        raise PairingError('请用数据线连接一台 AI Passport，并停止其他 Bridge / 串口工具。')
    print('本操作只配置无线，不刷固件，也不消费 Codex 额度。')
    ssid = input('2.4 GHz Wi-Fi 名称：')
    password = getpass.getpass('Wi-Fi 密码（不显示）：')
    try:
        default_ip = subprocess.check_output(['/usr/sbin/ipconfig', 'getifaddr', 'en0'], text=True, stderr=subprocess.DEVNULL).strip()
    except subprocess.CalledProcessError:
        default_ip = ''
    if not default_ip:
        from connection_diagnostics import local_ipv4
        candidates = local_ipv4()
        default_ip = candidates[0] if len(candidates) == 1 else ''
    ip = input(f'Mac 局域网 IPv4 地址 [{default_ip}]：').strip() or default_ip
    try:
        address = ipaddress.IPv4Address(ip)
    except ipaddress.AddressValueError:
        raise PairingError('Mac 地址需要是局域网 IPv4 地址，例如 192.168.1.110。') from None
    if address.is_loopback or address.is_unspecified or address.is_multicast or address.is_reserved:
        raise PairingError('请填写设备可访问的 Mac 局域网地址。')
    ip = str(address)
    config_path = private / 'wireless.json'
    pending_path = private / 'wireless-pending.json'
    old_path = pending_path if pending_path.exists() else config_path
    try:
        old = json.loads(old_path.read_text()) if old_path.exists() else {}
    except (ValueError, OSError):
        raise PairingError('本机配对记录无法读取，请保留文件继续排查。') from None
    if not isinstance(old, dict):
        raise PairingError('本机配对记录格式无效，请保留文件继续排查。')
    compatible = certificate_is_named_p256(private / 'bridge-cert.pem')
    if not compatible and (private / 'bridge-cert.pem').exists():
        print('检测到旧证书编码不兼容，将生成设备可解析的新证书；本次 USB 配对会更新设备证书。')
    if old.get('ip') != ip or not compatible or not (private / 'bridge-key.pem').exists():
        try:
            create_certificate(private, ip)
        except ValueError as error:
            raise PairingError(str(error)) from None
    config = {'ip': ip, 'token': old.get('token') or secrets.token_hex(32)}
    message = {'type': 'provision', 'ssid': ssid, 'password': password, 'url': f'https://{ip}:8765/device', 'token': config['token'], 'cert': (private / 'bridge-cert.pem').read_text(), 'utc': int(time.time())}
    encode_config(message)
    # Keep only non-password pairing data if a successful save ACK is lost.
    # Activate the Bridge config only after a positive device ACK.
    write_private_json(pending_path, config)
    print('正在打开 USB 并等待设备握手，随后再按设备确认…', flush=True)
    with open_device(ports[0]) as device:
        provision(device, message)
    os.replace(pending_path, config_path)
    print('设备已确认保存，正在重启连接 Wi-Fi。接下来启动 Bridge；看到 Wi-Fi 握手成功后再拔 USB。')


if __name__ == '__main__':
    try:
        main()
    except (PairingError, serial.SerialException, OSError, subprocess.CalledProcessError) as error:
        # OS errors contain port paths, never the password or provisioning frame.
        sys.exit(f'无线配置未完成：{error}')
    except (KeyboardInterrupt, EOFError):
        sys.exit('\n已停止无线配置。')
