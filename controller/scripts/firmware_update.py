"""Build and safely update the application from the Windows console."""
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'bridge'))


def source_digest(root=ROOT):
    digest = hashlib.sha256()
    files = sorted(p for p in (root/'firmware').rglob('*') if p.is_file()
                   and not any(x in p.relative_to(root/'firmware').parts
                               for x in ('build', 'managed_components', '.git'))
                   and (p.suffix in ('.c', '.h', '.yml', '.csv', '.lock')
                        or p.name in ('CMakeLists.txt', 'sdkconfig', 'sdkconfig.defaults')))
    for path in files:
        digest.update(path.relative_to(root).as_posix().encode()+b'\0')
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def validate_image(root=ROOT, require_assets=True):
    manifest = json.loads((root/'dist/manifest.json').read_text(encoding='utf-8'))
    image = (root/'dist/PassportController.bin').read_bytes()
    version = re.search(r'set\(PROJECT_VER "companion-([^"]+)"\)',
                        (root/'firmware/CMakeLists.txt').read_text(encoding='utf-8')).group(1)
    if manifest.get('version') != version or manifest.get('chip') != 'esp32c3':
        raise ValueError('固件版本或芯片不匹配，请重新构建。')
    if manifest.get('sha256') != hashlib.sha256(image).hexdigest() or manifest.get('size') != len(image):
        raise ValueError('固件摘要或大小校验失败。')
    if manifest.get('source_sha256') != source_digest(root):
        raise ValueError('固件未绑定当前源码，或源码已更新；请先重新构建。')
    if require_assets and manifest.get('apple_assets_included') is not True:
        raise ValueError('缺少 Apple 原版表情素材，拒绝刷入无表情固件。请从原 Mac 私有备份恢复 pet_assets.h 后重新构建。')
    if manifest.get('bootloader_included') is not False or manifest.get('partition_table_included') is not False:
        raise ValueError('只允许应用镜像。')
    return manifest


def build():
    if not (ROOT/'firmware/main/pet_assets.h').is_file():
        raise RuntimeError('缺少私有 firmware/main/pet_assets.h。请从原 Mac 私有备份恢复；不会替换表情或构建用于升级的无图固件。')
    env = dict(os.environ)
    idf = env.get('IDF_PATH')
    if idf and (Path(idf)/'tools/idf.py').is_file():
        version = subprocess.check_output([sys.executable, str(Path(idf)/'tools/idf.py'), '--version'], text=True)
        if not re.search(r'v5\.5\.3\b', version):
            raise RuntimeError('需要 ESP-IDF 5.5.3；未使用未知版本构建。')
        subprocess.run([sys.executable, str(Path(idf)/'tools/idf.py'), '-B',
                        str(ROOT/'private/build-windows'), 'build'], cwd=ROOT/'firmware', env=env, check=True)
        output = ROOT/'private/build-windows/PassportController.bin'
    else:
        # Reuse the installed Linux toolchain; USB is handled on Windows only.
        linux_root = subprocess.check_output(['wsl.exe', '-e', 'wslpath', '-a', str(ROOT)], text=True).strip()
        script = ('set -eu; . "${IDF_PATH:-$HOME/esp/esp-idf-v5.5.3}/export.sh" >/dev/null; '
                  'python "$IDF_PATH/tools/idf.py" --version | grep -E "v5[.]5[.]3([^0-9]|$)"; '
                  'cd '+shlex.quote(linux_root+'/firmware')+'; '
                  'python "$IDF_PATH/tools/idf.py" -B '+shlex.quote(linux_root+'/private/build')+' build')
        subprocess.run(['wsl.exe', '-e', 'bash', '-c', script], check=True)
        output = ROOT/'private/build/PassportController.bin'
    dist = ROOT/'dist'
    dist.mkdir(exist_ok=True)
    temporary = dist/'PassportController.bin.tmp'
    temporary.write_bytes(output.read_bytes())
    temporary.replace(dist/'PassportController.bin')
    subprocess.run([sys.executable, str(ROOT/'scripts/manifest.py')], check=True)
    manifest_path = dist/'manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    manifest['source_sha256'] = source_digest()
    manifest_path.write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
    validate_image()
    print('构建与源码绑定校验通过；尚未写入设备。')


def flash_python():
    interpreter = os.environ.get('CONTROLLER_FLASH_PYTHON') or str(ROOT/'private/flash-venv-windows/Scripts/python.exe')
    if not Path(interpreter).is_file():
        raise RuntimeError('未准备刷写环境，请先选择菜单 4。')
    subprocess.run([interpreter, '-c', 'import esptool; assert esptool.__version__.split(".")[0]=="4", "需要 esptool 4.x"'], check=True)
    return interpreter


def setup_flash():
    import venv
    from windows_security import secure_directory
    private = secure_directory(ROOT/'private', create=True, restrict_existing=True)
    folder = private/'flash-venv-windows'
    if not (folder/'Scripts/python.exe').exists():
        venv.EnvBuilder(with_pip=True).create(folder)
    subprocess.run([str(folder/'Scripts/python.exe'), '-m', 'pip', 'install', 'esptool==4.8.1'], check=True)


def update():
    from host_platform import usb_ports
    from connection_diagnostics import inspect
    from recover_bridge import stop_idle_bridge
    from ipc_path import acquire_endpoint
    manifest = validate_image()
    interpreter = flash_python()
    ports = usb_ports()
    if len(ports) != 1:
        raise RuntimeError('请用 USB 数据线连接唯一一台 AI Passport，关闭其他串口工具。')
    print('固件 '+manifest['version']+' / SHA-256 '+manifest['sha256'])
    print('将双读完整 8 MB 备份，仅写 factory 应用并校验；保留配对和其他分区。')
    if input('输入 FLASH 开始；其他输入取消：').strip() != 'FLASH':return
    # Check again after confirmation, before touching the Bridge or USB.
    validate_image()
    stop_idle_bridge(inspect()['status'])
    lease = acquire_endpoint()
    try:
        subprocess.run([interpreter, str(ROOT/'scripts/flash.py'), 'flash', '--port', ports[0], '--execute'], check=True)
    finally:
        lease.close()
    print('应用写入及校验完成。请通过控制台菜单 2 恢复 Bridge，再检查真屏和按键。')


def main():
    print('1 构建最新固件（复用 ESP-IDF / WSL，需原版私有表情素材）\n2 检查镜像与当前源码\n3 USB 安全升级\n4 准备 Windows 刷写环境（下载 esptool 4.8.1）\nq 返回')
    choice = input('选择：').strip()
    if choice == '1':build()
    elif choice == '2':print(json.dumps(validate_image(), ensure_ascii=False, indent=2))
    elif choice == '3':update()
    elif choice == '4':setup_flash()


if __name__ == '__main__':
    try:main()
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        sys.exit('固件维护未完成：'+str(error))
