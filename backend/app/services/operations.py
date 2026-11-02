"""实例操作供控制台、批量操作和调度器共用。"""
from contextlib import closing
from ..core.database import connect
from ..infra.process_manager import get_process_manager, RUNNING_PROCESSES
from .rcon_service import execute_rcon_command
import asyncio, os, secrets, time, zipfile


async def send_command(instance_id, command):
    # 优先使用托管进程的标准输入，否则通过 RCON 发送。
    if not command.strip() or len(command) > 512 or '\n' in command or '\r' in command:
        raise ValueError('每次只能发送一条有效指令')
    process = RUNNING_PROCESSES.get(instance_id)
    if process and process.returncode is None and process.stdin:
        process.stdin.write((command.lstrip('/') + '\n').encode())
        await process.stdin.drain()
        return ''
    with closing(connect()) as conn:
        row = conn.execute('SELECT * FROM instances WHERE id=?',(instance_id,)).fetchone()
    if not row or not row['rcon_enabled'] or not row['rcon_password'] or not await get_process_manager().is_running(instance_id):
        raise ValueError('实例未运行或 RCON 未配置')
    return await execute_rcon_command(row['rcon_host'] or '127.0.0.1',row['rcon_port'] or 25575,row['rcon_password'],command.lstrip('/'))


async def operate(instance_id, action, command=''):
    if action == 'command': return await send_command(instance_id,command)
    with closing(connect()) as conn:
        row = conn.execute('SELECT * FROM instances WHERE id=?',(instance_id,)).fetchone()
    if not row: raise ValueError('实例不存在')
    if row['status'] == 'deploying': raise ValueError('实例正在部署')
    manager = get_process_manager()
    if action=='backup':
        # 停服备份保证世界一致，失败不会遗留完整文件名。
        from ..infra.process_manager import safe_instance_root
        if await manager.is_running(instance_id): raise ValueError('一致性备份需要先停止实例')
        root=safe_instance_root(instance_id);directory=root/'backups'
        if directory.is_symlink(): raise ValueError('备份目录不能是链接')
        directory.mkdir(exist_ok=True)
        target=directory/('scheduled-'+time.strftime('%Y%m%d-%H%M%S')+'-'+secrets.token_hex(3)+'.zip')
        temporary=target.with_suffix('.part')
        def pack():
            with zipfile.ZipFile(temporary,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=1) as archive:
                for base,folders,files in os.walk(root,followlinks=False):
                    from pathlib import Path
                    folders[:]=[name for name in folders if name not in {'backups','.runtime-tmp','.install-tmp'} and not (Path(base)/name).is_symlink()]
                    for name in files:
                        path=Path(base)/name
                        if not path.is_symlink() and root.resolve() in path.resolve().parents: archive.write(path,path.relative_to(root))
            temporary.replace(target)
        try: await asyncio.to_thread(pack)
        finally: temporary.unlink(missing_ok=True)
        return target.name
    if action in {'stop','restart'}: await manager.stop(instance_id)
    if action in {'start','restart'}:
        await manager.start(instance_id,row['selected_core'] or row['jar_name'],row['memory_mb'])
    if action not in {'start','stop','restart'}: raise ValueError('不支持的操作')
    with closing(connect()) as conn:
        conn.execute('UPDATE instances SET status=? WHERE id=?',('stopped' if action=='stop' else 'running',instance_id));conn.commit()
    return action
