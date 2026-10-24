#!/usr/bin/env python3
"""Fail-closed esptool 4.x app-only updater. No erase-all, NVS writes or efuse writes."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import struct
import subprocess
import sys
import time

SIZE = 8 * 1024 * 1024
SECTOR = 4096
ROOT = Path(__file__).resolve().parents[1]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def partitions(image):
    table = image[0x8000:0x9000]
    found = []
    checksum = False
    for offset in range(0, 0xc00, 32):
        record = table[offset:offset+32]
        magic = record[:2]
        if magic == b'\xeb\xeb':
            if record[16:] != hashlib.md5(table[:offset]).digest():
                raise ValueError('Partition table MD5 mismatch')
            checksum = True
            break
        if magic == b'\xff\xff':
            break
        if magic != b'\xaa\x50':
            raise ValueError('Unrecognized partition table; refusing automatic flash')
        _, kind, subtype, start, size, label, flags = struct.unpack('<HBBII16sI', record)
        name = label.split(b'\0')[0].decode('ascii')
        if start < 0x9000 or start % SECTOR or size <= 0 or size % SECTOR or start+size > SIZE:
            raise ValueError('Invalid partition range')
        found.append({'name': name, 'type': kind, 'subtype': subtype, 'offset': start, 'size': size, 'flags': flags})
    if not checksum or not found:
        raise ValueError('A valid MD5 partition table is required')
    spans = sorted(found, key=lambda p: p['offset'])
    for left, right in zip(spans, spans[1:]):
        if left['offset']+left['size'] > right['offset']:
            raise ValueError('Overlapping partitions')
    return found


def plan(image, app):
    if len(image) != SIZE:
        raise ValueError('Expected full 8 MB backup')
    table = partitions(image)
    apps = [p for p in table if p['type'] == 0]
    if len(apps) != 1 or apps[0]['subtype'] != 0 or apps[0]['name'] != 'factory':
        raise ValueError('Only a single factory app layout is supported; OTA/recovery needs manual review')
    target = apps[0]
    if target['offset'] != 0x10000 or target['flags'] != 0:
        raise ValueError('Unexpected app offset/flags')
    if len(app) < 256 or app[0] != 0xe9 or struct.unpack_from('<H', app, 12)[0] != 5:
        raise ValueError('Expected an ESP32-C3 application image')
    end = (target['offset']+len(app)+SECTOR-1)//SECTOR*SECTOR
    # Conservative ceiling below conflicting community cardid/recovery locations.
    if end > min(target['offset']+target['size'], 0x300000):
        raise ValueError('Application exceeds conservative protected boundary')
    return {'offset': target['offset'], 'erase_end': end, 'size': len(app),
            'image_sha256': sha(app), 'backup_sha256': sha(image), 'partitions': table,
            'writes_partition_table': False, 'writes_bootloader': False, 'erase_all': False}


class Tool:
    def __init__(self, port):
        self.base = [sys.executable, '-m', 'esptool', '--chip', 'esp32c3', '--port', port, '--baud', '460800']

    def run(self, *args):
        if args and args[0] in {'read_flash', 'write_flash', 'verify_flash'}:
            process = subprocess.Popen(self.base+list(args), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            output = bytearray()
            while True:
                chunk = process.stdout.read1(4096)
                if not chunk:
                    break
                output.extend(chunk)
                sys.stdout.buffer.write(chunk)
                sys.stdout.buffer.flush()
            code = process.wait()
            text = output.decode('utf-8', errors='replace')
            if code:
                raise RuntimeError(text[-4000:])
            return text
        result = subprocess.run(self.base+list(args), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        if result.returncode:
            raise RuntimeError(result.stdout[-4000:])
        return result.stdout

    def identity(self):
        info = self.run('flash_id')
        mac = re.search(r'MAC:\s*([0-9a-f:]{17})', info, re.I)
        if not mac or 'Detected flash size: 8MB' not in info:
            raise ValueError('Could not positively identify an 8 MB ESP32-C3')
        security = self.run('get_security_info')
        if 'Secure Boot: Disabled' not in security or 'Flash Encryption: Disabled' not in security:
            raise ValueError('Secure Boot/encryption enabled or unknown; custom image refused')
        return mac.group(1).lower()


def backup(tool):
    mac = tool.identity()
    folder = ROOT/'private'/'backups'/(time.strftime('%Y%m%d-%H%M%S')+'-'+mac.replace(':', ''))
    folder.mkdir(parents=True, mode=0o700, exist_ok=False)
    image_path, verify_path = folder/'flash.bin', folder/'verify.bin'
    print('备份 1/2：读取 8 MB Flash（只读，不擦除、不写入）…', flush=True)
    tool.run('read_flash', '0', hex(SIZE), str(image_path))
    print('备份 2/2：再次读取 8 MB，用于独立校验…', flush=True)
    tool.run('read_flash', '0', hex(SIZE), str(verify_path))
    image = image_path.read_bytes()
    if sha(image) != sha(verify_path.read_bytes()) or len(image) != SIZE:
        raise ValueError('Independent backup verification failed')
    verify_path.unlink()
    manifest = {'mac': mac, 'sha256': sha(image), 'size': len(image), 'partitions': partitions(image)}
    (folder/'manifest.json').write_text(json.dumps(manifest, indent=2))
    print('Verified private backup:', folder)
    return folder


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['backup', 'plan', 'flash', 'restore'])
    parser.add_argument('--port', default='/dev/cu.usbmodem1101')
    parser.add_argument('--backup', type=Path)
    parser.add_argument('--image', type=Path, default=ROOT/'dist'/'PassportController.bin')
    parser.add_argument('--execute', action='store_true', help='Explicitly execute a reviewed app-only plan')
    args = parser.parse_args()
    tool = Tool(args.port)
    if args.action == 'backup':
        backup(tool)
        return
    folder = args.backup
    if not folder:
        if args.action == 'plan':
            parser.error('--backup is required for offline planning')
        folder = backup(tool)
    image = (folder/'flash.bin').read_bytes()
    manifest = json.loads((folder/'manifest.json').read_text())
    if sha(image) != manifest['sha256']:
        raise ValueError('Backup hash does not match its manifest')
    app = args.image.read_bytes()
    info = subprocess.run([sys.executable, '-m', 'esptool', '--chip', 'esp32c3', 'image_info', str(args.image)],
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if info.returncode or not re.search(r'Validation Hash: [0-9a-f]+ \(valid\)', info.stdout):
        raise ValueError('esptool image validation failed: '+info.stdout[-1000:])
    reviewed = plan(image, app)
    print(json.dumps(reviewed, indent=2))
    if args.action == 'plan' or not args.execute:
        print('Plan only. To write, repeat with flash --execute (or restore --execute).')
        return
    if tool.identity() != manifest['mac']:
        raise ValueError('Connected device differs from backup')
    live = folder/'live-table.bin'
    tool.run('read_flash', '0x8000', '0x1000', str(live))
    if live.read_bytes() != image[0x8000:0x9000]:
        raise ValueError('Device partition table changed since backup')
    start, end = reviewed['offset'], reviewed['erase_end']
    if args.action == 'restore':
        record = json.loads((folder/'last-write.json').read_text())
        if record['image_sha256'] != reviewed['image_sha256'] or record['erase_end'] != end:
            raise ValueError('Restore must use the same application image as the recorded write')
        data = image[start:end]
    else:
        # Preserve bytes beyond the new image in the final erased sector.
        data = app + image[start+len(app):end]
    staged = folder/'app-write.bin'
    staged.write_bytes(data)
    # Save the rollback interval BEFORE starting a potentially interrupted write.
    (folder/'last-write.json').write_text(json.dumps(reviewed, indent=2))
    print(f'Writing only [{start:#x}, {end:#x}); backup: {folder}', flush=True)
    tool.run('write_flash', hex(start), str(staged))
    tool.run('verify_flash', hex(start), str(staged))
    (folder/'last-result.json').write_text(json.dumps({'verified': True, 'action': args.action, 'sha256': sha(data)}))


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        sys.exit(str(e))
