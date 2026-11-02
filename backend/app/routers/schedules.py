"""全局定时与多实例批量操作。"""
import asyncio, json
from contextlib import closing
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from ..core.database import connect
from ..core.security import require_user, can_access
from ..services.scheduler import next_run, execute
from ..services.operations import operate
from ..services.panel_settings import audit

router=APIRouter(prefix='/api',tags=['schedules'])


class SchedulePayload(BaseModel):
    name:str=Field(min_length=1,max_length=100)
    instance_id:str=Field(min_length=1,max_length=64)
    cron:str=Field(min_length=5,max_length=120)
    action:str=Field(pattern='^(start|stop|restart|command|backup)$')
    command:str=Field(default='',max_length=512)
    enabled:bool=True


def validate_access(user,instance_id,action):
    permission='command' if action=='command' else 'backups' if action=='backup' else 'power'
    if user['role']=='viewer' or not can_access(user,instance_id,'schedule') or not can_access(user,instance_id,permission): raise HTTPException(403,'没有任务操作权限')
    with closing(connect()) as conn:
        if not conn.execute('SELECT 1 FROM instances WHERE id=?',(instance_id,)).fetchone(): raise HTTPException(404,'实例不存在')


@router.get('/schedules')
def list_tasks(request:Request):
    if isinstance(user:=require_user(request),JSONResponse): return user
    with closing(connect()) as conn:
        tasks=[dict(row) for row in conn.execute('SELECT * FROM schedules ORDER BY instance_id,id') if can_access(user,row['instance_id'],'schedule') and (user['role']=='admin' or row['owner_id']==user['id'])]
    return {'tasks':tasks,'timezone':'UTC'}


@router.post('/schedules')
@router.put('/schedules/{task_id}')
async def save_task(request:Request,payload:SchedulePayload,task_id:int|None=None):
    if isinstance(user:=require_user(request),JSONResponse): return user
    validate_access(user,payload.instance_id,payload.action)
    if payload.action=='command' and (not payload.command.strip() or '\n' in payload.command or '\r' in payload.command): raise HTTPException(422,'请输入单行命令')
    try: upcoming=await asyncio.to_thread(next_run,payload.cron)
    except ValueError as exc: raise HTTPException(422,str(exc))
    values=(payload.name,payload.instance_id,payload.cron,payload.action,payload.command,int(payload.enabled),user['id'],upcoming)
    with closing(connect()) as conn:
        if task_id:
            row=conn.execute('SELECT owner_id FROM schedules WHERE id=?',(task_id,)).fetchone()
            if not row: raise HTTPException(404,'任务不存在')
            if user['role']!='admin' and row['owner_id']!=user['id']: raise HTTPException(403,'不可修改他人的任务')
            conn.execute('UPDATE schedules SET name=?,instance_id=?,cron=?,action=?,command=?,enabled=?,owner_id=?,next_run=? WHERE id=?',(*values,task_id))
        else: task_id=conn.execute('INSERT INTO schedules(name,instance_id,cron,action,command,enabled,owner_id,next_run) VALUES(?,?,?,?,?,?,?,?)',values).lastrowid
        conn.commit()
    audit(user['id'],'schedule.save',str(task_id));return {'ok':True,'id':task_id,'next_run':upcoming}


@router.post('/schedules/{task_id}/run')
async def run_task(request:Request,task_id:int):
    if isinstance(user:=require_user(request),JSONResponse): return user
    with closing(connect()) as conn: row=conn.execute('SELECT * FROM schedules WHERE id=?',(task_id,)).fetchone()
    if not row: raise HTTPException(404,'任务不存在')
    validate_access(user,row['instance_id'],row['action'])
    if user['role']!='admin' and row['owner_id']!=user['id']: raise HTTPException(403,'不可运行他人的任务')
    return {'result':await execute(dict(row))}


@router.delete('/schedules/{task_id}')
async def delete_task(request:Request,task_id:int):
    if isinstance(user:=require_user(request),JSONResponse): return user
    with closing(connect()) as conn:
        row=conn.execute('SELECT * FROM schedules WHERE id=?',(task_id,)).fetchone()
        if not row: raise HTTPException(404,'任务不存在')
        validate_access(user,row['instance_id'],row['action'])
        if user['role']!='admin' and row['owner_id']!=user['id']: raise HTTPException(403,'不可删除他人的任务')
        conn.execute('DELETE FROM schedules WHERE id=?',(task_id,));conn.commit()
    audit(user['id'],'schedule.delete',str(task_id));return {'ok':True}


class BatchPayload(BaseModel):
    instance_ids:list[str]=Field(min_length=1,max_length=50)
    action:str=Field(pattern='^(start|stop|restart|command)$')
    command:str=Field(default='',max_length=512)


@router.post('/batch')
async def batch(request:Request,payload:BatchPayload):
    if isinstance(user:=require_user(request),JSONResponse): return user
    ids=list(dict.fromkeys(payload.instance_ids))
    for instance_id in ids:
        if not can_access(user,instance_id,'command' if payload.action=='command' else 'power'): raise HTTPException(403,'没有所选实例的操作权限')
    semaphore=asyncio.Semaphore(4)
    async def run(instance_id):
        async with semaphore:
            try: return {'id':instance_id,'ok':True,'result':await operate(instance_id,payload.action,payload.command)}
            except Exception as exc: return {'id':instance_id,'ok':False,'result':str(exc)}
    results=await asyncio.gather(*(run(instance_id) for instance_id in ids))
    audit(user['id'],'batch.'+payload.action,json.dumps(results,ensure_ascii=False));return {'results':results}
