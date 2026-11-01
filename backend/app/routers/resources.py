from fastapi import APIRouter, Request, Query
from fastapi.responses import JSONResponse
import logging
from ..core.security import require_user
from ..services.mc_meta_service import list_versions, list_builds, resolve_download

router = APIRouter(prefix='/api/resources', tags=['resources'])
logger = logging.getLogger(__name__)

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
async def core_versions(request: Request, core_id: str, source: str = Query('fastmirror')):
    if isinstance((user := require_user(request)), JSONResponse):
        return user
    values = await list_versions(core_id, source if source in {'fastmirror', 'official'} else 'fastmirror')
    logger.info('版本接口响应 core=%s payload=%s', core_id, values)
    return {'ok': True, 'core': core_id, 'versions': values, 'source': source}

@router.get('/cores/{core_id}/versions/{mc_version}/builds')
async def core_builds(request: Request, core_id: str, mc_version: str, source: str = Query('fastmirror')):
    if isinstance((user := require_user(request)), JSONResponse):
        return user
    values = await list_builds(core_id, mc_version, source if source in {'fastmirror', 'official'} else 'fastmirror')
    return {'ok': True, 'core': core_id, 'version': mc_version, 'builds': values, 'source': source}

@router.get('/cores/{core_id}/versions/{mc_version}/builds/{build}/download')
async def core_download(request: Request, core_id: str, mc_version: str, build: str, source: str = Query('fastmirror')):
    if isinstance((user := require_user(request)), JSONResponse):
        return user
    return {'ok': True, **await resolve_download(core_id, mc_version, build, source if source in {'fastmirror', 'official'} else 'fastmirror')}
