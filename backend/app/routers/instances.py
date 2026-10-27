from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from ..core.database import connect
from ..core.security import require_user

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

@router.get('/{instance_id}/status')
def instance_status(request: Request, instance_id: str):
    if isinstance((user:=require_user(request)),JSONResponse): return user
    conn=connect(); row=conn.execute('SELECT status FROM instances WHERE id=?',(instance_id,)).fetchone(); conn.close()
    return {'ok':True,'status':row['status'] if row else 'unknown'}
