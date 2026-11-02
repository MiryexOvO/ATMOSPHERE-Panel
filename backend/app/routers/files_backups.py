from fastapi import APIRouter, Request, Query, UploadFile, File, Form
from pydantic import BaseModel
from fastapi.responses import JSONResponse, FileResponse
from ..core.security import require_user
from ..core.config import SERVER_ROOT
from pathlib import Path
import shutil, time
import asyncio, secrets, zipfile, tarfile
from ..archive_service import extract_archive
from ..services.panel_settings import read_settings, audit
router=APIRouter(prefix='/api/instances',tags=['files-backups'])

def safe_path(instance_id:str, requested:str)->tuple[Path,Path]:
    if not instance_id or '/' in instance_id or '\\' in instance_id or ':' in instance_id or '..' in instance_id: raise ValueError('实例 ID 无效')
    root=(SERVER_ROOT/instance_id).resolve(); target=(root/requested.lstrip('/')).resolve()
    if SERVER_ROOT.resolve() not in root.parents: raise ValueError('实例路径无效')
    if target!=root and root not in target.parents: raise ValueError('路径超出实例目录')
    return root,target

class PropertiesPayload(BaseModel):
    properties: dict[str, object]


class FileAction(BaseModel):
    action: str
    path: str
    destination: str = ''


@router.get('/{instance_id}/files/download')
def download_file(request: Request, instance_id: str, path: str):
    if isinstance(user := require_user(request), JSONResponse): return user
    try:
        _, target = safe_path(instance_id, path)
        if not target.is_file(): raise ValueError('文件不存在')
        return FileResponse(target, filename=target.name)
    except (ValueError, OSError) as exc:
        return JSONResponse({'message': str(exc)}, status_code=400)


@router.post('/{instance_id}/files/upload')
async def upload_file(request: Request, instance_id: str, path: str = Form('/'), file: UploadFile = File(...)):
    if isinstance(user := require_user(request), JSONResponse): return user
    temporary = None
    try:
        root, directory = safe_path(instance_id, path)
        if not directory.is_dir(): raise ValueError('目标目录不存在')
        name = file.filename or ''
        if Path(name).name != name or '/' in name or '\\' in name: raise ValueError('文件名无效')
        _, target = safe_path(instance_id, (directory / name).relative_to(root).as_posix())
        if target.exists(): raise ValueError('同名文件已存在，请先重命名')
        temporary = directory / ('.upload-' + secrets.token_hex(8))
        limit, total = read_settings()['upload_limit_mb'] * 1024 * 1024, 0
        with temporary.open('wb') as output:
            while chunk := await file.read(1024 * 1024):
                total += len(chunk)
                if total > limit: raise ValueError('文件超过面板上传限制')
                output.write(chunk)
        temporary.rename(target)
        return {'ok': True}
    except (ValueError, OSError) as exc:
        return JSONResponse({'message': str(exc)}, status_code=400)
    finally:
        if temporary and temporary.exists(): temporary.unlink()


@router.post('/{instance_id}/files/action')
async def file_action(request: Request, instance_id: str, payload: FileAction):
    if isinstance(user := require_user(request), JSONResponse): return user
    temp = None
    try:
        root, target = safe_path(instance_id, payload.path)
        if target == root: raise ValueError('不能操作实例根目录')
        destination = safe_path(instance_id, payload.destination)[1] if payload.destination else None
        # 所有变更均校验解析后的路径，不覆盖已有文件。
        if payload.action == 'mkdir': target.mkdir(parents=False, exist_ok=False)
        elif payload.action == 'create':
            with target.open('x', encoding='utf-8'): pass
        elif payload.action == 'delete':
            if target.is_dir(): await asyncio.to_thread(shutil.rmtree, target)
            else: target.unlink()
        elif payload.action in {'rename', 'move', 'copy'}:
            if not destination or destination == root or destination.exists(): raise ValueError('目标无效或已存在')
            if target in destination.parents: raise ValueError('不能复制或移动到自身目录内')
            if payload.action == 'copy':
                await asyncio.to_thread(shutil.copytree if target.is_dir() else shutil.copy2, target, destination)
            else: target.rename(destination)
        elif payload.action == 'extract':
            if not target.is_file() or not destination or destination.exists(): raise ValueError('请指定新的解压目录')
            # 解压到临时目录，失败不污染目标目录。
            temp = root / ('.extract-' + secrets.token_hex(8))
            await asyncio.to_thread(extract_archive, target, temp)
            temp.rename(destination)
        elif payload.action == 'compress':
            if not target.exists() or not destination or destination.exists() or destination.suffix != '.zip': raise ValueError('请指定新的 ZIP 文件')
            temp = root / ('.compress-' + secrets.token_hex(8) + '.zip')
            def compress():
                with zipfile.ZipFile(temp, 'w', zipfile.ZIP_DEFLATED) as output:
                    if target.is_file(): output.write(target, target.name)
                    else:
                        for item in target.rglob('*'):
                            if item.is_file() and root in item.resolve().parents:
                                output.write(item, item.relative_to(target.parent))
            await asyncio.to_thread(compress)
            temp.rename(destination)
        else: raise ValueError('未知文件操作')
        # 记录文件动作与路径，不记录文件内容。
        import json
        audit(user['id'],'file.'+payload.action,json.dumps({'instance':instance_id,'path':payload.path,'destination':payload.destination},ensure_ascii=False))
        return {'ok': True}
    except (ValueError, OSError, zipfile.BadZipFile, tarfile.TarError) as exc:
        return JSONResponse({'message': str(exc)}, status_code=400)
    finally:
        if temp and temp.exists() and root in temp.resolve().parents:
            if temp.is_dir(): shutil.rmtree(temp)
            else: temp.unlink()


def parse_property_value(value: str) -> object:
    normalized = value.strip()
    if normalized.lower() in {'true', 'false'}:
        return normalized.lower() == 'true'
    try:
        return int(normalized)
    except ValueError:
        return normalized


@router.get('/{instance_id}/properties')
def get_properties(request: Request, instance_id: str):
    if isinstance((user := require_user(request)), JSONResponse):
        return user
    try:
        _, target = safe_path(instance_id, '/server.properties')
        if not target.is_file():
            return {'ok': True, 'properties': {}, 'exists': False}
        parsed = {}
        for line in target.read_text(encoding='utf-8').splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith('#') or '=' not in stripped:
                continue
            key, value = stripped.split('=', 1)
            parsed[key.strip()] = parse_property_value(value)
        return {'ok': True, 'properties': parsed, 'exists': True}
    except (ValueError, OSError, UnicodeError) as exc:
        return JSONResponse({'ok': False, 'message': f'属性读取失败: {exc}'}, status_code=400)


@router.put('/{instance_id}/properties')
def update_properties(request: Request, instance_id: str, payload: PropertiesPayload):
    if isinstance((user := require_user(request)), JSONResponse):
        return user
    try:
        _, target = safe_path(instance_id, '/server.properties')
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.is_file():
            shutil.copy2(target, target.with_name('server.properties.bak'))
        lines = []
        for key, value in payload.properties.items():
            if not isinstance(key, str) or not key or '/' in key or '\n' in key or '=' in key:
                raise ValueError('属性键名无效')
            if isinstance(value, bool):
                serialized = 'true' if value else 'false'
            elif isinstance(value, (str, int, float)):
                serialized = str(value)
            else:
                raise ValueError(f'属性值无效: {key}')
            if '\n' in serialized or '\r' in serialized:
                raise ValueError('属性值包含非法换行')
            lines.append(f'{key}={serialized}')
        target.write_text('\n'.join(lines) + ('\n' if lines else ''), encoding='utf-8')
        return {'ok': True, 'properties': payload.properties}
    except (ValueError, OSError) as exc:
        return JSONResponse({'ok': False, 'message': f'属性保存失败: {exc}'}, status_code=400)

@router.get('/{instance_id}/files')
def files(request:Request,instance_id:str,path:str='/'):
    if isinstance((user:=require_user(request)),JSONResponse): return user
    try:
        root,directory=safe_path(instance_id,path)
        if not directory.is_dir():
            return {'ok': True, 'path': path, 'entries': []}
        entries=[]
        for item in sorted(directory.iterdir(),key=lambda p:(not p.is_dir(),p.name.lower())):
            if item.is_symlink() or (hasattr(item,'is_junction') and item.is_junction()): continue
            entries.append({'name':item.name,'path':'/'+str(item.relative_to(root)).replace('\\','/'),'type':'directory' if item.is_dir() else 'file','size':item.stat().st_size if item.is_file() else None,'modified_at':item.stat().st_mtime})
        return {'ok':True,'path':path,'entries':entries}
    except ValueError as exc: return JSONResponse({'ok':False,'message':str(exc)},status_code=400)

@router.get('/{instance_id}/backups')
def backups(request:Request,instance_id:str):
    if isinstance((user:=require_user(request)),JSONResponse): return user
    try:
        root,_=safe_path(instance_id,'/'); directory=root/'backups'; directory.mkdir(parents=True,exist_ok=True)
        return {'ok':True,'backups':[{'name':p.name,'size':p.stat().st_size,'created_at':p.stat().st_mtime} for p in directory.glob('*.tar.gz')]}
    except ValueError as exc: return JSONResponse({'ok':False,'message':str(exc)},status_code=400)

@router.get('/{instance_id}/files/content')
def file_content(request: Request, instance_id: str, path: str):
    if isinstance((user := require_user(request)), JSONResponse): return user
    try:
        _, target = safe_path(instance_id, path)
        if not target.is_file() or target.stat().st_size > 5 * 1024 * 1024:
            return JSONResponse({'ok': False, 'message': '文件不存在或超过 5MB'}, status_code=400)
        return {'ok': True, 'path': path, 'content': target.read_text(encoding='utf-8')}
    except (ValueError, UnicodeDecodeError, OSError) as exc:
        return JSONResponse({'ok': False, 'message': f'文件读取失败: {exc}'}, status_code=400)


@router.post('/{instance_id}/files/save')
def save_file(request: Request, instance_id: str, payload: dict):
    if isinstance((user := require_user(request)), JSONResponse): return user
    try:
        path = str(payload.get('path', ''))
        content = str(payload.get('content', ''))
        if len(content.encode('utf-8')) > 5 * 1024 * 1024:
            return JSONResponse({'ok': False, 'message': '文件超过 5MB'}, status_code=400)
        _, target = safe_path(instance_id, path)
        if target.exists() and target.is_dir():
            return JSONResponse({'ok': False, 'message': '不能覆盖目录'}, status_code=400)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding='utf-8')
        return {'ok': True, 'path': path}
    except (ValueError, OSError) as exc:
        return JSONResponse({'ok': False, 'message': f'文件保存失败: {exc}'}, status_code=400)


@router.post('/{instance_id}/backups')
def create_backup(request: Request, instance_id: str):
    if isinstance((user := require_user(request)), JSONResponse): return user
    try:
        root, _ = safe_path(instance_id, '/')
        if not root.is_dir():
            return JSONResponse({'ok': False, 'message': '实例目录不存在'}, status_code=404)
        directory = root / 'backups'
        directory.mkdir(parents=True, exist_ok=True)
        filename = f"backup-{time.strftime('%Y%m%d-%H%M%S')}.tar.gz"
        archive = directory / filename
        # 备份目录不打包自身，避免递归膨胀。
        with tarfile.open(archive, 'w:gz') as output:
            for item in root.iterdir():
                if item.name != 'backups' and not item.is_symlink():
                    output.add(item,arcname=item.name)
        return {'ok': True, 'name': Path(archive).name}
    except (ValueError, OSError) as exc:
        return JSONResponse({'ok': False, 'message': f'备份失败: {exc}'}, status_code=400)
