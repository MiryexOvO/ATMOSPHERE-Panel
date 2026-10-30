from fastapi import APIRouter, Request
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
from ..services.systemd_service import SystemdService

router=APIRouter(prefix='/api/instances',tags=['instances'])

@router.get('')
def list_instances(request: Request):
    if isinstance((user:=require_user(request)),JSONResponse): return user
    conn=connect(); rows=conn.execute('SELECT id,name,port,jar_name,status,created_at FROM instances ORDER BY created_at DESC').fetchall(); conn.close()
    return {'ok':True,'instances':[dict(row) for row in rows]}

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

class PowerPayload(BaseModel):
    action: str = Field(pattern='^(start|stop|restart)$')


@router.post('/{instance_id}/power')
def power_instance(request: Request, instance_id: str, payload: PowerPayload):
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
    service = SystemdService()
    action = 'restart' if payload.action == 'restart' else payload.action
    code, output = service.run(action, f'mc-{instance_id}')
    if code != 0:
        conn.close()
        return JSONResponse({'ok': False, 'message': output or 'systemd 操作失败'}, status_code=502)
    conn.execute('UPDATE instances SET status=? WHERE id=?', (next_status, instance_id))
    conn.commit()
    conn.close()
    return {'ok': True, 'instance_id': instance_id, 'action': payload.action, 'status': next_status}


@router.delete('/{instance_id}')
def delete_instance(request: Request, instance_id: str):
    if isinstance((user := require_user(request)), JSONResponse):
        return user
    conn = connect()
    row = conn.execute('SELECT id FROM instances WHERE id=?', (instance_id,)).fetchone()
    if row is None:
        conn.close()
        return JSONResponse({'ok': False, 'message': '实例不存在'}, status_code=404)
    if platform.system() != 'Windows':
        SystemdService().run('stop', f'mc-{instance_id}')
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