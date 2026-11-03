"""Windows console bootstrap. Local, isolated dependencies; never starts App by itself."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import venv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'bridge'))


def prepare():
    if sys.platform != 'win32':raise RuntimeError('此入口用于 Windows；macOS 请使用 .command 入口。')
    if sys.version_info < (3, 11):raise RuntimeError('请安装 Python 3.11 或更新版本（含 pip 和 Tcl/Tk）。')
    import ssl
    if ssl.OPENSSL_VERSION_INFO < (3,):raise RuntimeError('Bridge 需要 OpenSSL 3。')
    from windows_security import secure_directory
    private = secure_directory(ROOT/'private', create=True, restrict_existing=True)
    interpreter = private/'bridge-venv-windows/Scripts/python.exe'
    if not interpreter.exists():
        print('正在准备 Windows 独立 Python 环境…', flush=True)
        venv.EnvBuilder(with_pip=True).create(interpreter.parents[1])
    env = dict(os.environ, PYTHONUTF8='1', PYTHONIOENCODING='utf-8',
               CONTROLLER_BRIDGE_PYTHON=str(interpreter))
    if not env.get('COMPANION_CODEX'):
        from host_platform import desktop_app
        try:
            binary=desktop_app()/'resources/codex.exe'
            if binary.is_file():env['COMPANION_CODEX']=str(binary)
        except (OSError, RuntimeError, ValueError):pass
    subprocess.run([str(interpreter), str(ROOT/'scripts/setup_bridge_deps.py')], env=env, check=True)
    # Native .exe entry preserves argv and avoids cmd.exe escaping of App
    # Server arguments. pip's distlib launcher embeds this interpreter path.
    code = """
from pip._vendor.distlib.scripts import ScriptMaker
from pathlib import Path
import sys
root=Path(sys.argv[1])
maker=ScriptMaker(None,str(root/'private'))
maker.executable=sys.executable
maker.clobber=True
maker.variants={''}
maker.script_template='import runpy,sys\\nsys.path.insert(0,%r)\\nrunpy.run_path(%r,run_name="__main__")\\n' % (str(root/'bridge'),str(root/'scripts/app_relay.py'))
maker.make('app-relay = passport:main')
"""
    executable=private/'app-relay.exe'
    receipt=private/'app-relay.json'
    expected={'version':1, 'interpreter':str(interpreter), 'root':str(ROOT)}
    try:
        recorded=json.loads(receipt.read_text(encoding='utf-8'))
        ready=all(recorded.get(k)==v for k,v in expected.items()) and recorded.get('sha256')==hashlib.sha256(executable.read_bytes()).hexdigest()
    except (OSError, ValueError, AttributeError):ready=False
    if not ready:
        subprocess.run([str(interpreter), '-c', code, str(ROOT)], env=env, check=True)
        from private_permissions import set_private
        set_private(executable)
        receipt.write_text(json.dumps(dict(expected,sha256=hashlib.sha256(executable.read_bytes()).hexdigest())),encoding='utf-8')
        set_private(receipt)
    subprocess.run([str(interpreter), '-c', 'import serial,websockets,ssl,tkinter; assert ssl.OPENSSL_VERSION_INFO >= (3,); print("Windows Bridge dependencies ready")'], env=env, check=True)
    return interpreter, env


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--setup-only', action='store_true')
    parser.add_argument('--check-only', action='store_true')
    args, extra = parser.parse_known_args()
    if (args.setup_only or args.check_only) and extra:parser.error('检查/准备模式不接受额外参数')
    interpreter, env = prepare()
    if args.check_only:
        return subprocess.run([str(interpreter), str(ROOT/'scripts/check_windows.py')], env=env).returncode
    if args.setup_only:return 0
    return subprocess.run([str(interpreter), str(ROOT/'scripts/controller_console.py'), *extra], env=env).returncode


if __name__ == '__main__':
    try:sys.exit(main())
    except (OSError, RuntimeError, subprocess.SubprocessError) as error:sys.exit('Windows 环境准备未完成：'+str(error))
