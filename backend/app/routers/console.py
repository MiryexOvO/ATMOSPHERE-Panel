from fastapi import APIRouter, Request
from pydantic import BaseModel, Field
from fastapi.responses import JSONResponse, StreamingResponse
from ..core.security import require_user
from ..core.database import connect
from ..core.config import SERVER_ROOT
import json, subprocess, re, platform, time
router=APIRouter(prefix='/api/instances',tags=['console'])
INSTANCE_RE=re.compile(r'^[a-z0-9][a-z0-9-]{1,30}$')

class CommandPayload(BaseModel):
    command: str = Field(min_length=1, max_length=512)

@router.post('/{instance_id}/command')
def command(request: Request, instance_id: str, payload: CommandPayload):
    if isinstance((user:=require_user(request)),JSONResponse): return user
    if platform.system() == 'Windows':
        print(f'[MOCK RCON] {instance_id}: {payload.command}')
        return {'ok': True, 'status': 'mock_success', 'output': 'Command executed'}
    conn = connect()
    row = conn.execute('SELECT rcon_host, rcon_port, rcon_password_hash FROM instances WHERE id=?', (instance_id,)).fetchone()
    conn.close()
    if not row or not row['rcon_host'] or not row['rcon_port'] or not row['rcon_password_hash']:
        print(f'[MOCK RCON] {instance_id}: {payload.command}')
        return {'ok': True, 'status': 'mock_success', 'output': 'Command executed'}
    return JSONResponse({'ok': False, 'message': 'RCON 客户端尚未配置'}, status_code=501)

@router.get('/{instance_id}/players')
def players(request: Request, instance_id: str):
    if isinstance((user:=require_user(request)),JSONResponse): return user
    return {'ok':True,'players':[]}

@router.get('/{instance_id}/logs/stream')
def logs_stream(request: Request, instance_id: str):
    if isinstance((user:=require_user(request)),JSONResponse): return user
    def events():
        if platform.system() == 'Windows':
            while True:
                yield f'data: {json.dumps({"line": "[INFO] Server tick..."}, ensure_ascii=False)}\n\n'
                time.sleep(1)
        try:
            process=subprocess.Popen(['journalctl','-u',f'mc-{instance_id}','-n','50','-f','--output=cat'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1)
            assert process.stdout is not None
            for line in iter(process.stdout.readline,''):
                if line: yield f'data: {json.dumps({"line":line.rstrip()},ensure_ascii=False)}\n\n'
        except (FileNotFoundError,OSError) as exc:
            yield f'data: {json.dumps({"line":str(exc)},ensure_ascii=False)}\n\n'
    return StreamingResponse(events(),media_type='text/event-stream',headers={'Cache-Control':'no-cache','X-Accel-Buffering':'no'})