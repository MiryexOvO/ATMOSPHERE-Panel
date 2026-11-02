from fastapi import APIRouter, Request
from pydantic import BaseModel, Field
from fastapi.responses import JSONResponse, StreamingResponse
from ..core.security import require_user
from ..core.database import connect
from ..core.config import SERVER_ROOT
from ..services.rcon_service import execute_rcon_command
import json, re, sys
from ..infra.process_manager import get_process_manager, RUNNING_PROCESSES
router=APIRouter(prefix='/api/instances',tags=['console'])
INSTANCE_RE=re.compile(r'^[a-z0-9][a-z0-9-]{1,30}$')

class CommandPayload(BaseModel):
    command: str = Field(min_length=1, max_length=512)

@router.post('/{instance_id}/command')
async def command(request: Request, instance_id: str, payload: CommandPayload):
    if isinstance((user:=require_user(request)),JSONResponse): return user
    # 指令仅存摘要，避免插件登录密码进入审计明文。
    import hashlib
    from ..services.panel_settings import audit
    def audit_command(): audit(user['id'],'console.command',json.dumps({'instance':instance_id,'sha256':hashlib.sha256(payload.command.encode()).hexdigest()}))
    # 面板托管的进程直接写入 stdin，不依赖 RCON。
    process = RUNNING_PROCESSES.get(instance_id)
    if process and process.returncode is None and process.stdin:
        if '\n' in payload.command or '\r' in payload.command:
            return JSONResponse({'ok': False, 'message': '每次只能发送一条指令'}, status_code=422)
        try:
            process.stdin.write((payload.command.lstrip('/') + '\n').encode('utf-8'))
            await process.stdin.drain()
            audit_command()
            return {'ok': True, 'status': 'success', 'output': ''}
        except (BrokenPipeError, ConnectionResetError):
            return JSONResponse({'ok': False, 'message': '实例进程已退出'}, status_code=409)
    conn = connect()
    row = conn.execute('SELECT rcon_host, rcon_port, rcon_password, status, rcon_enabled FROM instances WHERE id=?', (instance_id,)).fetchone()
    conn.close()
    if not row or not row['rcon_enabled'] or not await get_process_manager().is_running(instance_id) or not row['rcon_password']:
        return JSONResponse({'ok': False, 'message': '实例未运行或 RCON 未配置'}, status_code=409)
    try:
        output = await execute_rcon_command(row['rcon_host'] or '127.0.0.1', int(row['rcon_port'] or 25575), row['rcon_password'], payload.command.lstrip('/'))
        audit_command()
        return {'ok': True, 'status': 'success', 'output': output}
    except (OSError, ValueError, RuntimeError) as exc:
        return JSONResponse({'ok': False, 'message': f'RCON 连接失败: {exc}'}, status_code=502)

@router.get('/{instance_id}/players')
async def players(request: Request, instance_id: str):
    if isinstance((user:=require_user(request)),JSONResponse): return user
    conn = connect()
    row = conn.execute('SELECT rcon_host, rcon_port, rcon_password, status, rcon_enabled FROM instances WHERE id=?', (instance_id,)).fetchone()
    conn.close()
    if not row or not row['rcon_enabled'] or not await get_process_manager().is_running(instance_id) or not row['rcon_password']:
        return JSONResponse({'ok': False, 'message': '实例未运行或 RCON 未配置'}, status_code=409)
    try:
        output = await execute_rcon_command(row['rcon_host'] or '127.0.0.1', int(row['rcon_port'] or 25575), row['rcon_password'], 'list')
        match = re.search(r'(\d+)\s+of\s+(?:a max of\s+)?(\d+)\s+players online', output, re.I)
        names = output.split(':', 1)[1].strip() if ':' in output else ''
        # 去掉服务端颜色控制码，只接受合法玩家名称。
        names=re.sub(r'§[0-9a-fk-or]','',names,flags=re.I)
        players = [name.strip() for name in names.split(',') if re.fullmatch(r'[A-Za-z0-9_]{1,16}',name.strip())] if names else []
        return {'ok': True, 'players': players, 'online': int(match.group(1)) if match else len(players), 'max': int(match.group(2)) if match else None, 'raw': output}
    except (OSError, ValueError, RuntimeError) as exc:
        return JSONResponse({'ok': False, 'message': f'RCON 连接失败: {exc}'}, status_code=502)

@router.get('/{instance_id}/logs/stream')
async def logs_stream(request: Request, instance_id: str):
    if isinstance((user := require_user(request)), JSONResponse):
        return user
    manager = get_process_manager()
    async def events():
        # 游戏状态与 SSE 传输状态分别报告。
        yield f'event: state\ndata: {json.dumps({"running": await manager.is_running(instance_id)})}\n\n'
        # 独立心跳避免日志繁忙或 Linux journal 阻塞状态更新。
        import asyncio, time
        last_state=time.monotonic()
        lines=manager.get_logs(instance_id).__aiter__()
        pending=asyncio.create_task(anext(lines))
        try:
            while not await request.is_disconnected():
                done,_=await asyncio.wait({pending},timeout=3)
                if pending in done:
                    try: line=pending.result()
                    except StopAsyncIteration: break
                    if line: yield f'data: {json.dumps({"line": line},ensure_ascii=False)}\n\n'
                    pending=asyncio.create_task(anext(lines))
                if time.monotonic()-last_state>=3:
                    yield f'event: state\ndata: {json.dumps({"running":await manager.is_running(instance_id)})}\n\n'
                    last_state=time.monotonic()
                    if isinstance(require_user(request),JSONResponse): break
        finally:
            pending.cancel();await asyncio.gather(pending,return_exceptions=True)
            await lines.aclose()
    return StreamingResponse(events(), media_type='text/event-stream', headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})
