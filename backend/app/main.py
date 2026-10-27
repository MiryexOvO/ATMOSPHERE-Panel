from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import shutil
import sqlite3
import string
import time
import asyncio
import subprocess
import shutil
from pathlib import Path
from xml.etree import ElementTree
import httpx

JAVA_BY_VERSION = {'8': '8', '1.16.5': '8', '1.17': '16', '1.17.1': '16', '1.18': '17', '1.19': '17', '1.20.4': '17', '1.20.5': '21', '1.21': '21'}

import bcrypt
from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from .archive_service import extract_archive, find_core_candidates

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "panel.sqlite3"
SERVER_ROOT = Path("/opt/mc-panel/servers")
SESSION_HOURS = 24
MAX_JAR_BYTES = 300 * 1024 * 1024
MAX_PACKAGE_BYTES = 500 * 1024 * 1024
INSTANCE_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,30}$")
DOWNLOAD_TASKS: dict[str, dict] = {}
SYSTEMD_DIR = Path('/etc/systemd/system')
JAVA_ROOT = Path('/opt/mc-panel/java')

app = FastAPI(title="Atmosphere API", version="0.2.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


def db():
    conn = sqlite3.connect(DB_PATH); conn.row_factory = sqlite3.Row; return conn


def init_db():
    conn = db(); conn.executescript("""
    CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, created_at INTEGER NOT NULL);
    CREATE TABLE IF NOT EXISTS sessions(token_hash TEXT PRIMARY KEY, user_id INTEGER NOT NULL, expires_at INTEGER NOT NULL, created_at INTEGER NOT NULL);
    CREATE TABLE IF NOT EXISTS instances(id TEXT PRIMARY KEY, name TEXT NOT NULL, port INTEGER UNIQUE NOT NULL, jar_name TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'stopped', created_at INTEGER NOT NULL, core_candidates TEXT NOT NULL DEFAULT '[]', selected_core TEXT);
    """)
    existing = conn.execute("SELECT id FROM users WHERE username='Atmo7'").fetchone()
    if not existing:
        legacy = conn.execute("SELECT id FROM users WHERE username='admin'").fetchone()
        if legacy: conn.execute("UPDATE users SET username='Atmo7' WHERE id=?", (legacy['id'],)); existing = legacy
    if not existing:
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*_-+=?"; password = ''.join(secrets.choice(alphabet) for _ in range(20))
        conn.execute("INSERT INTO users(username,password_hash,created_at) VALUES(?,?,?)", ('Atmo7', bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode(), int(time.time()))); conn.commit()
        print(f"[INIT] 面板初始密码: {password}（请立即登录修改）", flush=True)
    conn.close()


@app.on_event('startup')
def startup():
    init_db(); print('-' * 72); print('[READY] ATMOSPHERE backend connected · http://127.0.0.1:27777'); print('-' * 72, flush=True)


class LoginPayload(BaseModel):
    username: str = Field(min_length=1, max_length=32)
    password: str = Field(min_length=1, max_length=256)


def current_user(request: Request):
    token = request.cookies.get('mc_panel_session')
    if not token: return None
    conn = db(); row = conn.execute("SELECT users.id,users.username FROM sessions JOIN users ON users.id=sessions.user_id WHERE token_hash=? AND expires_at>?", (hashlib.sha256(token.encode()).hexdigest(), int(time.time()))).fetchone(); conn.close(); return row


def require_user(request: Request):
    user = current_user(request)
    return user if user else JSONResponse({'ok': False, 'message': '未登录'}, status_code=401)


@app.get('/api/health')
@app.get('/health')
def health(): return {'ok': True, 'service': 'atmosphere', 'stage': 2}


@app.post('/api/login')
@app.post('/login')
def login(payload: LoginPayload):
    conn = db(); row = conn.execute('SELECT id,password_hash FROM users WHERE username=?', (payload.username,)).fetchone()
    if not row or not bcrypt.checkpw(payload.password.encode(), row['password_hash'].encode()): conn.close(); return JSONResponse({'ok': False, 'message': '用户名或密码错误'}, status_code=401)
    token = secrets.token_urlsafe(48); now = int(time.time()); conn.execute('INSERT INTO sessions VALUES(?,?,?,?)', (hashlib.sha256(token.encode()).hexdigest(), row['id'], now + SESSION_HOURS * 3600, now)); conn.commit(); conn.close()
    response = JSONResponse({'ok': True, 'user': {'username': payload.username}}); response.set_cookie('mc_panel_session', token, max_age=SESSION_HOURS * 3600, httponly=True, samesite='lax'); return response


@app.get('/api/me')
@app.get('/me')
def me(request: Request):
    user = current_user(request)
    return {'ok': True, 'user': {'username': user['username']}} if user else JSONResponse({'ok': False, 'message': '未登录'}, status_code=401)


@app.post('/api/logout')
@app.post('/logout')
def logout(request: Request):
    token = request.cookies.get('mc_panel_session'); conn = db()
    if token: conn.execute('DELETE FROM sessions WHERE token_hash=?', (hashlib.sha256(token.encode()).hexdigest(),)); conn.commit()
    conn.close(); response = JSONResponse({'ok': True}); response.delete_cookie('mc_panel_session'); return response


MIRRORS_PATH = ROOT / 'mirrors.json'


def mirror_config():
    return json.loads(MIRRORS_PATH.read_text(encoding='utf-8'))


CORE_CATALOG = [
    {'id':'paper','name':'Paper','category':'plugin','description':'高性能 Spigot 分支，适合插件服务器','versions':['1.21.4','1.21.1','1.20.6','1.20.4','1.19.4','1.16.5']},
    {'id':'purpur','name':'Purpur','category':'plugin','description':'Paper 兼容的增强核心','versions':['1.21.4','1.21.1','1.20.4','1.19.4']},
    {'id':'spigot','name':'Spigot','category':'plugin','description':'经典 Bukkit/Spigot 服务端','versions':['1.21.4','1.20.4','1.19.4','1.16.5']},
    {'id':'velocity','name':'Velocity','category':'proxy','description':'现代代理服务端','versions':['3.4.0','3.3.0','3.2.0']},
    {'id':'fabric','name':'Fabric','category':'mod','description':'轻量、现代的模组加载器','versions':['1.21.4','1.21.1','1.20.4','1.20.1']},
    {'id':'forge','name':'Forge','category':'mod','description':'传统大型模组生态','versions':['1.21.1','1.20.1','1.20.4','1.19.2','1.16.5']},
    {'id':'neoforge','name':'NeoForge','category':'mod','description':'NeoForge 模组服务端','versions':['1.21.1','1.20.6','1.20.4']},
    {'id':'vanilla','name':'Vanilla','category':'vanilla','description':'Minecraft 官方原版核心','versions':['1.21.4','1.21.1','1.20.4','1.19.4','1.16.5']},
    {'id':'bedrock','name':'Bedrock','category':'bedrock','description':'Minecraft 基岩版服务端','versions':['1.21.50','1.21.40']},
    {'id':'mcdr','name':'MCDR','category':'tool','description':'Minecraft 服务端管理与插件框架','versions':['2.12','2.11']}
]


@app.get('/api/resources/cores')
def core_catalog(request: Request):
    if isinstance((user := require_user(request)), JSONResponse): return user
    return {'ok': True, 'categories': [{'id':'plugin','name':'插件服务端'},{'id':'mod','name':'模组服务端'},{'id':'vanilla','name':'原版服务端'},{'id':'proxy','name':'代理服务端'},{'id':'bedrock','name':'基岩版'},{'id':'tool','name':'MCDR'}], 'cores': CORE_CATALOG}


async def core_download_urls(core_id: str, version: str) -> list[str]:
    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        if core_id in {'bedrock','mcdr'}:
            raise ValueError('该模式需要专用部署器，在线核心下载将在下一步接入')
        if core_id in {'paper','purpur','velocity'}:
            project = core_id
            try:
                payload = (await client.get(f'https://fill.papermc.io/v3/projects/{project}/{version}')).raise_for_status().json()
                builds = payload.get('builds', [])
                if builds:
                    build = builds[0].get('id') or builds[0].get('build')
                    application = builds[0].get('downloads', {}).get('application', {}).get('name') or f'{project}-{version}-{build}.jar'
                    return [f'https://fill.papermc.io/v3/projects/{project}/{version}/{build}/downloads/{application}']
            except Exception:
                pass
            payload = (await client.get(f'https://api.papermc.io/v2/projects/{project}/versions/{version}')).raise_for_status().json()
            builds = payload.get('builds', [])
            if not builds: raise ValueError('没有可用构建')
            build = builds[-1]
            details = (await client.get(f'https://api.papermc.io/v2/projects/{project}/versions/{version}/builds/{build}')).raise_for_status().json()
            downloads = details.get('downloads', {})
            application = downloads.get('application', {}).get('name') or f'{project}-{version}-{build}.jar'
            return [f'https://api.papermc.io/v2/projects/{project}/versions/{version}/builds/{build}/downloads/{application}', f'https://bmclapi2.bangbang93.com/maven/com/{project}/{project}/{version}/{application}']
        if core_id == 'vanilla':
            manifest = (await client.get('https://piston-meta.mojang.com/mc/game/version_manifest_v2.json')).raise_for_status().json()
            item = next((x for x in manifest['versions'] if x['id'] == version), None)
            if not item: raise ValueError('Vanilla 版本不存在')
            detail = (await client.get(item['url'])).raise_for_status().json()
            return [detail['downloads']['server']['url'], f'https://bmclapi2.bangbang93.com/server/{version}/server.jar']
        if core_id == 'fabric':
            loaders = (await client.get(f'https://meta.fabricmc.net/v2/versions/loader/{version}')).raise_for_status().json()
            if not loaders: raise ValueError('Fabric 没有可用 Loader')
            loader = loaders[0]['loader']['version']; installers = (await client.get('https://meta.fabricmc.net/v2/versions/installer')).raise_for_status().json(); installer = installers[0]['version']
            return [f'https://meta.fabricmc.net/v2/versions/loader/{version}/{loader}/{installer}/server/jar']
        if core_id == 'forge':
            return [f'https://maven.minecraftforge.net/net/minecraftforge/forge/{version}/forge-{version}-installer.jar', f'https://bmclapi2.bangbang93.com/maven/net/minecraftforge/forge/{version}/forge-{version}-installer.jar']
        if core_id == 'neoforge':
            return [f'https://maven.neoforged.net/releases/net/neoforged/neoforge/{version}/neoforge-{version}-installer.jar']
    raise ValueError('不支持的核心')


async def real_core_versions(core_id: str):
    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        if core_id in {'paper','purpur'}:
            project = 'paper' if core_id == 'paper' else 'purpur'
            payload = (await client.get(f'https://api.papermc.io/v2/projects/{project}')).raise_for_status().json()
            return payload.get('versions', [])
        if core_id == 'velocity':
            payload = (await client.get('https://api.papermc.io/v2/projects/velocity')).raise_for_status().json()
            return payload.get('versions', [])
        if core_id == 'fabric':
            payload = (await client.get('https://meta.fabricmc.net/v2/versions/game')).raise_for_status().json()
            return [item['version'] for item in payload if item.get('stable')][:80]
        if core_id == 'vanilla':
            payload = (await client.get('https://piston-meta.mojang.com/mc/game/version_manifest_v2.json')).raise_for_status().json()
            return [item['id'] for item in payload.get('versions', []) if item.get('type') == 'release']
        if core_id == 'forge':
            xml = (await client.get('https://maven.minecraftforge.net/net/minecraftforge/forge/maven-metadata.xml')).text
            root = ElementTree.fromstring(xml); return [node.text for node in root.findall('.//version') if node.text]
        if core_id == 'neoforge':
            xml = (await client.get('https://maven.neoforged.net/releases/net/neoforged/neoforge/maven-metadata.xml')).text
            root = ElementTree.fromstring(xml); return [node.text for node in root.findall('.//version') if node.text]
        if core_id in {'forge','neoforge','bedrock','mcdr'}:
            return next(item['versions'] for item in CORE_CATALOG if item['id'] == core_id)
    return []


@app.get('/api/resources/cores/{core_id}/versions')
async def core_versions(request: Request, core_id: str):
    if isinstance((user := require_user(request)), JSONResponse): return user
    if not any(item['id'] == core_id for item in CORE_CATALOG): return JSONResponse({'ok':False,'message':'核心不存在'}, status_code=404)
    try: versions = await real_core_versions(core_id)
    except Exception as exc: return JSONResponse({'ok':False,'message':f'版本源暂不可用: {exc}'}, status_code=502)
    return {'ok':True,'core':core_id,'versions':versions,'source':'official'}


@app.get('/api/resources/mirrors')
def resources_mirrors(request: Request):
    if isinstance((user := require_user(request)), JSONResponse): return user
    return {'ok': True, 'mirrors': mirror_config()}


@app.get('/api/resources/versions')
async def resource_versions(request: Request, resource: str = 'paper'):
    if isinstance((user := require_user(request)), JSONResponse): return user
    config = mirror_config()[resource]; url = config['official']
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            data = (await client.get(url)).raise_for_status()
            payload = data.json()
        if resource == 'paper': return {'ok': True, 'resource': resource, 'versions': payload.get('versions', [])}
        manifest = payload
        return {'ok': True, 'resource': resource, 'versions': [item['id'] for item in manifest.get('versions', [])]}
    except Exception as exc:
        return JSONResponse({'ok': False, 'message': f'资源版本获取失败: {exc}'}, status_code=502)


@app.get('/api/resources/paper/{version}/builds')
async def paper_builds(request: Request, version: str):
    if isinstance((user := require_user(request)), JSONResponse): return user
    if not re.fullmatch(r'[0-9A-Za-z.\-]+', version): return JSONResponse({'ok': False, 'message': '版本格式无效'}, status_code=400)
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            payload = (await client.get(f'https://api.papermc.io/v2/projects/paper/versions/{version}')).raise_for_status().json()
        return {'ok': True, 'version': version, 'builds': payload.get('builds', [])}
    except Exception as exc:
        return JSONResponse({'ok': False, 'message': f'构建版本获取失败: {exc}'}, status_code=502)


def run_systemctl(*args: str) -> tuple[int, str]:
    try:
        result = subprocess.run(['systemctl', *args], capture_output=True, text=True, timeout=20, check=False)
        return result.returncode, (result.stdout or result.stderr).strip()
    except (FileNotFoundError, OSError) as exc:
        return 127, str(exc)


def unit_path(instance_id: str) -> Path:
    if not INSTANCE_RE.fullmatch(instance_id): raise ValueError('实例 ID 无效')
    return SYSTEMD_DIR / f'mc-{instance_id}.service'


def write_unit(instance_id: str, selected_core: str, java_version: str = '17', memory: str = '4G') -> Path:
    root = (SERVER_ROOT / instance_id).resolve(); core = (root / selected_core).resolve()
    if root not in core.parents or not core.is_file(): raise ValueError('核心文件不存在或路径非法')
    java = (JAVA_ROOT / java_version / 'bin' / 'java').resolve()
    if not java.is_file(): java = Path('/usr/bin/java')
    unit = f'''[Unit]\nDescription=Atmosphere Minecraft Server {instance_id}\nAfter=network.target\n\n[Service]\nType=simple\nUser=mcserver\nWorkingDirectory={root}\nExecStart={java} -Xms{memory} -Xmx{memory} -jar {core} nogui\nRestart=always\nRestartSec=10\nMemoryMax={memory}\nStandardOutput=journal\nStandardError=journal\n\n[Install]\nWantedBy=multi-user.target\n'''
    path = unit_path(instance_id); path.parent.mkdir(parents=True, exist_ok=True); path.write_text(unit, encoding='utf-8'); return path


def prepare_mcdr_environment(root: Path, system_python: str) -> str:
    venv = (root / '.venv').resolve()
    if root not in venv.parents:
        raise ValueError('MCDR 虚拟环境路径非法')
    subprocess.run([system_python, '-m', 'venv', str(venv)], check=True, capture_output=True, text=True, timeout=120)
    python_path = venv / ('Scripts' if os.name == 'nt' else 'bin') / ('python.exe' if os.name == 'nt' else 'python')
    if not python_path.is_file():
        raise RuntimeError('Python 虚拟环境创建失败')
    subprocess.run([str(python_path), '-m', 'pip', 'install', '--disable-pip-version-check', 'mcdreforged'], check=True, capture_output=True, text=True, timeout=180)
    return str(python_path)


def write_mcdr_unit(instance_id: str, python: str, memory: str = '4G') -> Path:
    root = (SERVER_ROOT / instance_id).resolve()
    script = (root / 'start_mcdr.py').resolve()
    if root not in script.parents or not script.is_file():
        raise ValueError('MCDR 启动脚本不存在或路径非法')
    unit = f'''[Unit]\nDescription=Atmosphere MCDR Server {instance_id}\nAfter=network.target\n\n[Service]\nType=simple\nUser=mcserver\nWorkingDirectory={root}\nExecStart={python} {script}\nRestart=always\nRestartSec=10\nMemoryMax={memory}\nStandardOutput=journal\nStandardError=journal\n\n[Install]\nWantedBy=multi-user.target\n'''
    path = unit_path(instance_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(unit, encoding='utf-8')
    return path


@app.post('/api/instances/{instance_id}/deploy')
def deploy_instance(request: Request, instance_id: str, selected_core: str = Form(...), java_version: str = Form('17'), memory: str = Form('4G')):
    if isinstance((user := require_user(request)), JSONResponse): return user
    try: write_unit(instance_id, selected_core, java_version, memory)
    except Exception as exc: return JSONResponse({'ok':False,'message':str(exc)}, status_code=400)
    reload_code, reload_output = run_systemctl('daemon-reload')
    enable_code, enable_output = run_systemctl('enable', f'mc-{instance_id}.service')
    start_code, start_output = run_systemctl('start', f'mc-{instance_id}.service')
    status = 'running' if start_code == 0 else 'failed'
    conn = db(); conn.execute('UPDATE instances SET status=?,selected_core=? WHERE id=?', (status, selected_core, instance_id)); conn.commit(); conn.close()
    return {'ok': start_code == 0, 'status': status, 'steps': {'daemon_reload': reload_code == 0, 'enable': enable_code == 0, 'start': start_code == 0}, 'output': start_output or enable_output or reload_output}


@app.post('/api/instances/{instance_id}/{action}')
def instance_action(request: Request, instance_id: str, action: str):
    if isinstance((user := require_user(request)), JSONResponse): return user
    if action not in {'start','stop','restart','disable'}: return JSONResponse({'ok':False,'message':'不支持的操作'}, status_code=400)
    code, output = run_systemctl(action, f'mc-{instance_id}.service')
    status = 'running' if action in {'start','restart'} and code == 0 else 'stopped' if action in {'stop','disable'} and code == 0 else 'failed'
    conn = db(); conn.execute('UPDATE instances SET status=? WHERE id=?', (status, instance_id)); conn.commit(); conn.close(); return {'ok': code == 0, 'status': status, 'output': output}


@app.get('/api/instances/{instance_id}/status')
def instance_status(request: Request, instance_id: str):
    if isinstance((user := require_user(request)), JSONResponse): return user
    code, output = run_systemctl('is-active', f'mc-{instance_id}.service'); return {'ok': True, 'status': 'running' if code == 0 else 'stopped', 'detail': output}


@app.get('/api/instances/{instance_id}/logs')
def instance_logs(request: Request, instance_id: str, lines: int = 100):
    if isinstance((user := require_user(request)), JSONResponse): return user
    lines = max(1, min(lines, 500)); code, output = run_systemctl('status', f'mc-{instance_id}.service', '--no-pager', '-n', str(lines)); return {'ok': code == 0, 'logs': output}


@app.get('/api/instances/{instance_id}/logs/stream')
def instance_logs_stream(request: Request, instance_id: str):
    if isinstance((user := require_user(request)), JSONResponse): return user
    def events():
        code, output = run_systemctl('status', f'mc-{instance_id}.service', '--no-pager', '-n', '100')
        yield f'data: {json.dumps({"ok": code == 0, "logs": output}, ensure_ascii=False)}\\n\\n'
    return StreamingResponse(events(), media_type='text/event-stream', headers={'Cache-Control':'no-cache','X-Accel-Buffering':'no'})




@app.get('/api/instances/{instance_id}/monitor')
def instance_monitor(request: Request, instance_id: str):
    if isinstance((user := require_user(request)), JSONResponse):
        return user
    if not instance_row(instance_id):
        return JSONResponse({'ok': False, 'message': '实例不存在'}, status_code=404)
    code, output = run_systemctl('show', f'mc-{instance_id}.service', '--property=MainPID')
    values = dict(line.split('=', 1) for line in output.splitlines() if '=' in line)
    pid = int(values.get('MainPID', '0') or 0)
    cpu = 0.0
    memory = 0.0
    try:
        import psutil
        if pid:
            process = psutil.Process(pid)
            cpu = process.cpu_percent(interval=0.05)
            memory = process.memory_percent()
    except (ImportError, ValueError):
        pass
    return {'ok': code == 0, 'cpu_percent': round(cpu, 2), 'memory_percent': round(memory, 2), 'pid': pid}


def safe_instance_path(instance_id: str, requested: str) -> tuple[Path, Path]:
    root = instance_root(instance_id)
    candidate = (root / requested.lstrip('/')).resolve()
    if candidate != root and root not in candidate.parents:
        raise ValueError('路径超出实例目录')
    return root, candidate


@app.get('/api/instances/{instance_id}/files')
def list_instance_files(request: Request, instance_id: str, path: str = '/'):
    if isinstance((user := require_user(request)), JSONResponse):
        return user
    try:
        _, directory = safe_instance_path(instance_id, path)
        if not directory.is_dir():
            return JSONResponse({'ok': False, 'message': '目录不存在'}, status_code=404)
        root = instance_root(instance_id)
        entries = []
        for item in sorted(directory.iterdir(), key=lambda entry: (not entry.is_dir(), entry.name.lower())):
            relative = '/' + str(item.relative_to(root)).replace('\\', '/')
            entries.append({'name': item.name, 'path': relative, 'type': 'directory' if item.is_dir() else 'file', 'size': item.stat().st_size if item.is_file() else None})
        return {'ok': True, 'path': path, 'entries': entries}
    except ValueError as exc:
        return JSONResponse({'ok': False, 'message': str(exc)}, status_code=400)


@app.get('/api/instances/{instance_id}/files/content')
def read_instance_file(request: Request, instance_id: str, path: str):
    if isinstance((user := require_user(request)), JSONResponse):
        return user
    try:
        _, target = safe_instance_path(instance_id, path)
        if not target.is_file() or target.stat().st_size > 5 * 1024 * 1024:
            return JSONResponse({'ok': False, 'message': '文件不存在或超过 5MB'}, status_code=400)
        return {'ok': True, 'path': path, 'content': target.read_text(encoding='utf-8')}
    except (ValueError, UnicodeDecodeError, OSError) as exc:
        return JSONResponse({'ok': False, 'message': f'文件读取失败: {exc}'}, status_code=400)


class FileSavePayload(BaseModel):
    path: str = Field(min_length=1, max_length=512)
    content: str = Field(max_length=5 * 1024 * 1024)


@app.post('/api/instances/{instance_id}/files/save')
def save_instance_file(request: Request, instance_id: str, payload: FileSavePayload):
    if isinstance((user := require_user(request)), JSONResponse):
        return user
    try:
        _, target = safe_instance_path(instance_id, payload.path)
        if target.exists() and target.is_dir():
            return JSONResponse({'ok': False, 'message': '不能覆盖目录'}, status_code=400)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(payload.content, encoding='utf-8')
        return {'ok': True, 'path': payload.path}
    except (ValueError, OSError) as exc:
        return JSONResponse({'ok': False, 'message': f'文件保存失败: {exc}'}, status_code=400)


@app.get('/api/instances/{instance_id}/metrics')
def instance_metrics(request: Request, instance_id: str):
    if isinstance((user := require_user(request)), JSONResponse): return user
    code, output = run_systemctl('show', f'mc-{instance_id}.service', '--property=MemoryCurrent,MemoryMax,CPUUsageNSec,ActiveState')
    values = {}
    for line in output.splitlines():
        if '=' in line:
            key, value = line.split('=', 1); values[key] = value
    return {'ok': code == 0, 'cpu_ns': values.get('CPUUsageNSec','0'), 'memory_bytes': values.get('MemoryCurrent','0'), 'memory_max': values.get('MemoryMax','0'), 'active': values.get('ActiveState','unknown')}


@app.delete('/api/instances/{instance_id}')
def delete_instance(request: Request, instance_id: str):
    if isinstance((user := require_user(request)), JSONResponse): return user
    if not INSTANCE_RE.fullmatch(instance_id): return JSONResponse({'ok':False,'message':'实例 ID 无效'}, status_code=400)
    stop_code, stop_output = run_systemctl('stop', f'mc-{instance_id}.service')
    disable_code, disable_output = run_systemctl('disable', f'mc-{instance_id}.service')
    unit = unit_path(instance_id)
    try:
        if unit.exists(): unit.unlink()
        run_systemctl('daemon-reload')
        shutil.rmtree((SERVER_ROOT / instance_id).resolve(), ignore_errors=False)
    except Exception as exc:
        return JSONResponse({'ok':False,'message':f'删除失败: {exc}'}, status_code=400)
    conn = db(); conn.execute('DELETE FROM instances WHERE id=?', (instance_id,)); conn.commit(); conn.close()
    return {'ok': stop_code == 0 or disable_code == 0, 'steps': {'stop': stop_code == 0, 'disable': disable_code == 0, 'unit_removed': True, 'data_removed': True}, 'output': stop_output or disable_output}


@app.get('/api/instances')
def list_instances(request: Request):
    if isinstance((user := require_user(request)), JSONResponse): return user
    conn = db(); rows = conn.execute('SELECT id,name,port,jar_name,status,created_at FROM instances ORDER BY created_at DESC').fetchall(); conn.close(); return {'ok': True, 'instances': [dict(row) for row in rows]}


@app.post('/api/instances/package')
async def upload_package(request: Request, instance_id: str = Form(...), name: str = Form(...), port: int = Form(25565), eula: bool = Form(False), package: UploadFile = File(...)):
    if isinstance((user := require_user(request)), JSONResponse): return user
    instance_id = instance_id.strip().lower(); filename = (package.filename or '').lower()
    if not INSTANCE_RE.fullmatch(instance_id): return JSONResponse({'ok': False, 'message': '实例 ID 格式无效'}, status_code=400)
    if not eula: return JSONResponse({'ok': False, 'message': '必须确认 EULA'}, status_code=400)
    if not (filename.endswith('.zip') or filename.endswith('.tar.gz') or filename.endswith('.tgz')): return JSONResponse({'ok': False, 'message': '仅支持 ZIP 或 TAR.GZ'}, status_code=400)
    conn = db()
    if conn.execute('SELECT 1 FROM instances WHERE id=? OR port=?', (instance_id, port)).fetchone(): conn.close(); return JSONResponse({'ok': False, 'message': '实例 ID 或端口已存在'}, status_code=409)
    temp = ROOT / 'tmp-packages'; temp.mkdir(exist_ok=True); archive = temp / f'{secrets.token_hex(12)}-{Path(filename).name}'; target = SERVER_ROOT / instance_id
    try:
        total = 0
        with archive.open('wb') as output:
            while chunk := await package.read(1024 * 1024):
                total += len(chunk)
                if total > MAX_PACKAGE_BYTES: raise ValueError('整合包超过 500MB 限制')
                output.write(chunk)
        target.mkdir(parents=True, exist_ok=False); extract_archive(archive, target); candidates = find_core_candidates(target)
        (target / 'eula.txt').write_text('eula=true\n'); (target / 'server.properties').write_text(f'online-mode=false\nserver-port={port}\n')
        recommended = next((x['path'] for x in candidates if x.get('recommended')), None)
        conn.execute('INSERT INTO instances VALUES(?,?,?,?,?,?,?,?)', (instance_id, name.strip(), port, package.filename, 'stopped', int(time.time()), json.dumps(candidates), recommended)); conn.commit()
        if recommended and recommended.endswith('.jar') and shutil.which('java'):
            write_unit(instance_id, recommended, '21', '4G')
            run_systemctl('daemon-reload')
            run_systemctl('enable', f'mc-{instance_id}.service')
    except Exception as exc:
        shutil.rmtree(target, ignore_errors=True); conn.close(); archive.unlink(missing_ok=True); return JSONResponse({'ok': False, 'message': str(exc)}, status_code=400)
    archive.unlink(missing_ok=True); conn.close(); return {'ok': True, 'message': '正在解压并分析核心', 'needs_core_selection': not bool(candidates), 'core_candidates': candidates, 'instance': {'id': instance_id}}


async def stream_download(task_id: str, urls: list[str], destination: Path):
    task = DOWNLOAD_TASKS[task_id]; destination.parent.mkdir(parents=True, exist_ok=True)
    for index, url in enumerate(urls):
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, read=120.0), follow_redirects=True) as client:
                async with client.stream('GET', url) as response:
                    response.raise_for_status(); total = int(response.headers.get('content-length', '0')); received = 0; started = time.monotonic()
                    with destination.open('wb') as output:
                        async for chunk in response.aiter_bytes(1024 * 1024):
                            output.write(chunk); received += len(chunk); elapsed = max(time.monotonic() - started, .001)
                            task.update({'status':'downloading','percent':round(received / total * 100, 1) if total else 0,'speed':f'{received / elapsed / 1024 / 1024:.2f} MB/s','source':url})
            task.update({'status':'completed','percent':100,'speed':'—','source':url}); return
        except Exception as exc:
            task['last_error'] = str(exc)
            if destination.exists(): destination.unlink()
            if index == len(urls) - 1: task.update({'status':'failed','percent':0,'speed':'—'})


@app.post('/api/deploy/tasks')
async def create_download_task(request: Request, instance_id: str = Form(...), resource: str = Form('paper'), version: str = Form('1.20.4'), java_version: str = Form('17')):
    if isinstance((user := require_user(request)), JSONResponse): return user
    core_id = resource.lower();
    if not INSTANCE_RE.fullmatch(instance_id) or core_id not in {item['id'] for item in CORE_CATALOG} or java_version not in {'8','16','17','21'}:
        return JSONResponse({'ok': False, 'message': '部署参数无效'}, status_code=400)
    task_id = secrets.token_urlsafe(12); target = SERVER_ROOT / instance_id
    try:
        urls = await core_download_urls(core_id, version)
    except Exception as exc:
        return JSONResponse({'ok': False, 'message': f'核心下载地址解析失败: {exc}'}, status_code=502)
    filename = 'server.jar'
    DOWNLOAD_TASKS[task_id] = {'status':'queued','percent':0,'speed':'0 MB/s','source':'—','resource':resource,'version':version,'java_version':java_version}
    asyncio.create_task(stream_download(task_id, urls, target / filename))
    target.mkdir(parents=True, exist_ok=True); (target / 'eula.txt').write_text('eula=true\\n', encoding='utf-8')
    return {'ok': True, 'task_id': task_id, 'resource': resource, 'version': version, 'java_version': java_version, 'java_recommendation': JAVA_BY_VERSION.get(version, '21')}


@app.get('/api/deploy/tasks/{task_id}')
def download_task(request: Request, task_id: str):
    if isinstance((user := require_user(request)), JSONResponse): return user
    task = DOWNLOAD_TASKS.get(task_id)
    return task or JSONResponse({'ok': False, 'message': '任务不存在'}, status_code=404)


@app.get('/api/deploy/stream')
def deploy_stream(request: Request, task_id: str | None = None):
    if isinstance((user := require_user(request)), JSONResponse): return user
    def events():
        if task_id and task_id in DOWNLOAD_TASKS:
            yield f'data: {json.dumps(DOWNLOAD_TASKS[task_id], ensure_ascii=False)}\n\n'
        else:
            for percent, stage, speed in [(8, '准备部署', '0 KB/s'), (42, '正在解压...', '18.4 MB/s'), (78, '正在分析核心...', '—'), (100, '等待启动', '—')]:
                yield f'data: {json.dumps({"percent": percent, "stage": stage, "speed": speed}, ensure_ascii=False)}\n\n'
    return StreamingResponse(events(), media_type='text/event-stream', headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})


@app.post('/api/instances/core')
async def select_core(request: Request, instance_id: str = Form(...), selected_core: str = Form(...)):
    if isinstance((user := require_user(request)), JSONResponse): return user
    if Path(selected_core).name != selected_core or not selected_core.endswith('.jar'): return JSONResponse({'ok': False, 'message': '核心文件选择无效'}, status_code=400)
    target = (SERVER_ROOT / instance_id / selected_core).resolve(); root = (SERVER_ROOT / instance_id).resolve()
    if not target.is_file() or root not in target.parents: return JSONResponse({'ok': False, 'message': '核心文件不存在'}, status_code=400)
    conn = db(); conn.execute('UPDATE instances SET selected_core=? WHERE id=?', (selected_core, instance_id)); conn.commit(); conn.close(); return {'ok': True}

class PowerPayload(BaseModel):
    action: str


class CommandPayload(BaseModel):
    command: str = Field(min_length=1, max_length=512)


def instance_row(instance_id: str):
    if not INSTANCE_RE.fullmatch(instance_id):
        return None
    conn = db()
    row = conn.execute('SELECT id,name,port,jar_name,status,created_at,selected_core FROM instances WHERE id=?', (instance_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def instance_root(instance_id: str) -> Path:
    if not INSTANCE_RE.fullmatch(instance_id):
        raise ValueError('实例 ID 无效')
    return (SERVER_ROOT / instance_id).resolve()


@app.get('/api/instances/{instance_id}')
def get_instance(request: Request, instance_id: str):
    if isinstance((user := require_user(request)), JSONResponse):
        return user
    row = instance_row(instance_id)
    return row or JSONResponse({'ok': False, 'message': '实例不存在'}, status_code=404)


@app.post('/api/instances/{instance_id}/power')
def power_instance(request: Request, instance_id: str, payload: PowerPayload):
    if isinstance((user := require_user(request)), JSONResponse):
        return user
    if payload.action not in {'start', 'stop', 'restart'}:
        return JSONResponse({'ok': False, 'message': '不支持的电源操作'}, status_code=400)
    if not instance_row(instance_id):
        return JSONResponse({'ok': False, 'message': '实例不存在'}, status_code=404)
    code, output = run_systemctl(payload.action, f'mc-{instance_id}.service')
    status = 'running' if code == 0 and payload.action in {'start', 'restart'} else 'stopped' if code == 0 else 'failed'
    conn = db()
    conn.execute('UPDATE instances SET status=? WHERE id=?', (status, instance_id))
    conn.commit()
    conn.close()
    return {'ok': code == 0, 'status': status, 'output': output}


@app.post('/api/instances/{instance_id}/command')
def instance_command(request: Request, instance_id: str, payload: CommandPayload):
    if isinstance((user := require_user(request)), JSONResponse):
        return user
    if not instance_row(instance_id):
        return JSONResponse({'ok': False, 'message': '实例不存在'}, status_code=404)
    return JSONResponse({'ok': False, 'message': 'RCON 尚未配置，请先在实例设置中配置 RCON'}, status_code=501)


@app.get('/api/instances/{instance_id}/players')
def instance_players(request: Request, instance_id: str):
    if isinstance((user := require_user(request)), JSONResponse):
        return user
    if not instance_row(instance_id):
        return JSONResponse({'ok': False, 'message': '实例不存在'}, status_code=404)
    return {'ok': True, 'players': []}


@app.get('/api/instances/{instance_id}/monitor')
def instance_monitor(request: Request, instance_id: str):
    if isinstance((user := require_user(request)), JSONResponse):
        return user
    if not instance_row(instance_id):
        return JSONResponse({'ok': False, 'message': '实例不存在'}, status_code=404)
    code, output = run_systemctl('show', f'mc-{instance_id}.service', '--property=MainPID')
    values = dict(line.split('=', 1) for line in output.splitlines() if '=' in line)
    pid = int(values.get('MainPID', '0') or 0)
    cpu = memory = 0.0
    try:
        import psutil
        if pid:
            process = psutil.Process(pid)
            cpu = process.cpu_percent(interval=0.05)
            memory = process.memory_percent()
    except (ImportError, ValueError):
        pass
    return {'ok': code == 0, 'cpu_percent': round(cpu, 2), 'memory_percent': round(memory, 2), 'pid': pid}


def safe_instance_path(instance_id: str, requested: str) -> tuple[Path, Path]:
    root = instance_root(instance_id)
    candidate = (root / requested.lstrip('/')).resolve()
    if candidate != root and root not in candidate.parents:
        raise ValueError('路径超出实例目录')
    return root, candidate


@app.get('/api/instances/{instance_id}/files')
def list_instance_files(request: Request, instance_id: str, path: str = '/'):
    if isinstance((user := require_user(request)), JSONResponse):
        return user
    try:
        root, directory = safe_instance_path(instance_id, path)
        if not directory.is_dir():
            return JSONResponse({'ok': False, 'message': '目录不存在'}, status_code=404)
        entries = []
        for item in sorted(directory.iterdir(), key=lambda entry: (not entry.is_dir(), entry.name.lower())):
            relative = '/' + str(item.relative_to(root)).replace('\\', '/')
            entries.append({'name': item.name, 'path': relative, 'type': 'directory' if item.is_dir() else 'file', 'size': item.stat().st_size if item.is_file() else None})
        return {'ok': True, 'path': path, 'entries': entries}
    except ValueError as exc:
        return JSONResponse({'ok': False, 'message': str(exc)}, status_code=400)


@app.get('/api/instances/{instance_id}/files/content')
def read_instance_file(request: Request, instance_id: str, path: str):
    if isinstance((user := require_user(request)), JSONResponse):
        return user
    try:
        _, target = safe_instance_path(instance_id, path)
        if not target.is_file() or target.stat().st_size > 5 * 1024 * 1024:
            return JSONResponse({'ok': False, 'message': '文件不存在或超过 5MB'}, status_code=400)
        return {'ok': True, 'path': path, 'content': target.read_text(encoding='utf-8')}
    except (ValueError, UnicodeDecodeError, OSError) as exc:
        return JSONResponse({'ok': False, 'message': f'文件读取失败: {exc}'}, status_code=400)


class FileSavePayload(BaseModel):
    path: str = Field(min_length=1, max_length=512)
    content: str = Field(max_length=5 * 1024 * 1024)


@app.post('/api/instances/{instance_id}/files/save')
def save_instance_file(request: Request, instance_id: str, payload: FileSavePayload):
    if isinstance((user := require_user(request)), JSONResponse):
        return user
    try:
        _, target = safe_instance_path(instance_id, payload.path)
        if target.exists() and target.is_dir():
            return JSONResponse({'ok': False, 'message': '不能覆盖目录'}, status_code=400)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(payload.content, encoding='utf-8')
        return {'ok': True, 'path': payload.path}
    except (ValueError, OSError) as exc:
        return JSONResponse({'ok': False, 'message': f'文件保存失败: {exc}'}, status_code=400)


@app.get('/api/instances/{instance_id}/backups')
def list_backups(request: Request, instance_id: str):
    if isinstance((user := require_user(request)), JSONResponse):
        return user
    try:
        root = instance_root(instance_id)
        backup_dir = root / 'backups'
        backup_dir.mkdir(parents=True, exist_ok=True)
        return {'ok': True, 'backups': [{'name': item.name, 'size': item.stat().st_size, 'created_at': item.stat().st_mtime} for item in sorted(backup_dir.glob('*.tar.gz'), key=lambda item: item.stat().st_mtime, reverse=True)]}
    except ValueError as exc:
        return JSONResponse({'ok': False, 'message': str(exc)}, status_code=400)


@app.post('/api/instances/{instance_id}/backups')
def create_backup(request: Request, instance_id: str):
    if isinstance((user := require_user(request)), JSONResponse):
        return user
    try:
        root = instance_root(instance_id)
        if not root.is_dir():
            return JSONResponse({'ok': False, 'message': '实例目录不存在'}, status_code=404)
        backup_dir = root / 'backups'
        backup_dir.mkdir(parents=True, exist_ok=True)
        filename = f"backup-{time.strftime('%Y%m%d-%H%M%S')}.tar.gz"
        archive = shutil.make_archive(str(backup_dir / filename[:-7]), 'gztar', root=str(root), base_dir='.', logger=None)
        return {'ok': True, 'name': Path(archive).name}
    except (ValueError, OSError) as exc:
        return JSONResponse({'ok': False, 'message': f'备份失败: {exc}'}, status_code=400)


@app.post('/api/instances/package/inspect')
async def inspect_package(request: Request, instance_id: str = Form(...), name: str = Form(...), port: int = Form(25565), eula: bool = Form(False), package: UploadFile = File(...)):
    if isinstance((user := require_user(request)), JSONResponse):
        return user
    filename = (package.filename or '').lower()
    if not (filename.endswith('.zip') or filename.endswith('.tar.gz') or filename.endswith('.tgz')):
        return JSONResponse({'ok': False, 'message': '仅支持 ZIP、TAR.GZ 或 TGZ'}, status_code=400)
    temp = ROOT / 'tmp-packages'; temp.mkdir(exist_ok=True)
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
        candidates = find_core_candidates(target)
        return {'ok': True, 'core_candidates': candidates, 'members': total}
    except Exception as exc:
        return JSONResponse({'ok': False, 'message': f'整合包分析失败: {exc}'}, status_code=400)
    finally:
        archive.unlink(missing_ok=True)
        shutil.rmtree(target, ignore_errors=True)


class ModeDeployPayload(BaseModel):
    mode: str
    instance_id: str
    port: int = Field(ge=1, le=65535)
    version: str = ''
    resource: str = ''
    java_version: str = '21'
    memory: int = Field(default=4096, ge=512, le=131072)


async def download_file(url: str, destination: Path):
    async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, read=180.0), follow_redirects=True) as client:
        async with client.stream('GET', url) as response:
            response.raise_for_status()
            with destination.open('wb') as output:
                async for chunk in response.aiter_bytes(1024 * 1024):
                    output.write(chunk)


@app.post('/api/deploy/modes')
async def deploy_mode(request: Request, payload: ModeDeployPayload):
    if isinstance((user := require_user(request)), JSONResponse):
        return user
    if payload.mode not in {'quick', 'bedrock', 'mcdr'}:
        return JSONResponse({'ok': False, 'message': '部署模式无效'}, status_code=400)
    instance_id = payload.instance_id.lower()
    if not INSTANCE_RE.fullmatch(instance_id):
        return JSONResponse({'ok': False, 'message': '实例 ID 无效'}, status_code=400)
    java = shutil.which('java')
    python = shutil.which('python3') or shutil.which('python')
    if payload.mode == 'mcdr' and not python:
        return JSONResponse({'ok': False, 'message': '当前主机未检测到 Python，请先安装 Python 3'}, status_code=503)
    if payload.mode == 'quick' and not java:
        return JSONResponse({'ok': False, 'message': '当前主机未检测到 Java，请先安装 Java 或配置 Java 环境'}, status_code=503)
    conn = db()
    if conn.execute('SELECT 1 FROM instances WHERE id=? OR port=?', (instance_id, payload.port)).fetchone():
        conn.close()
        return JSONResponse({'ok': False, 'message': '实例 ID 或端口已存在'}, status_code=409)
    root = (SERVER_ROOT / instance_id).resolve()
    root.mkdir(parents=True, exist_ok=False)
    selected_core = None
    try:
        if payload.mode == 'quick':
            if payload.resource not in {item['id'] for item in CORE_CATALOG} or not payload.version:
                raise ValueError('快速部署缺少核心或版本')
            urls = await core_download_urls(payload.resource, payload.version)
            jar = root / 'server.jar'
            await download_file(urls[0], jar)
            selected_core = 'server.jar'
        elif payload.mode == 'bedrock':
            raise ValueError('基岩版下载源尚未配置，请先配置 Bedrock 官方镜像')
        else:
            python = prepare_mcdr_environment(root, python)
            (root / 'start_mcdr.py').write_text("from mcdreforged.api.all import *\\n\\nserver = ServerInterface.get_instance()\\n", encoding='utf-8')
            selected_core = 'start_mcdr.py'
            write_mcdr_unit(instance_id, python, f'{payload.memory}M')
            run_systemctl('daemon-reload')
            run_systemctl('enable', f'mc-{instance_id}.service')
        (root / 'eula.txt').write_text('eula=true\\n', encoding='utf-8')
        (root / 'server.properties').write_text(f'server-port={payload.port}\\n', encoding='utf-8')
        conn.execute('INSERT INTO instances(id,name,port,jar_name,status,created_at,core_candidates,selected_core) VALUES(?,?,?,?,?,?,?,?)', (instance_id, instance_id, payload.port, selected_core or payload.mode, 'stopped', int(time.time()), '[]', selected_core))
        conn.commit()
        if payload.mode == 'quick':
            write_unit(instance_id, selected_core, payload.java_version, f'{payload.memory}M')
            run_systemctl('daemon-reload')
            run_systemctl('enable', f'mc-{instance_id}.service')
        return {'ok': True, 'mode': payload.mode, 'instance': {'id': instance_id}, 'status': 'stopped', 'environment': {'java': java, 'python': python}, 'core': selected_core}
    except Exception as exc:
        conn.rollback()
        shutil.rmtree(root, ignore_errors=True)
        return JSONResponse({'ok': False, 'message': f'部署失败: {exc}'}, status_code=502)
    finally:
        conn.close()


@app.get('/api/instances/{instance_id}/logs/stream')
def instance_logs_live(request: Request, instance_id: str):
    if isinstance((user := require_user(request)), JSONResponse):
        return user
    if not instance_row(instance_id):
        return JSONResponse({'ok': False, 'message': '实例不存在'}, status_code=404)

    def events():
        command = ['journalctl', '-u', f'mc-{instance_id}', '-n', '50', '-f', '--output=cat']
        try:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
            assert process.stdout is not None
            for line in iter(process.stdout.readline, ''):
                if line:
                    yield f'data: {json.dumps({"line": line.rstrip()}, ensure_ascii=False)}\\n\\n'
        except (FileNotFoundError, OSError) as exc:
            yield f'data: {json.dumps({"line": f"[log stream unavailable] {exc}"}, ensure_ascii=False)}\\n\\n'

    return StreamingResponse(events(), media_type='text/event-stream', headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})