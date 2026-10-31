from fastapi import APIRouter, Request, UploadFile, File, Form
from fastapi.responses import StreamingResponse
import asyncio, json, httpx
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from ..core.security import require_user
from ..core.database import connect
from ..core.config import SERVER_ROOT, ROOT, MAX_PACKAGE_BYTES
from ..archive_service import extract_archive, find_core_candidates
from pathlib import Path
import secrets, shutil, time, platform
from ..infra.process_manager import get_process_manager

router = APIRouter(prefix='/api', tags=['deployments'])
deploy_events: dict[str, asyncio.Queue] = {}

class DeployPayload(BaseModel):
    instance_id: str
    core_type: str
    mc_version: str
    build_version: str

async def run_deploy_task(instance_id: str, core_type: str, mc_version: str, build_version: str):
    queue = deploy_events[instance_id]
    async def report(progress: int, status: str):
        await queue.put({'progress': progress, 'status': status})
    try:
        await report(10, '正在解析核心信息...')
        root = SERVER_ROOT / instance_id
        root.mkdir(parents=True, exist_ok=True)
        jar = root / 'server.jar'
        await report(20, '正在下载核心...')
        url = 'https://api.fastmirror.net/v1/projects/' + core_type + '/versions/' + mc_version + '/builds/' + build_version + '/downloads/server:default/download'
        async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
            async with client.stream('GET', url) as response:
                response.raise_for_status()
                total = int(response.headers.get('content-length') or 0)
                downloaded = 0
                with jar.open('wb') as output:
                    async for chunk in response.aiter_bytes(1024 * 1024):
                        output.write(chunk)
                        downloaded += len(chunk)
                        progress = 20 + int(downloaded / total * 70) if total else 0
                        await report(progress, '正在下载核心...')
        if not jar.is_file() or jar.stat().st_size == 0:
            raise RuntimeError('核心下载完成但文件为空')
        password = secrets.token_urlsafe(24)
        (root / 'server.properties').write_text(f'server-port=25565\nenable-rcon=true\nrcon.port=25575\nrcon.password={password}\n', encoding='utf-8')
        conn = connect()
        password = secrets.token_urlsafe(24)
        properties = root / 'server.properties'
        properties.write_text('server-port=25565\nenable-rcon=true\nrcon.port=25575\nrcon.password=' + password + '\n', encoding='utf-8')
        conn.execute('INSERT INTO instances (id,name,port,jar_name,status,created_at,core_candidates,selected_core,rcon_host,rcon_port,rcon_password_hash,rcon_password) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)', (instance_id, instance_id, 25565, jar.name, 'stopped', int(time.time()), '[]', jar.name, '127.0.0.1', 25575, None, password))
        conn.commit()
        conn.close()
        await get_process_manager().start(instance_id, jar.name, 4096)
        await report(100, '部署完成！')
    except Exception as exc:
        await report(100, f'部署失败: {exc}')
    finally:
        await queue.put(None)

@router.post('/instances/deploy')
async def start_deploy(request: Request, payload: DeployPayload):
    if isinstance((user := require_user(request)), JSONResponse): return user
    deploy_events[payload.instance_id] = asyncio.Queue()
    asyncio.create_task(run_deploy_task(payload.instance_id, payload.core_type, payload.mc_version, payload.build_version))
    return {'ok': True, 'instance_id': payload.instance_id}

@router.get('/instances/deploy/stream/{instance_id}')
async def deploy_stream(request: Request, instance_id: str):
    if isinstance((user := require_user(request)), JSONResponse): return user
    queue = deploy_events.get(instance_id)
    if queue is None: return JSONResponse({'ok': False, 'message': '部署任务不存在'}, status_code=404)
    async def events():
        while True:
            event = await queue.get()
            if event is None: break
            yield f'data: {json.dumps(event, ensure_ascii=False)}\n\n'
    return StreamingResponse(events(), media_type='text/event-stream')


class ModePayload(BaseModel):
    mode: str
    instance_id: str
    port: int = Field(ge=1, le=65535)
    version: str = ''
    resource: str = ''
    java_version: str = '21'
    memory: int = Field(default=4096, ge=512, le=131072)

@router.post('/deploy/modes')
def deploy_mode(request: Request, payload: ModePayload):
    if isinstance((user := require_user(request)), JSONResponse):
        return user
    instance_id = payload.instance_id.lower()
    if payload.mode not in {'quick', 'bedrock', 'mcdr'}:
        return JSONResponse({'ok': False, 'message': '部署模式无效'}, status_code=400)
    if not instance_id or not instance_id.replace('-', '').isalnum():
        return JSONResponse({'ok': False, 'message': '实例 ID 无效'}, status_code=400)
    if payload.mode == 'bedrock':
        return JSONResponse({'ok': False, 'message': '基岩版下载源尚未配置，请先配置 Bedrock 官方镜像'}, status_code=503)
    conn = connect()
    if conn.execute('SELECT 1 FROM instances WHERE id=? OR port=?', (instance_id, payload.port)).fetchone():
        conn.close()
        return JSONResponse({'ok': False, 'message': '实例 ID 或端口已存在'}, status_code=409)
    root = SERVER_ROOT / instance_id
    try:
        root.mkdir(parents=True, exist_ok=False)
        (root / 'eula.txt').write_text('eula=true\n', encoding='utf-8')
        rcon_password = secrets.token_urlsafe(24)
        (root / 'server.properties').write_text(
            f'server-port={payload.port}\n'
            'enable-rcon=true\n'
            'rcon.port=25575\n'
            f'rcon.password={rcon_password}\n',
            encoding='utf-8',
        )
        selected = 'start_mcdr.py' if payload.mode == 'mcdr' else 'server.jar'
        if payload.mode == 'quick':
            (root / selected).write_bytes(b'')
        if payload.mode == 'mcdr':
            (root / selected).write_text('from mcdreforged.api.all import ServerInterface\n', encoding='utf-8')
        conn.execute(
            'INSERT INTO instances '
            '(id, name, port, jar_name, status, created_at, core_candidates, selected_core, '
            'rcon_host, rcon_port, rcon_password_hash, rcon_password) '
            'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
            (instance_id, instance_id, payload.port, selected, 'stopped', int(time.time()),
             '[]', selected, '127.0.0.1', 25575, None, rcon_password),
        )
        conn.commit()
        status = 'stopped'
        if platform.system() != 'Windows':
            code, output = SystemdService().deploy(instance_id, selected, payload.memory)
            if code != 0:
                raise RuntimeError(output or 'systemd 启动失败')
            status = 'running'
            conn.execute('UPDATE instances SET status=? WHERE id=?', (status, instance_id))
            conn.commit()
        return {'ok': True, 'mode': payload.mode, 'instance': {'id': instance_id}, 'status': status}
    except Exception as exc:
        shutil.rmtree(root, ignore_errors=True)
        conn.rollback()
        return JSONResponse({'ok': False, 'message': f'部署失败: {exc}'}, status_code=502)
    finally:
        conn.close()

@router.post('/instances/package')
async def upload_package(request: Request, package: UploadFile = File(...), instance_id: str = Form(...), port: int = Form(...)):
    if isinstance((user := require_user(request)), JSONResponse):
        return user
    filename = (package.filename or '').lower()
    if not filename.endswith(('.zip', '.tar.gz', '.tgz')):
        return JSONResponse({'ok': False, 'message': '仅支持 ZIP、TAR.GZ 或 TGZ'}, status_code=400)
    instance_id = instance_id.lower()
    if not instance_id or not instance_id.replace('-', '').isalnum() or not (1 <= port <= 65535):
        return JSONResponse({'ok': False, 'message': '实例 ID 或端口无效'}, status_code=400)
    temp = ROOT / 'tmp-packages'
    temp.mkdir(exist_ok=True)
    archive = temp / f'{secrets.token_hex(12)}-{Path(filename).name}'
    target = temp / f'package-{secrets.token_hex(8)}'
    root = SERVER_ROOT / instance_id
    conn = connect()
    try:
        if conn.execute('SELECT 1 FROM instances WHERE id=? OR port=?', (instance_id, port)).fetchone():
            return JSONResponse({'ok': False, 'message': '实例 ID 或端口已存在'}, status_code=409)
        total = 0
        with archive.open('wb') as output:
            while chunk := await package.read(1024 * 1024):
                total += len(chunk)
                if total > MAX_PACKAGE_BYTES:
                    raise ValueError('整合包超过 500MB 限制')
                output.write(chunk)
        extract_archive(archive, target)
        candidates = find_core_candidates(target)
        selected = next((item['path'] for item in candidates if item.get('recommended')), None)
        if not selected:
            raise ValueError('整合包中未找到可用服务端核心')
        root.mkdir(parents=True, exist_ok=False)
        shutil.copytree(target, root, dirs_exist_ok=True)
        rcon_password = secrets.token_urlsafe(24)
        properties = root / 'server.properties'
        existing = properties.read_text(encoding='utf-8') if properties.exists() else ''
        properties.write_text(
            existing.rstrip('\n') + '\n'
            'enable-rcon=true\n'
            'rcon.port=25575\n'
            f'rcon.password={rcon_password}\n',
            encoding='utf-8',
        )
        conn.execute(
            'INSERT INTO instances '
            '(id, name, port, jar_name, status, created_at, core_candidates, selected_core, '
            'rcon_host, rcon_port, rcon_password_hash, rcon_password) '
            'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
            (instance_id, instance_id, port, Path(selected).name, 'stopped', int(time.time()),
             str(candidates), selected, '127.0.0.1', 25575, None, rcon_password),
        )
        conn.commit()
        status = 'stopped'
        if platform.system() != 'Windows':
            code, output = SystemdService().deploy(instance_id, Path(selected).name)
            if code != 0:
                raise RuntimeError(output or 'systemd 启动失败')
            status = 'running'
            conn.execute('UPDATE instances SET status=? WHERE id=?', (status, instance_id))
            conn.commit()
        return {'ok': True, 'instance': {'id': instance_id, 'name': instance_id, 'port': port}, 'selected_core': selected, 'status': status}
    except Exception as exc:
        shutil.rmtree(root, ignore_errors=True)
        conn.rollback()
        return JSONResponse({'ok': False, 'message': f'部署失败: {exc}'}, status_code=400)
    finally:
        conn.close()
        archive.unlink(missing_ok=True)
        shutil.rmtree(target, ignore_errors=True)


@router.post('/instances/package/inspect')
async def inspect_package(request: Request, package: UploadFile = File(...)):
    if isinstance((user := require_user(request)), JSONResponse):
        return user
    filename = (package.filename or '').lower()
    if not filename.endswith(('.zip', '.tar.gz', '.tgz')):
        return JSONResponse({'ok': False, 'message': '仅支持 ZIP、TAR.GZ 或 TGZ'}, status_code=400)
    temp = ROOT / 'tmp-packages'
    temp.mkdir(exist_ok=True)
    archive = temp / f'{secrets.token_hex(12)}-{Path(filename).name}'
    target = temp / f'inspect-{secrets.token_hex(8)}'
    try:
        total = 0
        with archive.open('wb') as output:
            while chunk := await package.read(1024 * 1024):
                total += len(chunk)
                if total > MAX_PACKAGE_BYTES:
                    raise ValueError('整合包超过 500MB 限制')
                output.write(chunk)
        extract_archive(archive, target)
        return {'ok': True, 'core_candidates': find_core_candidates(target), 'bytes': total}
    except Exception as exc:
        return JSONResponse({'ok': False, 'message': f'整合包分析失败: {exc}'}, status_code=400)
    finally:
        archive.unlink(missing_ok=True)
        shutil.rmtree(target, ignore_errors=True)