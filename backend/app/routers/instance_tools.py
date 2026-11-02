"""玩家、扩展组件与实例文件导出。"""
import asyncio, json, os, re, struct, tempfile, tomllib, zipfile, zlib
from pathlib import Path
from contextlib import closing
from fastapi import APIRouter, Request, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, FileResponse, Response
from starlette.background import BackgroundTask
from pydantic import BaseModel, Field
from ..core.database import connect
from ..core.security import require_user
from ..infra.process_manager import get_process_manager
from ..services.operations import send_command
from ..services.panel_settings import audit
from .files_backups import safe_path

router = APIRouter(prefix='/api/instances',tags=['instance-tools'])


@router.get('/{instance_id}/players/avatar/{name}')
async def player_avatar(request:Request,instance_id:str,name:str):
    if isinstance(user:=require_user(request),JSONResponse): return user
    if not re.fullmatch(r'[A-Za-z0-9_]{1,16}',name): raise HTTPException(422,'玩家名称无效')
    root=root_for(instance_id)
    from ..services.player_skins import get_head
    svg=await get_head(root,name)
    return Response(svg,media_type='image/svg+xml',headers={'Cache-Control':'private,max-age=3600','Content-Security-Policy':"default-src 'none'; img-src data:; style-src 'unsafe-inline'; sandbox"})


def root_for(instance_id):
    root, _ = safe_path(instance_id,'')
    with closing(connect()) as conn:
        if not conn.execute('SELECT 1 FROM instances WHERE id=?',(instance_id,)).fetchone():
            raise HTTPException(404,'实例不存在')
    return root


def inspect_addons(root, kind):
    folder = root / kind
    items = []
    if folder.is_dir() and not folder.is_symlink() and root.resolve() in folder.resolve().parents:
        for path in sorted(folder.iterdir()):
            if not (path.name.endswith('.jar') or path.name.endswith('.jar.disabled')) or path.is_symlink(): continue
            item = {'file':path.name,'name':path.name.removesuffix('.disabled').removesuffix('.jar'),'version':'','enabled':not path.name.endswith('.disabled'),'client_only':False,'description':''}
            try:
                # 只依据明确的模组环境标记自动禁用。
                with zipfile.ZipFile(path) as jar:
                    def read(name):
                        info=jar.getinfo(name)
                        if info.file_size>1048576: raise ValueError('元数据过大')
                        return jar.read(name).decode('utf-8')
                    if 'fabric.mod.json' in jar.namelist():
                        data=json.loads(read('fabric.mod.json'));item.update(name=data.get('name') or data.get('id') or item['name'],version=str(data.get('version','')),client_only=data.get('environment')=='client')
                    elif 'quilt.mod.json' in jar.namelist():
                        data=json.loads(read('quilt.mod.json'));loader=data.get('quilt_loader',{});meta=loader.get('metadata',{});item.update(name=meta.get('name') or loader.get('id') or item['name'],version=str(loader.get('version','')),client_only=data.get('minecraft',{}).get('environment')=='client')
                    elif kind=='mods':
                        name=next((n for n in ['META-INF/neoforge.mods.toml','META-INF/mods.toml'] if n in jar.namelist()),None)
                        if name:
                            mod=tomllib.loads(read(name)).get('mods',[{}])[0];item.update(name=mod.get('displayName') or mod.get('modId') or item['name'],version=str(mod.get('version','')))
                    else:
                        name=next((n for n in ['paper-plugin.yml','plugin.yml'] if n in jar.namelist()),None)
                        if name:
                            data=dict(re.findall(r'^(name|version):\s*[\"\']?([^\r\n\"\']+)',read(name),re.M));item.update(name=data.get('name',item['name']),version=data.get('version',''))
            except (OSError,ValueError,KeyError,zipfile.BadZipFile,tomllib.TOMLDecodeError) as exc: item['description']=str(exc)
            items.append(item)
    return items


@router.get('/{instance_id}/addons/{kind}')
async def addons(request:Request,instance_id:str,kind:str):
    if isinstance(user:=require_user(request),JSONResponse): return user
    if kind not in {'mods','plugins'}: raise HTTPException(404)
    root=root_for(instance_id)
    items=await asyncio.to_thread(inspect_addons,root,kind)
    # 核心能力不能仅从空插件目录推断。
    with closing(connect()) as conn:
        row=conn.execute('SELECT jar_name,selected_core FROM instances WHERE id=?',(instance_id,)).fetchone()
    marker=' '.join(str(v or '') for v in row).lower()
    for log in [root/'logs/latest.log',root/'panel-console.log']:
        if log.is_file():
            with log.open('rb') as stream:
                stream.seek(max(0,log.stat().st_size-131072));marker+=' '+stream.read().decode(errors='ignore').lower()
    supported=any(word in marker for word in ['paper','purpur','spigot','bukkit','folia','arclight','mohist','catserver'])
    return {'items':items,'supported':supported if kind=='plugins' else True,'running':await get_process_manager().is_running(instance_id)}


class AddonAction(BaseModel):
    file:str = Field(default='',max_length=255)
    enabled:bool = True
    auto_client:bool = False


@router.post('/{instance_id}/addons/{kind}')
async def toggle_addon(request:Request,instance_id:str,kind:str,payload:AddonAction):
    if isinstance(user:=require_user(request),JSONResponse): return user
    if kind not in {'mods','plugins'}: raise HTTPException(404)
    root=root_for(instance_id)
    if await get_process_manager().is_running(instance_id): raise HTTPException(409,'请先停止实例')
    changes=[]
    items=await asyncio.to_thread(inspect_addons,root,kind)
    for item in items:
        if payload.auto_client:
            if kind!='mods' or not item['client_only'] or not item['enabled']: continue
            enabled=False
        else:
            if item['file']!=payload.file: continue
            enabled=payload.enabled
        source=root/kind/item['file'];target=source.with_name(source.name.removesuffix('.disabled') if enabled else source.name.removesuffix('.disabled')+'.disabled')
        _,source=safe_path(instance_id,str(source.relative_to(root)));_,target=safe_path(instance_id,str(target.relative_to(root)))
        if source!=target:
            if target.exists(): raise HTTPException(409,'目标文件已存在')
            source.rename(target);changes.append(item['file'])
    if not payload.auto_client and not any(i['file']==payload.file for i in items): raise HTTPException(404,'组件不存在')
    audit(user['id'],'addon.toggle',json.dumps({'instance':instance_id,'files':changes}));return {'ok':True,'changed':changes}


class PlayerAction(BaseModel):
    name:str = Field(pattern=r'^[A-Za-z0-9_]{1,16}$')
    action:str = Field(pattern='^(op|deop|kick|ban|pardon|whitelist-add|whitelist-remove)$')


@router.post('/{instance_id}/players/action')
async def player_action(request:Request,instance_id:str,payload:PlayerAction):
    if isinstance(user:=require_user(request),JSONResponse): return user
    root_for(instance_id)
    command=payload.action.replace('-',' ')+' '+payload.name
    try: output=await send_command(instance_id,command)
    except (OSError,RuntimeError,ValueError) as exc: raise HTTPException(409,str(exc))
    audit(user['id'],'player.'+payload.action,instance_id+':'+payload.name)
    return {'ok':True,'output':output}


@router.get('/{instance_id}/icon')
def get_icon(request:Request,instance_id:str):
    if isinstance(user:=require_user(request),JSONResponse): return user
    path=root_for(instance_id)/'server-icon.png'
    if not path.is_file(): raise HTTPException(404,'尚未设置图标')
    return FileResponse(path,media_type='image/png')


@router.post('/{instance_id}/icon')
async def upload_icon(request:Request,instance_id:str,file:UploadFile=File(...)):
    if isinstance(user:=require_user(request),JSONResponse): return user
    root=root_for(instance_id)
    if await get_process_manager().is_running(instance_id): raise HTTPException(409,'请先停止实例')
    data=await file.read(65537)
    # 验证 PNG 尺寸和数据校验和，拒绝伪装文件。
    if len(data)<33 or len(data)>65536 or data[:8]!=b'\x89PNG\r\n\x1a\n' or data[12:16]!=b'IHDR' or struct.unpack('>II',data[16:24])!=(64,64): raise HTTPException(422,'需要裁剪后的 64×64 PNG')
    offset=8;ended=False
    while offset+12<=len(data):
        size=struct.unpack('>I',data[offset:offset+4])[0];end=offset+8+size
        if end+4>len(data) or zlib.crc32(data[offset+4:end]) & 0xffffffff != struct.unpack('>I',data[end:end+4])[0]: raise HTTPException(422,'PNG 校验失败')
        if data[offset+4:offset+8]==b'IEND': ended=True;break
        offset=end+4
    if not ended: raise HTTPException(422,'PNG 不完整')
    temporary=root/'.server-icon.tmp';temporary.write_bytes(data);os.replace(temporary,root/'server-icon.png')
    audit(user['id'],'instance.icon',instance_id);return {'ok':True}


@router.get('/{instance_id}/export')
async def export(request:Request,instance_id:str):
    if isinstance(user:=require_user(request),JSONResponse): return user
    root=root_for(instance_id)
    if await get_process_manager().is_running(instance_id): raise HTTPException(409,'请先停止实例，确保世界存档一致')
    handle,name=tempfile.mkstemp(suffix='.zip');os.close(handle)
    path=Path(name)
    def pack():
        with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=1,allowZip64=True) as archive:
            for directory,folders,files in os.walk(root,followlinks=False):
                folders[:]=[folder for folder in folders if not (Path(directory)/folder).is_symlink() and folder not in {'.runtime-tmp','.install-tmp'}]
                for filename in files:
                    file=Path(directory)/filename
                    if file.is_symlink() or file.name.endswith('.lock'): continue
                    if root not in file.resolve().parents: continue
                    archive.write(file,file.relative_to(root))
    try: await asyncio.to_thread(pack)
    except OSError as exc:
        path.unlink(missing_ok=True);raise HTTPException(507,'导出失败，请检查磁盘空间和文件访问权限：'+str(exc))
    except BaseException: path.unlink(missing_ok=True);raise
    audit(user['id'],'instance.export',instance_id)
    return FileResponse(path,filename=instance_id+'-server.zip',background=BackgroundTask(path.unlink,missing_ok=True))
