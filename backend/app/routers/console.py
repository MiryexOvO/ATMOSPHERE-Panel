from fastapi import APIRouter, Request
from pydantic import BaseModel, Field
from fastapi.responses import JSONResponse, StreamingResponse
from ..core.security import require_user
from ..core.database import connect
from ..core.config import SERVER_ROOT
from ..services.rcon_service import execute_rcon_command
import json, re, sys
from ..infra.process_manager import get_process_manager
router=APIRouter(prefix='/api/instances',tags=['console'])
INSTANCE_RE=re.compile(r'^[a-z0-9][a-z0-9-]{1,30}$')

class CommandPayload(BaseModel):
    command: str = Field(min_length=1, max_length=512)

@router.post('/{instance_id}/command')
async def command(request: Request, instance_id: str, payload: CommandPayload):
    if isinstance((user:=require_user(request)),JSONResponse): return user
    if sys.platform.startswith('win'):
        return JSONResponse({'ok': False, 'message': 'Windows 下 RCON 不可用，请确认服务器运行环境'}, status_code=503)
    conn = connect()
    row = conn.execute('SELECT rcon_host, rcon_port, rcon_password, status FROM instances WHERE id=?', (instance_id,)).fetchone()
    conn.close()
    if not row or row['status'] == 'stopped' or not row['rcon_password']:
        return JSONResponse({'ok': False, 'message': '实例未运行或 RCON 未配置'}, status_code=409)
    try:
        output = await execute_rcon_command(row['rcon_host'] or '127.0.0.1', int(row['rcon_port'] or 25575), row['rcon_password'], payload.command.lstrip('/'))
        return {'ok': True, 'status': 'success', 'output': output}
    except (OSError, ValueError, RuntimeError) as exc:
        return JSONResponse({'ok': False, 'message': f'RCON 连接失败: {exc}'}, status_code=502)

@router.get('/{instance_id}/players')
async def players(request: Request, instance_id: str):
    if isinstance((user:=require_user(request)),JSONResponse): return user
    if sys.platform.startswith('win'):
        return JSONResponse({'ok': False, 'message': 'Windows 下无法读取真实玩家列表'}, status_code=503)
    conn = connect()
    row = conn.execute('SELECT rcon_host, rcon_port, rcon_password, status FROM instances WHERE id=?', (instance_id,)).fetchone()
    conn.close()
    if not row or row['status'] == 'stopped' or not row['rcon_password']:
        return JSONResponse({'ok': False, 'message': '实例未运行或 RCON 未配置'}, status_code=409)
    try:
        output = await execute_rcon_command(row['rcon_host'] or '127.0.0.1', int(row['rcon_port'] or 25575), row['rcon_password'], 'list')
        match = re.search(r':\s*(\d+)\s+of\s+(\d+)\s+players online', output, re.I)
        names = output.split(':', 1)[1].strip() if ':' in output else ''
        players = [name.strip() for name in names.split(',') if name.strip()] if names else []
        return {'ok': True, 'players': players, 'online': int(match.group(1)) if match else len(players), 'max': int(match.group(2)) if match else None, 'raw': output}
    except (OSError, ValueError, RuntimeError) as exc:
        return JSONResponse({'ok': False, 'message': f'RCON 连接失败: {exc}'}, status_code=502)

@router.get('/{instance_id}/logs/stream')
async def logs_stream(request: Request, instance_id: str):
    if isinstance((user := require_user(request)), JSONResponse):
        return user
    manager = get_process_manager()
    async def events():
        async for line in manager.get_logs(instance_id):
            yield f'data: {json.dumps({"line": line}, ensure_ascii=False)}\n\n'
    return StreamingResponse(events(), media_type='text/event-stream', headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})