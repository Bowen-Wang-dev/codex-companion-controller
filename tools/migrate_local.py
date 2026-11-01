#!/usr/bin/env python3
"""Copy a source checkout and private device state without changing live services."""
import argparse
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import uuid
import venv

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_DEST=Path.home()/'Developer'/'codex-companion-controller'
EXTRA_ROOT_FILES=('LOCAL-MIGRATION-INPUT.json',)


def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def source_files(source):
    raw=subprocess.check_output(['git','-C',str(source),'ls-files','--cached','--others','--exclude-standard','-z'])
    result=[]
    for name in sorted(set(raw.decode().split('\0'))):
        if not name:continue
        rel=Path(name)
        if rel.is_absolute() or '..' in rel.parts:raise ValueError('Unsafe source path')
        p=source/rel
        if p.is_symlink():raise ValueError('Source contains a symlink; inspect before migrating: '+str(rel))
        if p.is_file():result.append(rel)
    return result


def copy_checked(src,dst,records,private=False):
    if src.is_symlink() or not src.is_file():raise ValueError('Expected regular source file: '+str(src))
    dst.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(src,dst)
    if private:dst.chmod(0o600)
    if digest(src)!=digest(dst):raise ValueError('Copy checksum mismatch')
    records.append({'sha256':digest(dst),'bytes':dst.stat().st_size})


def private_tree(source,dest,records):
    if not source.exists():return
    for p in source.rglob('*'):
        if p.is_symlink():raise ValueError('Private backup contains a symlink; inspect locally before copying')
        if p.is_file():copy_checked(p,dest/p.relative_to(source),records,private=True)
    for p in [dest,*dest.rglob('*')]:
        if p.is_dir():p.chmod(0o700)


def copy_runtime(runtime,dest,records):
    private=runtime/'private';out=dest/'controller/private';out.mkdir(parents=True,mode=0o700,exist_ok=True)
    for p in private.iterdir():
        if p.is_file() and not p.is_symlink() and p.suffix.lower() in ('.json','.csv','.tsv','.pem','.key','.cnf'):
            copy_checked(p,out/p.name,records,True)
    for name in ('backups','apple-originals','hook-backups'):
        if (private/name).exists():private_tree(private/name,out/name,records)
    for name in ('pet_assets.h',):
        p=runtime/'firmware/main'/name
        if p.is_file():copy_checked(p,dest/'controller/firmware/main'/name,records,True)
    for name in ('sdkconfig','sdkconfig.old'):
        p=runtime/'firmware'/name
        if p.is_file():copy_checked(p,dest/'controller/firmware'/name,records,True)
    if (runtime/'dist').exists():private_tree(runtime/'dist',dest/'controller/dist',records)


def prepare_environment(dest):
    # Build at the final destination: an absolute wheel .pth must not refer to
    # the temporary staging directory or the old project venv.
    env=dest/'controller/private/bridge-venv'
    venv.EnvBuilder(with_pip=False).create(env)
    spec=importlib.util.find_spec('serial')
    if spec is None or spec.submodule_search_locations is None:
        raise ValueError('pySerial is missing in the migration interpreter; use the old Bridge Python')
    site=subprocess.check_output([str(env/'bin/python'),'-c','import sysconfig;print(sysconfig.get_path("purelib"))'],text=True).strip()
    origin=Path(next(iter(spec.submodule_search_locations)))
    shutil.copytree(origin,Path(site)/'serial',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    for metadata in origin.parent.glob('pyserial-*.dist-info'):
        shutil.copytree(metadata,Path(site)/metadata.name)
    subprocess.run([str(env/'bin/python'),str(dest/'controller/scripts/setup_bridge_deps.py')],check=True,capture_output=True)
    subprocess.run([str(env/'bin/python'),'-c','import serial,ssl,websockets;assert serial.VERSION=="3.5";assert ssl.OPENSSL_VERSION.startswith("OpenSSL 3.")'],check=True,capture_output=True)
    base=Path(getattr(sys,'_base_executable',sys.executable)).resolve()
    local=dest/'controller/private/local-env.sh'
    # Quote paths as shell data, not interpolation or command substitution.
    local.write_text('export CONTROLLER_MODERN_PYTHON='+shlex.quote(str(base))+'\n')
    local.chmod(0o600)


def migrate(source,destination,runtime=None,build_env=True):
    source=source.resolve();destination=destination.expanduser().resolve()
    if destination==source or source in destination.parents:raise ValueError('Destination cannot be inside source')
    if destination.exists():raise FileExistsError('目标已存在，拒绝覆盖：'+str(destination))
    if not (source/'.git').is_dir():raise ValueError('Source must be a Git checkout')
    files=source_files(source)
    destination.parent.mkdir(parents=True,exist_ok=True)
    temp=destination.with_name('.'+destination.name+'-copying-'+uuid.uuid4().hex[:8])
    temp.mkdir(mode=0o700)
    records=[]
    try:
        shutil.copytree(source/'.git',temp/'.git')
        for rel in files:copy_checked(source/rel,temp/rel,records)
        if runtime is not None:
            runtime=Path(runtime).resolve()
            if not (runtime/'private').is_dir():raise ValueError('Old runtime private directory is unavailable')
            copy_runtime(runtime,temp,records)
        # All stable copied bytes have been verified; don't overwrite any existing target.
        if destination.exists():raise FileExistsError('目标在复制期间出现，已保留临时副本，拒绝覆盖。')
        temp.rename(destination)
        env_status='not_requested'
        if build_env:
            prepare_environment(destination);env_status='ready'
        receipt={'date':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_commit':subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip(),
                 'files_verified':len(records),'bytes_verified':sum(r['bytes'] for r in records),'private_copied':runtime is not None,
                 'environment':env_status,'live_services_changed':False,'hooks_changed':False,
                 'note':'Copy only; activate new App/Bridge and switch exact old Hook paths separately.'}
        p=destination/'LOCAL-MIGRATION-RECEIPT.json';p.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n');p.chmod(0o600)
        return receipt
    except BaseException:
        # Leave a recoverable copy for inspection. Never delete a partially
        # created destination or the original project's data on failure.
        raise


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination',type=Path,default=DEFAULT_DEST)
    parser.add_argument('--runtime-source',type=Path)
    parser.add_argument('--execute',action='store_true')
    args=parser.parse_args()
    runtime=args.runtime_source
    hint=ROOT/'LOCAL-MIGRATION-INPUT.json'
    if runtime is None and hint.exists():runtime=Path(json.loads(hint.read_text())['runtime_source'])
    print('目标：'+str(args.destination));print('复制后保留旧目录，不启动服务、不刷机、不改 Hooks。')
    if not args.execute:
        print('当前仅预览；添加 --execute 才执行。');return
    receipt=migrate(ROOT,args.destination,runtime)
    print('复制与校验完成：'+str(args.destination))
    print('校验文件数：'+str(receipt['files_verified'])+'；新 Bridge Python 环境已建立。')
    print('后续从新目录打开 Agent，先读 AGENTS.md。启用新服务前先停止旧 Bridge，并按交接文档切换旧 Hooks 绝对路径。')


if __name__=='__main__':
    try:main()
    except (OSError,ValueError,subprocess.SubprocessError) as error:sys.exit('迁移未完成，旧项目保留：'+str(error))
