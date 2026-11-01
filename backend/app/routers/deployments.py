from fastapi import APIRouter, Request, UploadFile, File, Form
from fastapi.responses import StreamingResponse
import asyncio, json, httpx, logging, os, traceback
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
logger = logging.getLogger(__name__)

async def _resolve_fill_url(client: httpx.AsyncClient, mc_version: str) -> str:
    url = f'https://fill.papermc.io/v3/projects/paper/versions/{mc_version}/builds?channel=STABLE'
    response = await client.get(url)
    response.raise_for_status()
    builds = response.json()
    if not isinstance(builds, list) or not builds:
        raise RuntimeError(f'Fill v3 未找到 {mc_version} 的 STABLE 构建')
    item = (builds[0].get('downloads') or {}).get('server:default') or {}
    download_url = item.get('url')
    if not download_url:
        raise RuntimeError('Fill v3 缺少 downloads.server:default.url')
    return download_url

async def _resolve_fastmirror_url(client: httpx.AsyncClient, core: str, version: str) -> str:
    base = 'https://download.fastmirror.net/api/v3'
    response = await client.get(f'{base}/{core}/{version}')
    response.raise_for_status()
    payload = response.json()
    data = payload.get('data') if isinstance(payload, dict) else None
    builds = data.get('builds') if isinstance(data, dict) else None
    if not builds:
        raise RuntimeError(f'FastMirror 未找到 {core} {version} 的构建')
    build = builds[0]
    build_id = build.get('build') or build.get('buildVersion') or build.get('id')
    if not build_id:
        raise RuntimeError('FastMirror 构建响应缺少 build')
    detail = await client.get(f'{base}/{core}/{version}/{build_id}')
    detail.raise_for_status()
    item = detail.json()
    download_url = item.get('downloadUrl') if isinstance(item, dict) else None
    if not download_url and isinstance(item, dict):
        download_url = (item.get('data') or {}).get('downloadUrl')
    if not download_url:
        raise RuntimeError('FastMirror 响应缺少 downloadUrl')
    return download_url

async def _probe(client: httpx.AsyncClient, url: str) -> tuple[str, float] | None:
    started = asyncio.get_running_loop().time()
    try:
        response = await client.get(url, headers={'Range': 'bytes=0-1024'})
        if response.status_code not in (200, 206):
            return None
        return url, asyncio.get_running_loop().time() - started
    except (httpx.HTTPError, asyncio.TimeoutError):
        return None

async def download_engine(core: str, version: str, save_path: Path, report=None) -> int:
    headers = {'User-Agent': 'ATMOSPHERE-PANEL/1.0'}
    timeout = httpx.Timeout(2.0, connect=2.0, read=2.0, write=2.0, pool=2.0)
    async with httpx.AsyncClient(timeout=timeout, headers=headers, follow_redirects=True) as client:
        resolvers = []
        if core == 'paper':
            resolvers.append(_resolve_fill_url(client, version))
        resolvers.append(_resolve_fastmirror_url(client, core, version))
        resolved = await asyncio.gather(*resolvers, return_exceptions=True)
        candidates = [value for value in resolved if isinstance(value, str)]
        if not candidates:
            raise RuntimeError('官方 Fill v3 与 FastMirror 均未返回可用下载链接')
        probes = await asyncio.gather(*[_probe(client, value) for value in candidates])
        usable = [item for item in probes if item is not None]
        if not usable:
            raise RuntimeError('下载源测速均失败：2 秒内没有返回 200/206')
        selected_url = min(usable, key=lambda item: item[1])[0]
        logger.info('选择下载源: %s', selected_url)

        save_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = save_path.with_suffix(save_path.suffix + '.part')
        downloaded = 0
        try:
            async with client.stream('GET', selected_url, timeout=30.0) as response:
                response.raise_for_status()
                total = int(response.headers.get('content-length') or 0)
                with temp_path.open('wb') as output:
                    async for chunk in response.aiter_bytes(1024 * 1024):
                        output.write(chunk)
                        downloaded += len(chunk)
                        if report:
                            percent = 20 + int(downloaded / total * 70) if total else 20
                            await report(min(percent, 90), f'正在下载 {downloaded / 1048576:.1f} MB')
            if downloaded < 1024 * 1024:
                raise RuntimeError(f'下载文件过小，疑似错误页: {downloaded} bytes')
            temp_path.replace(save_path)
            return downloaded
        except Exception:
            temp_path.unlink(missing_ok=True)
            logger.error('下载失败: %s', selected_url, exc_info=True)
            raise

async def download_paper_jar(mc_version: str, save_path: Path, report=None) -> int:
    return await download_engine('paper', mc_version, save_path, report)

class DeployPayload(BaseModel):
    instance_id: str
    core_type: str
    mc_version: str
    build_version: str
    port: int = Field(default=25565, ge=1, le=65535)

async def _install_forge(root: Path, report) -> str:
    java = shutil.which('java')
    if not java:
        raise RuntimeError('未检测到 Java，无法安装 Forge')
    installer = root / 'installer.jar'
    # 启动安装器
    process = await asyncio.create_subprocess_exec(
        java, '-jar', installer.name, '--installServer',
        cwd=str(root),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    # 读取安装输出
    stdout, stderr = await process.communicate()
    out_text = stdout.decode(errors='replace').strip()
    err_text = stderr.decode(errors='replace').strip()
    if out_text:
        logger.info('[Forge stdout] %s', out_text)
    if err_text:
        logger.error('[Forge stderr] %s', err_text)
    await report(92, 'Forge 安装器执行完成，正在校验文件...')
    code = process.returncode
    if code != 0:
        raise RuntimeError(f'Forge 安装失败，退出码: {code}')
    if (root / 'run.bat').is_file():
        return 'run.bat'
    candidates = list(root.glob('*server*.jar')) + list(root.glob('forge-*.jar'))
    if candidates:
        return candidates[0].name
    raise RuntimeError('Forge 安装完成但未找到 run.bat 或服务端 JAR')

async def _download_core(core: str, version: str, root: Path, report) -> str:
    core = core.strip().casefold()
    if core == 'paper':
        target = root / 'server.jar'
        await download_engine('paper', version, target, report)
        return target.name
    if core in {'forge', 'neoforge'}:
        target = root / 'installer.jar'
        await download_engine(core, version, target, report)
        return await _install_forge(root, report)
    raise RuntimeError(f'当前下载链路不支持核心: {core}')

async def run_deploy_task(instance_id: str, core_type: str, mc_version: str, build_version: str, port: int):
    queue = deploy_events[instance_id]
    async def report(progress: int, status: str):
        await queue.put({'progress': progress, 'status': status})
    try:
        await report(10, '正在写入实例记录...')
        # 先插库
        conn = connect()
        try:
            stale = conn.execute('SELECT id, status FROM instances WHERE port=? AND id<>?', (port, instance_id)).fetchone()
            if stale is not None and stale['status'] == 'error':
                logger.warning('清理失败实例占用端口: id=%s port=%s', stale['id'], port)
                conn.execute('DELETE FROM instances WHERE id=?', (stale['id'],))
            conn.execute(
                'INSERT INTO instances (id,name,port,jar_name,status,created_at,core_candidates,selected_core,rcon_host,rcon_port,rcon_password_hash,rcon_password) VALUES (?,?,?,?,?,?,?,?,?,?,?,?) '
                'ON CONFLICT(id) DO UPDATE SET name=excluded.name, port=excluded.port, jar_name=excluded.jar_name, status=excluded.status, created_at=excluded.created_at, core_candidates=excluded.core_candidates, selected_core=excluded.selected_core, rcon_host=excluded.rcon_host, rcon_port=excluded.rcon_port, rcon_password_hash=excluded.rcon_password_hash, rcon_password=excluded.rcon_password',
                (instance_id, instance_id, port, 'server.jar', 'deploying', int(time.time()), '[]', 'server.jar', '127.0.0.1', 25575, None, ''),
            )
            conn.commit()
            logger.info('实例记录已写入: %s', instance_id)
        except Exception:
            conn.rollback()
            logger.error('实例记录写入失败: %s', instance_id, exc_info=True)
            raise
        finally:
            conn.close()
        # 再建目录
        root = SERVER_ROOT / instance_id
        root.mkdir(parents=True, exist_ok=True)
        logger.info('实例目录已创建: %s', root)
        await report(20, f'正在下载 {core_type} 核心...')
        normalized_core = core_type.strip().casefold()
        logger.info('部署核心标准化: raw=%s normalized=%s', core_type, normalized_core)
        jar_name = await _download_core(normalized_core, mc_version, root, report)
        # 生成实例配置
        (root / 'eula.txt').write_text('eula=true\n', encoding='utf-8')
        jar = root / jar_name
        if not jar.is_file() and jar_name != 'run.bat':
            raise RuntimeError(f'核心文件未落地: {jar_name}')
        password = secrets.token_urlsafe(24)
        (root / 'server.properties').write_text(f'server-port={port}\nenable-rcon=true\nrcon.port=25575\nrcon.password={password}\n', encoding='utf-8')
        password = secrets.token_urlsafe(24)
        properties = root / 'server.properties'
        properties.write_text(f'server-port={port}\nenable-rcon=true\nrcon.port=25575\nrcon.password={password}\n', encoding='utf-8')
        conn = connect()
        conn.execute('UPDATE instances SET status=?, jar_name=?, selected_core=?, rcon_password=? WHERE id=?', ('stopped', jar_name, jar_name, password, instance_id))
        conn.commit()
        conn.close()
        logger.info('准备启动实例: id=%s target=%s', instance_id, jar_name)
        await get_process_manager().start(instance_id, jar_name, 4096)
        logger.info('实例启动完成: id=%s', instance_id)
        await report(100, '部署完成！')
    except Exception as exc:
        logger.error('部署失败: %s', exc, exc_info=True)
        conn = connect()
        try:
            conn.execute('UPDATE instances SET status=? WHERE id=?', ('error', instance_id))
            logger.error('失败实例记录已保留: %s', instance_id)
            conn.commit()
            logger.error('实例状态已更新为 error: %s', instance_id)
        finally:
            conn.close()
        await report(99, f'部署失败: {type(exc).__name__}: {exc}')
    finally:
        await queue.put(None)

@router.post('/instances/deploy')
async def start_deploy(request: Request, payload: DeployPayload):
    if isinstance((user := require_user(request)), JSONResponse): return user
    deploy_events[payload.instance_id] = asyncio.Queue()
    asyncio.create_task(run_deploy_task(payload.instance_id, payload.core_type, payload.mc_version, payload.build_version, payload.port))
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