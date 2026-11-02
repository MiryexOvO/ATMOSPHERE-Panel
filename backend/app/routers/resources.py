from fastapi import APIRouter, Request, Query
from fastapi.responses import JSONResponse
import logging
import httpx
from functools import wraps
from ..core.security import require_user
from ..services.mc_meta_service import McMetaError
from ..services.download_sources import list_resource, resolve, download_candidates

router = APIRouter(prefix='/api/resources', tags=['resources'])
logger = logging.getLogger(__name__)

def resource_errors(handler):
    @wraps(handler)
    async def wrapped(*args, **kwargs):
        try:
            return await handler(*args, **kwargs)
        except (McMetaError, httpx.HTTPError, ValueError, KeyError) as exc:
            logger.warning('资源接口失败: %s', exc, exc_info=True)
            return JSONResponse({'ok': False, 'message': str(exc)}, status_code=502)
    return wrapped

@router.get('/cores')
def core_catalog(request: Request):
    if isinstance((user := require_user(request)), JSONResponse):
        return user
    catalog = {
        'plugin': ['Folia', 'Leaves', 'Paper', 'Purpur', 'Spigot', 'SpongeVanilla'],
        'mod': ['Arclight', 'CatServer', 'Fabric', 'Forge', 'NeoForge', 'Quilt'],
        'proxy': ['BungeeCord', 'Velocity'],
        'bedrock': ['Nukkit', 'PocketMine'],
        'vanilla': ['Vanilla'],
        'hybrid': ['SpongeForge', 'SpongeNeo'],
    }
    categories = [
        {'id': key, 'name': key} for key in catalog
    ]
    cores = [
        {'id': name.lower(), 'name': name, 'category': category}
        for category, names in catalog.items()
        for name in names
    ]
    return {'ok': True, 'categories': categories, 'cores': cores}

@router.get('/cores/{core_id}/versions')
@resource_errors
async def core_versions(request: Request, core_id: str, source: str | None = Query(None)):
    if isinstance((user := require_user(request)), JSONResponse):
        return user
    values = await list_resource(core_id, requested=source)
    logger.info('版本接口响应 core=%s payload=%s', core_id, values)
    return {'ok': True, 'core': core_id, 'versions': values, 'source': source}

@router.get('/cores/{core_id}/versions/{mc_version}/builds')
@resource_errors
async def core_builds(request: Request, core_id: str, mc_version: str, source: str | None = Query(None)):
    if isinstance((user := require_user(request)), JSONResponse):
        return user
    values = await list_resource(core_id, mc_version, source)
    return {'ok': True, 'core': core_id, 'version': mc_version, 'builds': values, 'source': source}

@router.get('/cores/{core_id}/versions/{mc_version}/builds/{build}/download')
@resource_errors
async def core_download(request: Request, core_id: str, mc_version: str, build: str, source: str | None = Query(None)):
    if isinstance((user := require_user(request)), JSONResponse):
        return user
    info = await resolve(core_id,mc_version,build,source) if source and source != 'default' else (await download_candidates(core_id,mc_version,build,source))[0]
    return {'ok':True,**info}
