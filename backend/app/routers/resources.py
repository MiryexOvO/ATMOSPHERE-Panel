from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from ..core.security import require_user

router = APIRouter(prefix='/api/resources', tags=['resources'])

CORE_CATALOG = [
    {'id': 'paper', 'name': 'Paper', 'category': 'plugin', 'description': '高性能 Spigot 分支', 'versions': ['1.21.4', '1.21.1', '1.20.6', '1.20.4']},
    {'id': 'purpur', 'name': 'Purpur', 'category': 'plugin', 'description': 'Paper 兼容增强核心', 'versions': ['1.21.1', '1.20.4']},
    {'id': 'fabric', 'name': 'Fabric', 'category': 'mod', 'description': '轻量现代模组加载器', 'versions': ['1.21.1', '1.20.4']},
    {'id': 'forge', 'name': 'Forge', 'category': 'mod', 'description': '传统大型模组生态', 'versions': ['1.21.1', '1.20.1']},
    {'id': 'vanilla', 'name': 'Vanilla', 'category': 'vanilla', 'description': '官方原版核心', 'versions': ['1.21.4', '1.20.4']},
    {'id': 'velocity', 'name': 'Velocity', 'category': 'proxy', 'description': '现代代理服务端', 'versions': ['3.4.0', '3.3.0']},
]

@router.get('/cores')
def core_catalog(request: Request):
    if isinstance((user := require_user(request)), JSONResponse): return user
    categories = [{'id': 'plugin', 'name': '插件服务端'}, {'id': 'mod', 'name': '模组服务端'}, {'id': 'vanilla', 'name': '原版服务端'}, {'id': 'proxy', 'name': '代理服务端'}]
    return {'ok': True, 'categories': categories, 'cores': CORE_CATALOG}

@router.get('/cores/{core_id}/versions')
def core_versions(request: Request, core_id: str):
    if isinstance((user := require_user(request)), JSONResponse): return user
    item = next((item for item in CORE_CATALOG if item['id'] == core_id), None)
    if not item: return JSONResponse({'ok': False, 'message': '核心不存在'}, status_code=404)
    return {'ok': True, 'core': core_id, 'versions': item['versions'], 'source': 'catalog'}
