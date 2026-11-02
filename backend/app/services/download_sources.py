"""明确来源的元数据适配与同构建测速。"""
import asyncio
import re
import time
import xml.etree.ElementTree as ET
import httpx
from . import mc_meta_service as meta
from .panel_settings import read_settings

FILL_PROJECTS = {'paper', 'folia', 'velocity', 'waterfall'}
POLARS = 'https://mirror.polars.cc/api/query/minecraft/core'


async def json_at(url):
    cached = meta._cached('source:' + url)
    if cached is not None: return cached
    async with httpx.AsyncClient(timeout=meta.META_TIMEOUT, headers=meta.HEADERS, follow_redirects=True) as client:
        result = await meta._get_json(client, url)
    return meta._store('source:' + url, result)


async def polars_files(core):
    catalog = await json_at(POLARS)
    entry = next((item for item in catalog if item['name'].casefold() == core.casefold() or (core == 'vanilla' and '官方' in item['name'])), None)
    if not entry: raise meta.McMetaError(f'Polars 未提供 {core}')
    files = await json_at(f'{POLARS}/{entry["id"]}')
    if not isinstance(files, list): raise meta.McMetaError('Polars 文件列表无效')
    return files


def polars_version(item):
    match = re.search(r'(?<!\d)(1\.\d+(?:\.\d+)?)(?!\d)', item['name'])
    return match[1] if match else None


async def official_data(core):
    if core in FILL_PROJECTS: return await json_at(f'{meta.FILL}/projects/{core}')
    if core == 'forge': return await json_at('https://files.minecraftforge.net/net/minecraftforge/forge/maven-metadata.json')
    if core == 'vanilla': return await json_at('https://piston-meta.mojang.com/mc/game/version_manifest_v2.json')
    if core == 'purpur': return await json_at('https://api.purpurmc.org/v2/purpur')
    if core == 'fabric': return await json_at('https://meta.fabricmc.net/v2/versions/game')
    if core == 'neoforge':
        key = 'source:neoforge-xml'
        if (cached := meta._cached(key)) is not None: return cached
        async with httpx.AsyncClient(timeout=meta.META_TIMEOUT, headers=meta.HEADERS, follow_redirects=True) as client:
            response = await client.get('https://maven.neoforged.net/releases/net/neoforged/neoforge/maven-metadata.xml')
            response.raise_for_status()
        return meta._store(key, [node.text for node in ET.fromstring(response.content).findall('./versioning/versions/version')])
    raise meta.McMetaError(f'尚无 {core} 官方适配器，请选择其他来源')


def neo_game(build):
    parts = build.split('.')
    if len(parts) < 2: return ''
    return f'1.{parts[0]}.{parts[1]}' if int(parts[0]) < 26 else '.'.join(parts[:-1])


async def versions(core, source):
    if source == 'fastmirror': return await meta._fast_versions(core)
    if source == 'polars': values = list(dict.fromkeys(filter(None, (polars_version(item) for item in await polars_files(core)))))
    else:
        data = await official_data(core)
        if core in FILL_PROJECTS:
            groups = data['versions']; values = [v for group in groups.values() for v in group] if isinstance(groups, dict) else groups
        elif core == 'forge': values = list(data.keys())
        elif core == 'neoforge': values = list(dict.fromkeys(neo_game(build) for build in reversed(data)))
        elif core == 'vanilla': values = [item['id'] for item in data['versions'] if item['type'] == 'release']
        elif core == 'fabric': values = [item['version'] for item in data if item.get('stable')]
        else: values = list(reversed(data['versions']))
    if not values: raise meta.McMetaError(f'{source} 未提供 {core} 版本')
    return [{'id': value, 'stable': True, 'source': source} for value in values]


async def builds(core, version, source):
    if source == 'fastmirror': return await meta._fast_builds(core, version)
    if source == 'polars': values = ['polars-' + str(item['id']) for item in await polars_files(core) if polars_version(item) == version]
    elif core in FILL_PROJECTS:
        data = await json_at(f'{meta.FILL}/projects/{core}/versions/{version}/builds')
        values = [str(item['id']) for item in data if item.get('channel') == 'STABLE']
    elif core == 'forge': values = list(reversed((await official_data(core)).get(version, [])))
    elif core == 'neoforge': values = [build for build in reversed(await official_data(core)) if neo_game(build) == version]
    elif core == 'vanilla': values = ['release'] if version in [item['id'] for item in (await official_data(core))['versions']] else []
    elif core == 'purpur': values = list(reversed((await json_at(f'https://api.purpurmc.org/v2/purpur/{version}'))['builds']['all']))
    elif core == 'fabric':
        installer = (await json_at('https://meta.fabricmc.net/v2/versions/installer'))[0]['version']
        values = [item['loader']['version'] + '+' + installer for item in await json_at(f'https://meta.fabricmc.net/v2/versions/loader/{version}')]
    else: raise meta.McMetaError(f'{source} 未提供 {core} 构建')
    if not values: raise meta.McMetaError(f'{source} 未提供 {core} {version} 构建')
    return [{'id': str(value), 'version': version, 'source': source} for value in values]


async def resolve(core, version, build, source):
    info = {'source': source, 'version': version, 'build': build}
    if source == 'fastmirror':
        if core in FILL_PROJECTS and build.isdigit(): build = 'build' + build
        if core == 'fabric': build = build.replace('+', '-')
        return await meta.resolve_download(core, version, build, 'fastmirror')
    if source == 'polars':
        item = next((item for item in await polars_files(core) if 'polars-' + str(item['id']) == build and polars_version(item) == version), None)
        if not item: raise meta.McMetaError('Polars 未提供所选精确构建；请从此来源重新选择版本和构建')
        url = item['downloadUrl']
        if url.startswith('http://cdn.polars.cc/'): url = url.replace('http:', 'https:', 1)
        return {**info, 'url': url, 'filename': item['name']}
    if core in FILL_PROJECTS:
        data = await json_at(f'{meta.FILL}/projects/{core}/versions/{version}/builds')
        item = next((item for item in data if str(item['id']) == build.removeprefix('build') and item.get('channel') == 'STABLE'), None)
        if not item: raise meta.McMetaError('官方没有所选稳定构建')
        file = item['downloads']['server:default']
        return {**info,'url':file['url'],'sha256':file.get('checksums',{}).get('sha256')}
    if core == 'forge':
        full = build if build.startswith(version + '-') else version + '-' + build
        if full not in (await official_data(core)).get(version, []): raise meta.McMetaError('官方没有所选 Forge 构建')
        return {**info,'url':f'https://maven.minecraftforge.net/net/minecraftforge/forge/{full}/forge-{full}-installer.jar'}
    if core == 'neoforge':
        if build not in await official_data(core) or neo_game(build) != version: raise meta.McMetaError('官方没有所选 NeoForge 构建')
        return {**info,'url':f'https://maven.neoforged.net/releases/net/neoforged/neoforge/{build}/neoforge-{build}-installer.jar'}
    if core == 'vanilla':
        entry = next((item for item in (await official_data(core))['versions'] if item['id'] == version), None)
        if not entry: raise meta.McMetaError('官方没有所选 Minecraft 版本')
        file = (await json_at(entry['url']))['downloads']['server']
        return {**info,'url':file['url'],'sha1':file['sha1']}
    if core == 'purpur':
        build = build.removeprefix('build')
        if not build.isdigit(): raise meta.McMetaError('请从 Purpur 官方列表选择精确构建')
        return {**info,'url':f'https://api.purpurmc.org/v2/purpur/{version}/{build}/download'}
    if core == 'fabric':
        separator = '+' if '+' in build else '-'
        loader, installer = build.split(separator)
        return {**info,'url':f'https://meta.fabricmc.net/v2/versions/loader/{version}/{loader}/{installer}/server/jar'}
    raise meta.McMetaError(f'尚无 {core} 官方下载适配器')


async def list_resource(core, version=None, requested=None):
    source = requested or read_settings()['download_source']
    if source not in {'default','fastmirror','official','polars'}: raise meta.McMetaError('无效下载来源')
    providers = ['fastmirror','official','polars'] if source == 'default' else [source]
    errors=[]
    for provider in providers:
        try:
            result = await (builds(core,version,provider) if version else versions(core,provider))
            if result: return result
        except (meta.McMetaError,httpx.HTTPError,ValueError,KeyError) as exc: errors.append(f'{provider}: {exc}')
    raise meta.McMetaUnavailableError('; '.join(errors))


async def download_candidates(core, version, build, origin):
    policy = read_settings()['download_source']
    providers = ['fastmirror','official','polars'] if policy == 'default' else [policy]
    # Polars 的文件 ID 不等于其他站的构建号，禁止静默换包。
    if policy == 'default' and build.startswith('polars-'): providers=['polars']
    results=await asyncio.gather(*(resolve(core,version,build,p) for p in providers),return_exceptions=True)
    candidates=[result for result in results if isinstance(result,dict)]
    if not candidates: raise meta.McMetaUnavailableError('; '.join(str(result) for result in results))
    if policy != 'default': return candidates
    async def probe(info):
        started=time.monotonic()
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(12,connect=5),headers=meta.HEADERS,follow_redirects=True) as client:
                async with client.stream('GET',info['url'],headers={'Range':'bytes=0-65535'}) as response:
                    response.raise_for_status()
                    async for chunk in response.aiter_bytes(65536):
                        if chunk: return (time.monotonic()-started)/len(chunk),info
        except httpx.HTTPError: pass
        return float('inf'),info
    # 只读取小段流量并行测速，不重复下载整个核心。
    ranked=await asyncio.gather(*(probe(info) for info in candidates))
    return [info for _,info in sorted(ranked,key=lambda item:item[0])]
