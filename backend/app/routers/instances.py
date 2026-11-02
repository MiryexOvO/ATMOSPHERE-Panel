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
from ..core.security import require_user, can_access
from ..core.config import SERVER_ROOT
from ..infra.process_manager import get_process_manager, safe_instance_root
from ..services.server_properties import parse_properties, write_properties
from contextlib import closing
import re
import json
import sqlite3
import time

MONITOR_SAMPLES = {}
MONITOR_READINGS = {}

router=APIRouter(prefix='/api/instances',tags=['instances'])

@router.get('')
async def list_instances(request: Request):
    # 展示进程实况，不信任历史 running 标记。
    if isinstance((user:=require_user(request)),JSONResponse): return user
    conn=connect(); rows=conn.execute('SELECT id,name,port,jar_name,status,created_at FROM instances ORDER BY created_at DESC').fetchall(); conn.close()
    items = [dict(row) for row in rows if can_access(user, row['id'])]
    manager = get_process_manager()
    for item in items:
        if item['status'] != 'deploying':
            item['status'] = 'running' if await manager.is_running(item['id']) else ('error' if item['status'] == 'error' else 'stopped')
    return {'ok':True,'instances':items}

@router.get('/{instance_id}/monitor')
async def instance_monitor(request: Request, instance_id: str):
    if isinstance((user := require_user(request)), JSONResponse):
        return user
    manager = get_process_manager()
    pid = await manager.get_pid(instance_id)
    with closing(connect()) as conn:
        row = conn.execute('SELECT memory_mb FROM instances WHERE id=?',(instance_id,)).fetchone()
    if not row: return JSONResponse({'message':'实例不存在'},status_code=404)
    budget = row['memory_mb']
    empty = {'running':False,'pid':None,'cpu_percent':0.0,'host_cpu_percent':0.0,'memory_mb':0.0,'memory_percent':0.0,'allocated_mb':budget,'threads':0,'uptime_seconds':0,'read_bytes_per_second':0,'write_bytes_per_second':0,'total_read_bytes':0,'total_write_bytes':0,'io_available':True}
    if pid is None or psutil is None:
        MONITOR_SAMPLES.pop(instance_id,None)
        MONITOR_READINGS.pop(instance_id,None)
        return empty
    try:
        # 只采样此实例的 Java 进程树，不使用主机总占用。
        parent = psutil.Process(pid)
        processes = [parent, *parent.children(recursive=True)]
        cpu_total = memory = reads = writes = threads = 0
        io_available=True
        for process in processes:
            try:
                times=process.cpu_times();cpu_total+=times.user+times.system
                memory+=process.memory_info().rss;threads+=process.num_threads()
                try:
                    io=process.io_counters();reads+=io.read_bytes;writes+=io.write_bytes
                except (AttributeError,psutil.AccessDenied): io_available=False
            except (psutil.NoSuchProcess,psutil.AccessDenied): continue
        now=time.monotonic();identity=(pid,parent.create_time())
        previous=MONITOR_SAMPLES.get(instance_id)
        cpu=read_rate=write_rate=0.0
        if previous and previous[0]==identity:
            elapsed=max(now-previous[1],.001)
            # 多浏览器同时轮询共用短期读数，避免极短窗口放大抖动。
            if elapsed<.25 and instance_id in MONITOR_READINGS: return MONITOR_READINGS[instance_id]
            cpu=max(0,(cpu_total-previous[2])/elapsed*100)
            read_rate=max(0,(reads-previous[3])/elapsed);write_rate=max(0,(writes-previous[4])/elapsed)
        MONITOR_SAMPLES[instance_id]=(identity,now,cpu_total,reads,writes)
        # 首次打开等待一个短采样窗，避免全零占用误导用户。
        if not previous or previous[0]!=identity:
            await asyncio.sleep(.25)
            return await instance_monitor(request,instance_id)
        memory_mb=memory/1048576
        result={**empty,'running':True,'pid':pid,'cpu_percent':round(cpu,2),'host_cpu_percent':round(cpu/(psutil.cpu_count() or 1),2),
                'memory_mb':round(memory_mb,2),'memory_percent':round(memory_mb/budget*100,2),'threads':threads,
                'uptime_seconds':int(time.time()-parent.create_time()),'read_bytes_per_second':round(read_rate),'write_bytes_per_second':round(write_rate),'total_read_bytes':reads,'total_write_bytes':writes,'io_available':io_available}
        MONITOR_READINGS[instance_id]=result
        return result
    except (psutil.NoSuchProcess,psutil.AccessDenied): return empty

@router.get('/{instance_id}')
async def get_instance(request: Request, instance_id: str):
    # 实例状态以实际 Java 进程为准。
    if isinstance((user:=require_user(request)),JSONResponse): return user
    conn=connect(); row=conn.execute('SELECT id,name,port,jar_name,status,created_at,selected_core FROM instances WHERE id=?',(instance_id,)).fetchone(); conn.close()
    if not row: return JSONResponse({'ok':False,'message':'实例不存在'},status_code=404)
    result = dict(row)
    if result['status'] != 'deploying':
        result['status'] = 'running' if await get_process_manager().is_running(instance_id) else ('error' if result['status'] == 'error' else 'stopped')
    return result


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
    java_version: str = Field(default='21', pattern=r'^(8|17|21|25)$')
    java_path: str = Field(default='', max_length=1000)
    jar_name: str = Field(default='server.jar', min_length=1, max_length=255)
    jvm_args: str = Field(default='', max_length=2000)
    memory_mb: int = Field(ge=512, le=131072)
    rcon_enabled: bool = True
    rcon_port: int = Field(default=25575, ge=1, le=65535)
    rcon_password: str = Field(default='', max_length=256)
    auto_restart: bool = False
    ignore_eula: bool = False
    property_values: dict[str, str] | None = None
    secondary_port:int|None=Field(default=None,ge=1,le=65535)


@router.get('/{instance_id}/settings')
def get_settings(request: Request, instance_id: str):
    if isinstance((user := require_user(request)), JSONResponse):
        return user
    conn = connect()
    row = conn.execute(
        'SELECT name, port, jar_name, memory_mb, java_version, java_path, jvm_args, '
        'rcon_enabled, rcon_port, rcon_password, auto_restart, ignore_eula '
        'FROM instances WHERE id=?',
        (instance_id,),
    ).fetchone()
    conn.close()
    if row is None:
        return JSONResponse({'ok': False, 'message': '实例不存在'}, status_code=404)
    settings = dict(row)
    from ..services.runtime_modes import runtime_mode
    settings['runtime_mode']=runtime_mode(SERVER_ROOT/instance_id)
    with closing(connect()) as conn:
        settings['secondary_port']=conn.execute('SELECT secondary_port FROM instances WHERE id=?',(instance_id,)).fetchone()['secondary_port']
    for key in ('rcon_enabled', 'auto_restart', 'ignore_eula'):
        settings[key] = bool(settings[key])
    properties = SERVER_ROOT / instance_id / 'server.properties'
    settings['instance_path'] = str(SERVER_ROOT / instance_id)
    try:
        settings['property_values'] = parse_properties(properties.read_text(encoding='utf-8')) if properties.is_file() else {}
    except (OSError, UnicodeError) as exc:
        return JSONResponse({'ok': False, 'message': f'服务端属性读取失败: {exc}'}, status_code=500)
    # 单个连接字段异常，不清空整份属性。
    try:
        values = settings['property_values']
        settings['rcon_enabled'] = values.get('enable-rcon', str(settings['rcon_enabled']).lower()) == 'true'
        settings['rcon_password'] = values.get('rcon.password', settings['rcon_password'] or '')
        settings['rcon_port'] = int(values.get('rcon.port') or settings['rcon_port'] or 25575)
        eula = SERVER_ROOT / instance_id / 'eula.txt'
        settings['ignore_eula'] = eula.is_file() and parse_properties(eula.read_text(encoding='utf-8')).get('eula') == 'true'
    except (OSError, UnicodeError, ValueError):
        settings['rcon_port'] = settings['rcon_port'] or 25575
    return {'ok': True, 'settings': settings}


@router.put('/{instance_id}/settings')
async def update_settings(request: Request, instance_id: str, payload: SettingsPayload):
    # 停服后保存，防止游戏进程覆盖配置。
    if isinstance((user := require_user(request)), JSONResponse): return user
    if await get_process_manager().is_running(instance_id):
        return JSONResponse({'ok': False, 'message': '请先停止实例再保存设置，避免服务端覆盖配置文件'}, status_code=409)
    values = dict(payload.property_values or {})
    if len(values) > 300 or any(not re.fullmatch(r'[A-Za-z0-9_.-]+', key) or len(value) > 10000 for key, value in values.items()):
        return JSONResponse({'ok': False, 'message': '服务端属性键或值无效'}, status_code=422)
    try:
        if values.get('generator-settings'):
            json.loads(values['generator-settings'])
    except ValueError:
        return JSONResponse({'ok': False, 'message': '世界生成参数必须是有效 JSON'}, status_code=422)
    if payload.rcon_enabled and (not payload.rcon_password or payload.rcon_port == payload.port):
        return JSONResponse({'ok': False, 'message': '请设置 RCON 密码，并使用不同于游戏端口的 RCON 端口'}, status_code=422)
    with closing(connect()) as conn:
        conn.execute('BEGIN IMMEDIATE')
        if not conn.execute('SELECT 1 FROM instances WHERE id=?', (instance_id,)).fetchone():
            return JSONResponse({'ok': False, 'message': '实例不存在'}, status_code=404)
        if conn.execute('SELECT 1 FROM instances WHERE (port=? OR secondary_port=?) AND id<>?', (payload.port,payload.port,instance_id)).fetchone():
            return JSONResponse({'ok': False, 'message': '服务端端口已被占用'}, status_code=409)
        root = safe_instance_root(instance_id)
        from ..services.runtime_modes import runtime_mode
        if runtime_mode(root)=='bedrock':
            secondary=payload.secondary_port or int(values.get('server-portv6') or 19133)
            if secondary==payload.port or conn.execute('SELECT 1 FROM instances WHERE (port=? OR secondary_port=?) AND id<>?',(secondary,secondary,instance_id)).fetchone():
                return JSONResponse({'message':'IPv6 UDP 端口重复或已占用'},status_code=409)
            values['server-portv6']=str(secondary)
            conn.execute('UPDATE instances SET secondary_port=? WHERE id=?',(secondary,instance_id))
        target = (root / payload.jar_name.removeprefix('@')).resolve()
        if root not in target.parents or not target.is_file():
            return JSONResponse({'ok': False, 'message': '启动目标不存在或路径无效'}, status_code=422)
        values.update({'server-port': str(payload.port), 'enable-rcon': str(payload.rcon_enabled).lower(),
                       'rcon.port': str(payload.rcon_port), 'rcon.password': payload.rcon_password})
        properties = root / 'server.properties'
        # 同步文件与数据库，失败时恢复原配置。
        originals = {path: path.read_bytes() if path.exists() else None for path in (properties, root / 'eula.txt')}
        try:
            if properties.exists():
                shutil.copy2(properties, root / 'server.properties.panel-backup')
            write_properties(properties, values)
            write_properties(root / 'eula.txt', {'eula': str(payload.ignore_eula).lower()})
            conn.execute(
                'UPDATE instances SET name=?,port=?,jar_name=?,selected_core=?,memory_mb=?,java_version=?,java_path=?, '
                'jvm_args=?,rcon_enabled=?,rcon_port=?,rcon_password=?,auto_restart=?,ignore_eula=? WHERE id=?',
                (payload.name, payload.port, payload.jar_name, payload.jar_name, payload.memory_mb, payload.java_version,
                 payload.java_path, payload.jvm_args, int(payload.rcon_enabled), payload.rcon_port, payload.rcon_password,
                 int(payload.auto_restart), int(payload.ignore_eula), instance_id),
            )
            conn.commit()
        except (OSError, sqlite3.Error) as exc:
            conn.rollback()
            for path, content in originals.items():
                if content is not None:
                    path.write_bytes(content)
                elif path.exists():
                    path.unlink()
            return JSONResponse({'ok': False, 'message': f'配置写入失败: {exc}'}, status_code=500)
    return {'ok': True, 'restart_required': True}


class PowerPayload(BaseModel):
    action: str = Field(pattern='^(start|stop|restart)$')


@router.post('/{instance_id}/power')
async def power_instance(request: Request, instance_id: str, payload: PowerPayload):
    if isinstance((user := require_user(request)), JSONResponse):
        return user
    conn = connect()
    row = conn.execute('SELECT jar_name,selected_core,memory_mb,status,ignore_eula FROM instances WHERE id=?', (instance_id,)).fetchone()
    if row is None:
        conn.close()
        return JSONResponse({'ok': False, 'message': '实例不存在'}, status_code=404)
    if row['status'] == 'deploying':
        conn.close()
        return JSONResponse({'ok': False, 'message': '实例正在部署，请等待完成'}, status_code=409)
    next_status = 'running' if payload.action in {'start', 'restart'} else 'stopped'
    manager = get_process_manager()
    try:
        # 各平台均执行真实进程操作。
        if payload.action == 'stop':
            await manager.stop(instance_id)
        else:
            if payload.action == 'restart':
                await manager.stop(instance_id)
            await manager.start(instance_id, row['selected_core'] or row['jar_name'], row['memory_mb'])
    except (OSError, RuntimeError, ValueError) as exc:
        conn.close()
        return JSONResponse({'ok': False, 'message': str(exc)}, status_code=502)
    conn.execute('UPDATE instances SET status=? WHERE id=?', (next_status, instance_id))
    conn.commit()
    conn.close()
    from ..services.panel_settings import audit
    audit(user['id'],'instance.'+payload.action,instance_id)
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
async def instance_status(request: Request, instance_id: str):
    if isinstance((user:=require_user(request)),JSONResponse): return user
    conn=connect(); row=conn.execute('SELECT status FROM instances WHERE id=?',(instance_id,)).fetchone(); conn.close()
    if not row: return JSONResponse({'ok':False,'message':'实例不存在'}, status_code=404)
    status = row['status']
    if status != 'deploying':
        status = 'running' if await get_process_manager().is_running(instance_id) else ('error' if status == 'error' else 'stopped')
    return {'ok':True,'status':status}
