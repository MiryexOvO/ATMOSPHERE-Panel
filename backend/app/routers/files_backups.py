from fastapi import APIRouter, Request, Query
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from ..core.security import require_user
from ..core.config import SERVER_ROOT
from pathlib import Path
import shutil, time
router=APIRouter(prefix='/api/instances',tags=['files-backups'])

def safe_path(instance_id:str, requested:str)->tuple[Path,Path]:
    if not instance_id or '/' in instance_id or '..' in instance_id: raise ValueError('实例 ID 无效')
    root=(SERVER_ROOT/instance_id).resolve(); target=(root/requested.lstrip('/')).resolve()
    if target!=root and root not in target.parents: raise ValueError('路径超出实例目录')
    return root,target

class PropertiesPayload(BaseModel):
    properties: dict[str, object]


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
        if not directory.is_dir(): return JSONResponse({'ok':False,'message':'目录不存在'},status_code=404)
        entries=[]
        for item in sorted(directory.iterdir(),key=lambda p:(not p.is_dir(),p.name.lower())):
            entries.append({'name':item.name,'path':'/'+str(item.relative_to(root)).replace('\\','/'),'type':'directory' if item.is_dir() else 'file','size':item.stat().st_size if item.is_file() else None})
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
        archive = shutil.make_archive(str(directory / filename[:-7]), 'gztar', root=str(root), base_dir='.', logger=None)
        return {'ok': True, 'name': Path(archive).name}
    except (ValueError, OSError) as exc:
        return JSONResponse({'ok': False, 'message': f'备份失败: {exc}'}, status_code=400)
