from fastapi import APIRouter, Request
import asyncio
from pydantic import BaseModel, Field
import os
import platform
import shutil

try:
    import psutil
except ImportError:
    psutil = None
from fastapi.responses import JSONResponse
from ..core.database import connect
from ..core.security import require_user
from ..core.config import SERVER_ROOT
from ..infra.process_manager import get_process_manager

router=APIRouter(prefix='/api/instances',tags=['instances'])

@router.get('')
def list_instances(request: Request):
    if isinstance((user:=require_user(request)),JSONResponse): return user
    conn=connect(); rows=conn.execute('SELECT id,name,port,jar_name,status,created_at FROM instances ORDER BY created_at DESC').fetchall(); conn.close()
    return {'ok':True,'instances':[dict(row) for row in rows]}

@router.get('/{instance_id}/monitor')
async def instance_monitor(request: Request, instance_id: str):
    if isinstance((user := require_user(request)), JSONResponse):
        return user
    manager = get_process_manager()
    pid = await manager.get_pid(instance_id)
    if pid is None or psutil is None:
        return {'running': False, 'pid': None, 'cpu_percent': 0.0, 'memory_mb': 0.0}
    try:
        process = psutil.Process(pid)
        cpu = await asyncio.to_thread(process.cpu_percent, 0.05)
        memory_mb = process.memory_info().rss / (1024 * 1024)
        return {'running': process.is_running(), 'pid': pid, 'cpu_percent': cpu, 'memory_mb': round(memory_mb, 2)}
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return {'running': False, 'pid': None, 'cpu_percent': 0.0, 'memory_mb': 0.0}

@router.get('/{instance_id}')
def get_instance(request: Request, instance_id: str):
    if isinstance((user:=require_user(request)),JSONResponse): return user
    conn=connect(); row=conn.execute('SELECT id,name,port,jar_name,status,created_at,selected_core FROM instances WHERE id=?',(instance_id,)).fetchone(); conn.close()
    return dict(row) if row else JSONResponse({'ok':False,'message':'实例不存在'},status_code=404)


@router.get('/system/metrics')
def system_metrics(request: Request):
    if isinstance((user := require_user(request)), JSONResponse): return user
    cpu = psutil.cpu_percent(interval=0.05) if psutil else 0.0
    memory = psutil.virtual_memory().percent if psutil else 0.0
    cores = psutil.cpu_percent(interval=0.05, percpu=True) if psutil else []
    return {'panel': 'ATMOSPHERE / 02', 'cpu': cpu, 'memory': memory, 'cores': cores, 'platform': os.name, 'hostname': os.getenv('COMPUTERNAME') or os.getenv('HOSTNAME') or 'unknown', 'release': os.getenv('OS') or 'unknown'}

class SettingsPayload(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    port: int = Field(ge=1, le=65535)
    java_version: str = Field(default='21', pattern=r'^(8|17|21)$')
    jar_name: str = Field(default='server.jar', min_length=1, max_length=255)
    jvm_args: str = Field(default='', max_length=2000)
    memory_mb: int = Field(ge=512, le=131072)
    rcon_enabled: bool = True
    rcon_port: int = Field(default=25575, ge=1, le=65535)
    rcon_password: str = Field(default='', max_length=256)
    auto_restart: bool = False
    ignore_eula: bool = False
    server_properties: str | None = None


@router.get('/{instance_id}/settings')
def get_settings(request: Request, instance_id: str):
    if isinstance((user := require_user(request)), JSONResponse):
        return user
    conn = connect()
    row = conn.execute(
        'SELECT name, port, jar_name, memory_mb, java_version, jvm_args, '
        'rcon_enabled, rcon_port, rcon_password, auto_restart, ignore_eula '
        'FROM instances WHERE id=?',
        (instance_id,),
    ).fetchone()
    conn.close()
    if row is None:
        return JSONResponse({'ok': False, 'message': '实例不存在'}, status_code=404)
    settings = dict(row)
    properties = SERVER_ROOT / instance_id / 'server.properties'
    settings['instance_path'] = str(SERVER_ROOT / instance_id)
    try:
        settings['server_properties'] = properties.read_text(encoding='utf-8') if properties.is_file() else ''
    except (OSError, UnicodeError):
        settings['server_properties'] = ''
    return {'ok': True, 'settings': settings}


@router.put('/{instance_id}/settings')
def update_settings(request: Request, instance_id: str, payload: SettingsPayload):
    if isinstance((user := require_user(request)), JSONResponse):
        return user
    conn = connect()
    row = conn.execute(
        'SELECT memory_mb, jar_name FROM instances WHERE id=?', (instance_id,)
    ).fetchone()
    if row is None:
        conn.close()
        return JSONResponse({'ok': False, 'message': '实例不存在'}, status_code=404)
    conflict = conn.execute(
        'SELECT 1 FROM instances WHERE port=? AND id<>?', (payload.port, instance_id)
    ).fetchone()
    if conflict:
        conn.close()
        return JSONResponse({'ok': False, 'message': '服务端端口已被占用'}, status_code=409)
    conn.execute(
        'UPDATE instances SET name=?, port=?, jar_name=?, memory_mb=?, java_version=?, '
        'jvm_args=?, rcon_enabled=?, rcon_port=?, rcon_password=?, auto_restart=?, ignore_eula=? WHERE id=?',
        (payload.name, payload.port, payload.jar_name, payload.memory_mb, payload.java_version,
         payload.jvm_args, int(payload.rcon_enabled), payload.rcon_port, payload.rcon_password,
         int(payload.auto_restart), int(payload.ignore_eula), instance_id),
    )
    conn.commit()
    if platform.system() != 'Windows':
        properties = SERVER_ROOT / instance_id / 'server.properties'
        properties.parent.mkdir(parents=True, exist_ok=True)
        if payload.server_properties is not None:
            properties.write_text(payload.server_properties, encoding='utf-8')
        lines = properties.read_text(encoding='utf-8').splitlines() if properties.exists() else []
        values = {
            'server-port': str(payload.port),
            'enable-rcon': str(payload.rcon_enabled).lower(),
            'rcon.port': str(payload.rcon_port),
            'rcon.password': payload.rcon_password,
            'eula': 'true' if payload.ignore_eula else 'false',
        }
        keys, output = set(), []
        for line in lines:
            key = line.split('=', 1)[0]
            if key in values:
                output.append(f'{key}={values[key]}'); keys.add(key)
            else:
                output.append(line)
        output.extend(f'{key}={value}' for key, value in values.items() if key not in keys)
        properties.write_text('\n'.join(output) + '\n', encoding='utf-8')
        service = SystemdService()
        service.create_unit(instance_id, payload.jar_name, payload.memory_mb)
        code, output = service.run('daemon-reload')
        if code != 0:
            conn.close()
            return JSONResponse({'ok': False, 'message': output or 'systemd daemon-reload 失败'}, status_code=502)
    conn.close()
    return {'ok': True, 'settings': payload.model_dump(), 'restart_required': row['memory_mb'] != payload.memory_mb}


class PowerPayload(BaseModel):
    action: str = Field(pattern='^(start|stop|restart)$')


@router.post('/{instance_id}/power')
async def power_instance(request: Request, instance_id: str, payload: PowerPayload):
    if isinstance((user := require_user(request)), JSONResponse):
        return user
    conn = connect()
    row = conn.execute('SELECT id FROM instances WHERE id=?', (instance_id,)).fetchone()
    if row is None:
        conn.close()
        return JSONResponse({'ok': False, 'message': '实例不存在'}, status_code=404)
    next_status = 'running' if payload.action in {'start', 'restart'} else 'stopped'
    if platform.system() == 'Windows':
        conn.execute('UPDATE instances SET status=? WHERE id=?', (next_status, instance_id))
        conn.commit()
        conn.close()
        return {'ok': True, 'instance_id': instance_id, 'action': payload.action, 'status': next_status, 'mock': True}
    manager = get_process_manager()
    try:
        if payload.action == 'stop':
            await manager.stop(instance_id)
        else:
            await manager.start(instance_id)
    except (OSError, RuntimeError, ValueError) as exc:
        conn.close()
        return JSONResponse({'ok': False, 'message': str(exc)}, status_code=502)
    conn.execute('UPDATE instances SET status=? WHERE id=?', (next_status, instance_id))
    conn.commit()
    conn.close()
    return {'ok': True, 'instance_id': instance_id, 'action': payload.action, 'status': next_status}


@router.delete('/{instance_id}')
async def delete_instance(request: Request, instance_id: str):
    if isinstance((user := require_user(request)), JSONResponse):
        return user
    conn = connect()
    row = conn.execute('SELECT id FROM instances WHERE id=?', (instance_id,)).fetchone()
    if row is None:
        conn.close()
        return JSONResponse({'ok': False, 'message': '实例不存在'}, status_code=404)
    await get_process_manager().stop(instance_id)
    conn.execute('DELETE FROM instances WHERE id=?', (instance_id,))
    conn.commit()
    conn.close()
    shutil.rmtree(SERVER_ROOT / instance_id, ignore_errors=True)
    return {'ok': True, 'instance_id': instance_id, 'deleted': True}


@router.get('/{instance_id}/status')
def instance_status(request: Request, instance_id: str):
    if isinstance((user:=require_user(request)),JSONResponse): return user
    conn=connect(); row=conn.execute('SELECT status FROM instances WHERE id=?',(instance_id,)).fetchone(); conn.close()
    return {'ok':True,'status':row['status'] if row else 'unknown'}