from __future__ import annotations

import logging
import time
from typing import Any, Literal

import httpx

SourceName = Literal['fastmirror', 'official']
logger = logging.getLogger(__name__)
FAST = 'https://download.fastmirror.net/api/v3'
FILL = 'https://fill.papermc.io/v3'
HEADERS = {'User-Agent': 'ATMOSPHERE-PANEL/1.0 (contact-url)'}
META_TIMEOUT = httpx.Timeout(30.0, connect=10.0)
TTL = 600.0
_cache: dict[str, tuple[float, Any]] = {}


async def resolve_forge_backup(version: str, build: str) -> dict[str, Any]:
    """Resolve the exact selected installer from BMCLAPI without changing builds."""
    base = 'https://bmclapi2.bangbang93.com'
    forge_version = build.removeprefix(f'{version}-')
    async with httpx.AsyncClient(timeout=META_TIMEOUT, headers=HEADERS, follow_redirects=True) as client:
        builds = await _get_json(client, f'{base}/forge/minecraft/{version}')
    item = next((item for item in builds if item.get('version') == forge_version), None)
    installer = next((file for file in (item or {}).get('files', [])
                      if file.get('category') == 'installer' and file.get('format') == 'jar'), None)
    if not installer:
        raise McMetaError(f'BMCLAPI 不存在 Forge {version} {forge_version} 安装器')
    url = httpx.URL(f'{base}/forge/download', params={
        'mcversion': version, 'version': forge_version, 'category': 'installer', 'format': 'jar',
    })
    return {'url': str(url), 'sha1': installer.get('hash'), 'source': 'bmclapi',
            'kind': 'installer', 'version': version, 'build': build}

class McMetaError(RuntimeError):
    pass

class McMetaUnavailableError(McMetaError):
    pass

def _cached(key: str) -> Any | None:
    item = _cache.get(key)
    if item and item[0] > time.monotonic():
        return item[1]
    _cache.pop(key, None)
    return None

def _store(key: str, value: Any) -> Any:
    if value is not None and value != []:
        _cache[key] = (time.monotonic() + TTL, value)
    return value

async def _get_json(client: httpx.AsyncClient, url: str) -> Any:
    try:
        response = await client.get(url)
        response.raise_for_status()
        payload = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise McMetaUnavailableError(f'资源请求失败 {url}: {type(exc).__name__}: {exc}') from exc
    if isinstance(payload, dict) and payload.get('success') is False:
        raise McMetaError(f'镜像返回错误: {payload.get("message", payload)}')
    return payload

async def _fast_core_name(client: httpx.AsyncClient, core: str) -> str:
    payload = _cached('fastmirror:catalog')
    if payload is None:
        payload = _store('fastmirror:catalog', await _get_json(client, f'{FAST}/'))
    entries = payload.get('data') if isinstance(payload, dict) else None
    if not isinstance(entries, list):
        raise McMetaError('FastMirror 根目录缺少核心列表')
    wanted = core.casefold()
    item = next((entry for entry in entries if str(entry.get('name', '')).casefold() == wanted), None)
    if item is None:
        raise McMetaError(f'FastMirror 不存在核心: {core}')
    return str(item['name'])

async def _fast_versions(core: str) -> list[dict[str, Any]]:
    async with httpx.AsyncClient(timeout=META_TIMEOUT, headers=HEADERS, follow_redirects=True) as client:
        real_core = await _fast_core_name(client, core)
        payload = await _get_json(client, f'{FAST}/{real_core}')
    data = payload.get('data') if isinstance(payload, dict) else None
    values = data.get('mc_versions') if isinstance(data, dict) else None
    if not isinstance(values, list):
        raise McMetaError(f'FastMirror 未返回 {real_core} 游戏版本列表')
    unique = list(dict.fromkeys(str(v) for v in values))
    logger.info('版本响应 core=%s count=%s', core, len(unique))
    return [{'id': value, 'stable': True, 'source': 'fastmirror'} for value in unique]

async def _official_versions(core: str) -> list[dict[str, Any]]:
    if core == 'paper':
        async with httpx.AsyncClient(timeout=META_TIMEOUT, headers=HEADERS, follow_redirects=True) as client:
            payload = await _get_json(client, f'{FILL}/projects/paper')
        values = payload.get('versions') if isinstance(payload, dict) else None
        if isinstance(values, dict):
            values = [version for group in values.values() for version in group]
        if not isinstance(values, list):
            raise McMetaError('Fill v3 未返回 Paper 版本列表')
        return [{'id': str(v), 'stable': True, 'source': 'official'} for v in values]
    raise McMetaError(f'暂无 {core} 官方版本适配器')

async def list_versions(core: str, source: SourceName = 'fastmirror') -> list[dict[str, Any]]:
    key = f'{source}:{core}:versions'
    cached = _cached(key)
    if cached is not None:
        return cached
    if source == 'official':
        return _store(key, await _official_versions(core))
    try:
        return _store(key, await _fast_versions(core))
    except McMetaError:
        logger.error('FastMirror 版本失败 core=%s', core, exc_info=True)
        if core != 'paper':
            raise
        return _store(key, await _official_versions(core))

async def _fast_builds(core: str, version: str) -> list[dict[str, Any]]:
    async with httpx.AsyncClient(timeout=META_TIMEOUT, headers=HEADERS, follow_redirects=True) as client:
        real_core = await _fast_core_name(client, core)
        payload = await _get_json(client, f'{FAST}/{real_core}/{version}?limit=100')
    data = payload.get('data') if isinstance(payload, dict) else None
    builds = data.get('builds') if isinstance(data, dict) else None
    if not isinstance(builds, list):
        raise McMetaError(f'FastMirror 未返回 {real_core} {version} 构建列表')
    return [{'id': str(item.get('core_version')), 'version': version, 'source': 'fastmirror'} for item in builds if isinstance(item, dict) and item.get('core_version')]

async def _official_builds(core: str, version: str) -> list[dict[str, Any]]:
    if core != 'paper':
        raise McMetaError(f'暂无 {core} 官方构建适配器')
    async with httpx.AsyncClient(timeout=META_TIMEOUT, headers=HEADERS, follow_redirects=True) as client:
        payload = await _get_json(client, f'{FILL}/projects/paper/versions/{version}/builds?channel=STABLE')
    if not isinstance(payload, list):
        raise McMetaError('Fill v3 未返回 Paper 构建列表')
    return [{'id': str(item.get('id')), 'version': version, 'source': 'official'} for item in payload if isinstance(item, dict)]

async def list_builds(core: str, version: str, source: SourceName = 'fastmirror') -> list[dict[str, Any]]:
    key = f'{source}:{core}:versions:{version}:builds'
    cached = _cached(key)
    if cached is not None:
        return cached
    if source == 'official':
        return _store(key, await _official_builds(core, version))
    try:
        return _store(key, await _fast_builds(core, version))
    except McMetaError:
        logger.error('FastMirror 构建失败 core=%s version=%s', core, version, exc_info=True)
        if core != 'paper':
            raise
        return _store(key, await _official_builds(core, version))

async def resolve_download(core: str, version: str, build: str, source: SourceName = 'fastmirror') -> dict[str, Any]:
    if source == 'official' and core == 'paper':
        async with httpx.AsyncClient(timeout=META_TIMEOUT, headers=HEADERS, follow_redirects=True) as client:
            builds = await _get_json(client, f'{FILL}/projects/paper/versions/{version}/builds?channel=STABLE')
        item = next((x for x in builds if str(x.get('id')) == str(build)), None)
        url = ((item or {}).get('downloads') or {}).get('server:default', {}).get('url')
        if not url:
            raise McMetaError('官方构建缺少下载地址')
        download = item['downloads']['server:default']
        return {'url': url, 'filename': download.get('name') or url.rsplit('/', 1)[-1], 'sha256': download.get('checksums', {}).get('sha256'), 'kind': 'server', 'source': 'official', 'version': version, 'build': build}
    async with httpx.AsyncClient(timeout=META_TIMEOUT, headers=HEADERS, follow_redirects=True) as client:
        real_core = await _fast_core_name(client, core)
        payload = await _get_json(client, f'{FAST}/{real_core}/{version}/{build}')
    data = payload.get('data') if isinstance(payload, dict) else None
    url = data.get('download_url') if isinstance(data, dict) else None
    if not url:
        raise McMetaError('镜像构建缺少 data.download_url')
    return {'url': url, 'filename': data.get('filename') or url.rsplit('/', 1)[-1], 'sha1': data.get('sha1'), 'kind': 'installer' if core in {'forge', 'neoforge'} else 'server', 'source': 'fastmirror', 'version': version, 'build': build}
