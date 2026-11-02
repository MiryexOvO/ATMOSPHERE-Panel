from fastapi import APIRouter, Request, UploadFile, File, Form
from fastapi.responses import StreamingResponse
import asyncio, json, httpx, logging, os, traceback
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from ..core.security import require_user
from ..core.database import connect
from ..core.config import SERVER_ROOT, ROOT, MAX_PACKAGE_BYTES
from ..archive_service import extract_archive, find_core_candidates
from ..services.server_properties import write_properties
from ..services.panel_settings import read_settings
from contextlib import closing
import sqlite3
from pathlib import Path
import secrets, shutil, time, platform
from ..infra.process_manager import get_process_manager

router = APIRouter(prefix='/api', tags=['deployments'])
deploy_events: dict[str, asyncio.Queue] = {}
active_deployments: set[str] = set()
logger = logging.getLogger(__name__)

async def download_engine(core: str, version: str, save_path: Path, report=None,
                          build: str = '', source: str = 'fastmirror') -> int:
    from ..services.download_sources import list_resource, download_candidates
    if not build:
        builds = await list_resource(core, version)
        build, source = builds[0]['id'], builds[0]['source']
    candidates = await download_candidates(core, version, build, source)
    errors = []
    for metadata in candidates:
        try:
            if report: await report(20, f'正在使用 {metadata["source"]} 下载所选构建...')
            return await _download_once(core,version,save_path,report,build,metadata['source'],metadata)
        except (httpx.HTTPError, RuntimeError) as exc:
            errors.append(f'{metadata["source"]}: {exc}')
    raise RuntimeError('; '.join(errors))


async def _download_once(core: str, version: str, save_path: Path, report=None,
                         build: str = '', source: str = 'fastmirror', metadata=None) -> int:
    from ..services.mc_meta_service import HEADERS, list_builds, resolve_download
    import hashlib
    import zipfile

    if not build:
        builds = await list_builds(core, version, source)
        if not builds:
            raise RuntimeError(f'{core} {version} 没有可用构建')
        build = builds[0]['id']
        source = builds[0]['source']
    if metadata is None:
        metadata = await resolve_download(core, version, build, source)
    selected_url = metadata['url']
    logger.info('下载核心 core=%s version=%s build=%s source=%s url=%s',
                core, version, build, source, selected_url)
    save_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = save_path.with_suffix(save_path.suffix + '.part')
    downloaded = 0
    sha1, sha256 = hashlib.sha1(), hashlib.sha256()
    timeout = httpx.Timeout(60.0, connect=15.0)
    try:
        async with httpx.AsyncClient(timeout=timeout, headers=HEADERS, follow_redirects=True) as client:
            async with client.stream('GET', selected_url) as response:
                response.raise_for_status()
                total = int(response.headers.get('content-length') or 0)
                if total > MAX_PACKAGE_BYTES:
                    raise RuntimeError('核心文件超过下载大小限制')
                with temp_path.open('wb') as output:
                    async for chunk in response.aiter_bytes(1024 * 1024):
                        downloaded += len(chunk)
                        if downloaded > MAX_PACKAGE_BYTES:
                            raise RuntimeError('核心文件超过下载大小限制')
                        output.write(chunk)
                        sha1.update(chunk)
                        sha256.update(chunk)
                        if report:
                            percent = 20 + int(downloaded / total * 70) if total else 20
                            await report(min(percent, 90), f'正在下载 {downloaded / 1048576:.1f} MB')
                if total and downloaded != total:
                    raise RuntimeError(f'下载不完整: {downloaded}/{total} bytes')
        for name, digest in [('sha1', sha1), ('sha256', sha256)]:
            expected = metadata.get(name)
            if expected and digest.hexdigest().lower() != expected.lower():
                raise RuntimeError(f'核心文件 {name} 校验失败')
        if not zipfile.is_zipfile(temp_path):
            raise RuntimeError('下载内容不是有效的 JAR 文件，可能返回了错误页面')
        with zipfile.ZipFile(temp_path) as archive:
            if 'META-INF/MANIFEST.MF' not in archive.namelist():
                raise RuntimeError('下载文件缺少 JAR manifest')
        temp_path.replace(save_path)
        return downloaded
    except Exception:
        temp_path.unlink(missing_ok=True)
        logger.error('核心下载失败: %s', selected_url, exc_info=True)
        raise

async def download_paper_jar(mc_version: str, save_path: Path, report=None) -> int:
    return await download_engine('paper', mc_version, save_path, report)

class DeployPayload(BaseModel):
    instance_id: str
    core_type: str
    mc_version: str
    build_version: str
    source: str = Field(default='fastmirror', pattern='^(default|fastmirror|official|polars)$')
    java_version: str = Field(default='21', pattern='^(8|17|21|25)$')
    memory: int = Field(default=4096, ge=512, le=131072)
    port: int = Field(default=25565, ge=1, le=65535)
    mode:str=Field(default='java',pattern='^(java|bedrock|mcdr)$')
    ipv6_port:int=Field(default=19133,ge=1,le=65535)
    accept_eula:bool=False

async def _install_forge(root: Path, report, installer_name: str = 'installer.jar', java_path: str | None = None) -> str:
    java = java_path or shutil.which('java')
    if not java:
        raise RuntimeError('未检测到 Java，无法安装 Forge')
    installer = root / installer_name
    from ..services.core_package import prepare_libraries
    await report(90, '正在校验安装器依赖...')
    await prepare_libraries(root, installer, report)
    temp_root = (root / '.install-tmp').resolve()
    temp_root.mkdir(parents=True, exist_ok=True)
    await report(90, '核心下载完成，正在安装 Forge 依赖...')
    process = await asyncio.create_subprocess_exec(
        java, f'-Djava.io.tmpdir={temp_root}', '-Djava.awt.headless=true', '-jar', installer.name, '--installServer',
        cwd=str(root), stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT,
    )
    tail = []
    async def consume():
        last_update = 0.0
        with (root / 'panel-install.log').open('w', encoding='utf-8') as output:
            while line := await process.stdout.readline():
                text = line.decode(errors='replace').strip()
                output.write(text + '\n')
                tail.append(text)
                del tail[:-12]
                if time.monotonic() - last_update >= 0.5:
                    output.flush()
                    last_update = time.monotonic()
                    logger.info('[Forge] %s', text)
                    await report(90, f'正在安装 Forge: {text[:240]}')
        return await process.wait()
    try:
        code = await asyncio.wait_for(consume(), timeout=600)
    except (asyncio.TimeoutError, asyncio.CancelledError) as exc:
        if process.returncode is None:
            process.kill()
            await process.wait()
        if isinstance(exc, asyncio.CancelledError):
            raise
        raise RuntimeError('Forge 安装超过 10 分钟，请查看实例 panel-install.log') from exc
    if code != 0:
        raise RuntimeError(f'Forge 安装失败，退出码 {code}: ' + ' | '.join(tail)[-1200:])
    await report(94, 'Forge 安装完成，正在校验启动文件...')
    args_name = 'win_args.txt' if os.name == 'nt' else 'unix_args.txt'
    args_files = list(root.glob(f'libraries/net/minecraftforge/forge/*/{args_name}'))
    args_files += list(root.glob(f'libraries/net/neoforged/neoforge/*/{args_name}'))
    if args_files:
        return '@' + args_files[0].relative_to(root).as_posix()
    candidates = list(root.glob('*server*.jar')) + list(root.glob('forge-*.jar'))
    if candidates:
        return candidates[0].name
    raise RuntimeError('Forge 安装完成但未找到 run.bat 或服务端 JAR')

async def _download_core(core: str, version: str, root: Path, report,
                         build: str = '', source: str = 'fastmirror') -> str:
    core = core.strip().casefold()
    if core == 'pocketmine':
        raise RuntimeError('PocketMine 需要 PHP 运行环境，暂不支持自动部署；请选择 Java 核心')
    installer = core in {'forge', 'neoforge'}
    target = root / ('installer.jar' if installer else 'server.jar')
    await download_engine(core, version, target, report, build, source)
    if installer:
        return await _install_forge(root, report)
    return target.name

async def run_deploy_task(instance_id: str, core_type: str, mc_version: str, build_version: str, port: int, source: str = 'fastmirror', java_version: str = '21', memory: int = 4096, mode='java',ipv6_port=19133):
    queue = deploy_events[instance_id]
    last_progress = 0
    root = SERVER_ROOT / f'.deploy-{instance_id}-{secrets.token_hex(6)}'
    final_root = SERVER_ROOT / instance_id
    published = False
    async def report(progress: int, status: str):
        nonlocal last_progress
        progress=max(last_progress,progress)
        last_progress = progress
        await queue.put({'progress': progress, 'status': status})
    try:
        await report(10, '已确认部署，正在准备临时目录...')
        # 下载和安装完成前不创建实例。
        root.mkdir(parents=True, exist_ok=True)
        logger.info('实例目录已创建: %s', root)
        await report(20, f'正在下载 {core_type} 核心...')
        normalized_core = core_type.strip().casefold()
        logger.info('部署核心标准化: raw=%s normalized=%s', core_type, normalized_core)
        from ..services.runtime_modes import prepare_bedrock,prepare_mcdr
        if mode=='bedrock': jar_name=await prepare_bedrock(root,mc_version,report)
        else:
            jar_name = await _download_core(normalized_core, mc_version, root, report, build_version, source)
            if mode=='mcdr': await prepare_mcdr(root,report,normalized_core)
        # 生成实例配置
        (root / 'eula.txt').write_text('eula=true\n', encoding='utf-8')
        jar = root / jar_name.removeprefix('@')
        if not jar.is_file():
            raise RuntimeError(f'核心文件未落地: {jar_name}')
        password = secrets.token_urlsafe(24)
        properties = root / 'server.properties'
        if mode=='bedrock':
            # 保留官方默认属性，仅写入本实例连接参数。
            write_properties(properties,{'server-port':str(port),'server-portv6':str(ipv6_port),'server-name':instance_id})
        else: properties.write_text(f'server-port={port}\nenable-rcon=true\nrcon.port=25575\nrcon.password={password}\n', encoding='utf-8')
        await report(96, '文件已就绪，正在创建实例...')
        with closing(connect()) as conn:
            conn.execute('BEGIN IMMEDIATE')
            if conn.execute('SELECT 1 FROM instances WHERE id=? OR port=? OR secondary_port=?', (instance_id, port,port)).fetchone():
                raise ValueError('实例 ID 或端口已存在')
            if mode=='bedrock' and conn.execute('SELECT 1 FROM instances WHERE port=? OR secondary_port=?',(ipv6_port,ipv6_port)).fetchone(): raise ValueError('IPv6 端口已存在')
            if final_root.exists():
                raise ValueError('实例目录已存在，请先管理已有目录')
            root.rename(final_root)
            published = True
            conn.execute(
                'INSERT INTO instances (id,name,port,jar_name,status,created_at,core_candidates,selected_core,rcon_host,rcon_port,rcon_password,memory_mb,java_version,ignore_eula) '
                'VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                (instance_id, instance_id, port, jar_name, 'stopped', int(time.time()), '[]', jar_name,
                 '127.0.0.1', 25575, password, memory, java_version, 1),
            )
            conn.execute("UPDATE deployment_jobs SET status='complete',error='' WHERE id=?", (instance_id,))
            if mode=='bedrock': conn.execute('UPDATE instances SET secondary_port=?,rcon_enabled=0,rcon_password=NULL WHERE id=?',(ipv6_port,instance_id))
            conn.commit()
        await report(100, '部署完成，实例已创建，可手动启动')
    except Exception as exc:
        logger.error('部署失败: %s', exc, exc_info=True)
        with closing(connect()) as conn:
            conn.execute("UPDATE deployment_jobs SET status='error',error=? WHERE id=?", (str(exc), instance_id))
            conn.commit()
        # 仅清理本任务目录，已有实例文件不受影响。
        cleanup = final_root if published else root
        base = SERVER_ROOT.resolve()
        if base in cleanup.resolve().parents:
            shutil.rmtree(cleanup, ignore_errors=True)
        await report(last_progress, f'部署失败: {type(exc).__name__}: {exc}')
    finally:
        active_deployments.discard(instance_id)
        await queue.put(None)

@router.post('/instances/deploy')
async def start_deploy(request: Request, payload: DeployPayload):
    if isinstance((user := require_user(request)), JSONResponse): return user
    instance_id = payload.instance_id
    if payload.mode=='bedrock' and (not payload.accept_eula or payload.port==payload.ipv6_port):
        return JSONResponse({'message':'请同意 Minecraft EULA，并设置不同的 IPv4 / IPv6 UDP 端口'},status_code=422)
    if not instance_id or not instance_id.replace('-', '').isalnum():
        return JSONResponse({'ok': False, 'message': '实例 ID 无效'}, status_code=400)
    if instance_id in active_deployments:
        return JSONResponse({'ok': False, 'message': '该实例正在部署，请等待完成'}, status_code=409)
    conn = connect()
    try:
        conn.execute('BEGIN IMMEDIATE')
        if conn.execute('SELECT 1 FROM instances WHERE id=? OR port=? OR secondary_port=?', (instance_id, payload.port,payload.port)).fetchone():
            return JSONResponse({'ok': False, 'message': '实例 ID 或端口已存在，请管理已有实例或更换端口'}, status_code=409)
        if conn.execute("SELECT 1 FROM deployment_jobs WHERE status='deploying' AND (id=? OR port=? OR secondary_port=?)", (instance_id, payload.port,payload.port)).fetchone():
            return JSONResponse({'ok': False, 'message': '该实例或端口正在部署'}, status_code=409)
        if payload.mode=='bedrock':
            if conn.execute('SELECT 1 FROM instances WHERE port=? OR secondary_port=?',(payload.ipv6_port,payload.ipv6_port)).fetchone() or conn.execute("SELECT 1 FROM deployment_jobs WHERE status='deploying' AND (port=? OR secondary_port=?)",(payload.ipv6_port,payload.ipv6_port)).fetchone():
                return JSONResponse({'message':'IPv6 UDP 端口已被其他实例或任务预留'},status_code=409)
        # 只预留任务，实例列表中尚无此实例。
        conn.execute("INSERT INTO deployment_jobs(id,port,status,error,created_at) VALUES(?,?,'deploying','',?) ON CONFLICT(id) DO UPDATE SET port=excluded.port,status='deploying',error='',created_at=excluded.created_at", (instance_id, payload.port, int(time.time())))
        conn.execute('UPDATE deployment_jobs SET secondary_port=? WHERE id=?',(payload.ipv6_port if payload.mode=='bedrock' else None,instance_id))
        conn.commit()
    finally:
        conn.close()
    active_deployments.add(instance_id)
    deploy_events[instance_id] = asyncio.Queue()
    asyncio.create_task(run_deploy_task(instance_id, payload.core_type, payload.mc_version, payload.build_version, payload.port, payload.source, payload.java_version, payload.memory,payload.mode,payload.ipv6_port))
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
async def deploy_mode(request: Request, payload: ModePayload):
    # 旧入口同样进入真实下载流程，禁止生成空核心。
    if isinstance((user := require_user(request)), JSONResponse): return user
    if not payload.version:
        return JSONResponse({'ok': False, 'message': '请选择游戏版本'}, status_code=422)
    if payload.mode not in {'quick','mcdr'}: return JSONResponse({'message':'请使用新版向导选择基岩版版本并确认 EULA'},status_code=422)
    return await start_deploy(request, DeployPayload(instance_id=payload.instance_id, core_type=payload.resource or 'paper', mc_version=payload.version, build_version='', port=payload.port, java_version=payload.java_version, memory=payload.memory,mode='mcdr' if payload.mode=='mcdr' else 'java'))


@router.get('/deploy/bedrock/versions')
async def bedrock_versions(request:Request):
    if isinstance(user:=require_user(request),JSONResponse): return user
    from ..services.runtime_modes import bedrock_catalog
    try: return await bedrock_catalog()
    except (httpx.HTTPError,ValueError,KeyError,RuntimeError) as exc: return JSONResponse({'message':'获取官方基岩版版本失败：'+str(exc)},status_code=502)

def package_content_root(target: Path) -> Path:
    # 解开压缩包最外层的单目录包装。
    current = target
    for _ in range(5):
        entries = [p for p in current.iterdir() if p.name != '__MACOSX']
        if len(entries) != 1 or not entries[0].is_dir():
            break
        current = entries[0]
    return current


@router.post('/instances/package')
async def upload_package(request: Request, package: UploadFile = File(...), instance_id: str = Form(...),
                         port: int = Form(...), selected_core: str = Form(''), memory: int = Form(4096),
                         java_version: str = Form('21')):
    if isinstance((user := require_user(request)), JSONResponse): return user
    filename = (package.filename or '').lower()
    upload_limit = read_settings()['upload_limit_mb'] * 1048576
    if not filename.endswith(('.zip', '.tar.gz', '.tgz')):
        return JSONResponse({'ok': False, 'message': '仅支持 ZIP、TAR.GZ 或 TGZ'}, status_code=400)
    instance_id = instance_id.lower()
    if not instance_id or not instance_id.replace('-', '').isalnum() or not (1 <= port <= 65535) or not (512 <= memory <= 131072) or java_version not in {'8','17','21','25'}:
        return JSONResponse({'ok': False, 'message': '实例 ID、端口或运行环境无效'}, status_code=400)
    temp = ROOT / 'tmp-packages'
    temp.mkdir(exist_ok=True)
    archive = temp / f'{secrets.token_hex(12)}-{Path(filename).name}'
    target = temp / f'package-{secrets.token_hex(8)}'
    root = SERVER_ROOT / instance_id
    created = False
    try:
        # 最终确认才进入此接口，完整预检后一次性入库。
        with closing(connect()) as conn:
            if conn.execute('SELECT 1 FROM instances WHERE id=? OR port=? OR secondary_port=?', (instance_id, port,port)).fetchone() or conn.execute("SELECT 1 FROM deployment_jobs WHERE status='deploying' AND (id=? OR port=? OR secondary_port=?)", (instance_id, port,port)).fetchone():
                return JSONResponse({'ok': False, 'message': '实例 ID 或端口已存在或正在部署'}, status_code=409)
        total = 0
        with archive.open('wb') as output:
            while chunk := await package.read(1024 * 1024):
                total += len(chunk)
                if total > upload_limit: raise ValueError(f'整合包超过 {upload_limit // 1048576}MB 限制')
                output.write(chunk)
        await asyncio.to_thread(extract_archive, archive, target)
        content = package_content_root(target)
        candidates = await asyncio.to_thread(find_core_candidates, content)
        selected = selected_core or next((item['path'] for item in candidates if item.get('recommended')), '')
        if not any(item['path'] == selected and item['kind'] in {'jar','args'} for item in candidates):
            raise ValueError('请选择整合包中的有效服务端 JAR 或 Forge 参数文件')
        password = secrets.token_urlsafe(24)
        # 整合包附带安装器时，先生成真正的服务端启动目标。
        from ..services.core_package import is_installer
        if not selected.startswith('@') and is_installer(content / selected):
            async def report_install(progress, message): logger.info('%s', message)
            selected = await _install_forge(content, report_install, selected)
        write_properties(content / 'server.properties', {'server-port': str(port), 'enable-rcon':'true', 'rcon.port':'25575', 'rcon.password':password})
        write_properties(content / 'eula.txt', {'eula':'true'})
        with closing(connect()) as conn:
            conn.execute('BEGIN IMMEDIATE')
            if conn.execute('SELECT 1 FROM instances WHERE id=? OR port=? OR secondary_port=?', (instance_id, port,port)).fetchone() or conn.execute("SELECT 1 FROM deployment_jobs WHERE status='deploying' AND (id=? OR port=? OR secondary_port=?)", (instance_id, port,port)).fetchone():
                raise ValueError('实例 ID 或端口已被其他任务使用')
            if root.exists(): raise ValueError('目标实例目录已存在，请管理已有目录')
            content.rename(root)
            created = True
            conn.execute('INSERT INTO instances (id,name,port,jar_name,status,created_at,core_candidates,selected_core,rcon_host,rcon_port,rcon_password,memory_mb,java_version,ignore_eula) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                         (instance_id,instance_id,port,selected,'stopped',int(time.time()),json.dumps(candidates),selected,'127.0.0.1',25575,password,memory,java_version,1))
            conn.commit()
        return {'ok':True,'instance':{'id':instance_id,'name':instance_id,'port':port},'selected_core':selected,'status':'stopped'}
    except Exception as exc:
        if created and SERVER_ROOT.resolve() in root.resolve().parents:
            shutil.rmtree(root, ignore_errors=True)
        return JSONResponse({'ok':False,'message':f'部署失败: {exc}'},status_code=400)
    finally:
        archive.unlink(missing_ok=True)
        if temp.resolve() in target.resolve().parents:
            shutil.rmtree(target,ignore_errors=True)


@router.post('/instances/package/inspect')
async def inspect_package(request: Request, package: UploadFile = File(...)):
    if isinstance((user := require_user(request)), JSONResponse):
        return user
    filename = (package.filename or '').lower()
    upload_limit = read_settings()['upload_limit_mb'] * 1048576
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
                if total > upload_limit:
                    raise ValueError(f'整合包超过 {upload_limit // 1048576}MB 限制')
                output.write(chunk)
        await asyncio.to_thread(extract_archive, archive, target)
        return {'ok': True, 'core_candidates': await asyncio.to_thread(find_core_candidates, package_content_root(target)), 'bytes': total}
    except Exception as exc:
        return JSONResponse({'ok': False, 'message': f'整合包分析失败: {exc}'}, status_code=400)
    finally:
        archive.unlink(missing_ok=True)
        shutil.rmtree(target, ignore_errors=True)
