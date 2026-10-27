from fastapi import APIRouter, Request, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from ..core.security import require_user
from ..core.database import connect
from ..core.config import SERVER_ROOT, ROOT, MAX_PACKAGE_BYTES
from ..archive_service import extract_archive, find_core_candidates
from pathlib import Path
import secrets, shutil, time

router = APIRouter(prefix='/api', tags=['deployments'])

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
        (root / 'server.properties').write_text(f'server-port={payload.port}\n', encoding='utf-8')
        selected = 'start_mcdr.py' if payload.mode == 'mcdr' else 'server.jar'
        if payload.mode == 'quick':
            raise ValueError('快速部署尚未连接核心下载器，请使用上传整合包或配置下载源')
        if payload.mode == 'mcdr':
            (root / selected).write_text('from mcdreforged.api.all import ServerInterface\n', encoding='utf-8')
        conn.execute('INSERT INTO instances VALUES(?,?,?,?,?,?,?,?)', (instance_id, instance_id, payload.port, selected, 'stopped', int(time.time()), '[]', selected))
        conn.commit()
        return {'ok': True, 'mode': payload.mode, 'instance': {'id': instance_id}, 'status': 'stopped'}
    except Exception as exc:
        shutil.rmtree(root, ignore_errors=True)
        conn.rollback()
        return JSONResponse({'ok': False, 'message': f'部署失败: {exc}'}, status_code=502)
    finally:
        conn.close()

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