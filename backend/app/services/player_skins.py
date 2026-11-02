"""从授权的 Minecraft 官方接口获取并缓存皮肤头像。"""
import asyncio, base64, json, re, ssl, struct, time
from pathlib import Path
import httpx

locks={}
failures={}
FETCH_LIMIT=asyncio.Semaphore(4)
DEFAULT_HEAD='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 8 8" shape-rendering="crispEdges"><path fill="#b48a64" d="M0 0h8v8H0z"/><path fill="#493629" d="M0 0h8v2H0zM0 2h1v2H0zM7 2h1v2H7z"/><path fill="#d2ad89" d="M1 3h6v3H1z"/><path fill="#eee5d4" d="M1 4h2v1H1zM5 4h2v1H5z"/><path fill="#536a80" d="M2 4h1v1H2zM5 4h1v1H5z"/><path fill="#71503d" d="M2 6h4v2H2z"/></svg>'


async def get_head(root,name):
    directory=root/'.panel'/'player-heads'
    if directory.is_symlink() or (root/'.panel').is_symlink() or root.resolve() not in directory.resolve().parents: return DEFAULT_HEAD
    cache=directory/(name.lower()+'.svg')
    if cache.is_file() and not cache.is_symlink() and time.time()-cache.stat().st_mtime<86400: return cache.read_text(encoding='utf-8')
    if failures.get(name.lower(),0)>time.monotonic(): return DEFAULT_HEAD
    lock=locks.setdefault(str(root)+name.lower(),asyncio.Lock())
    async with lock,FETCH_LIMIT:
        if cache.is_file() and not cache.is_symlink() and time.time()-cache.stat().st_mtime<86400: return cache.read_text(encoding='utf-8')
        try:
            # 仅访问官方身份、会话和纹理域名，拒绝跨域重定向。
            for use_proxy in [True,False]:
                try:
                    async with httpx.AsyncClient(trust_env=use_proxy,verify=ssl.create_default_context(),timeout=10,follow_redirects=False) as client:
                        profile=await client.get('https://api.mojang.com/users/profiles/minecraft/'+name);profile.raise_for_status()
                        uuid=profile.json()['id']
                        if not re.fullmatch(r'[a-fA-F0-9]{32}',uuid): raise ValueError('无效的玩家 UUID')
                        response=await client.get('https://sessionserver.mojang.com/session/minecraft/profile/'+uuid);response.raise_for_status()
                        properties=response.json().get('properties',[])
                        value=next(item['value'] for item in properties if item.get('name')=='textures')
                        texture=json.loads(base64.b64decode(value))['textures']['SKIN']['url']
                        if not re.fullmatch(r'https?://textures\.minecraft\.net/texture/[a-fA-F0-9]+',texture): raise ValueError('非官方皮肤地址')
                        data=bytearray()
                        async with client.stream('GET',texture.replace('http://','https://',1)) as response:
                            response.raise_for_status()
                            async for chunk in response.aiter_bytes(65536):
                                data.extend(chunk)
                                if len(data)>1048576: raise ValueError('皮肤文件过大')
                        break
                except httpx.TransportError:
                    if not use_proxy: raise
            if len(data)<33 or data[:8]!=b'\x89PNG\r\n\x1a\n' or struct.unpack('>II',data[16:24]) not in {(64,32),(64,64)}: raise ValueError('皮肤格式无效')
            encoded=base64.b64encode(data).decode();height=struct.unpack('>I',data[20:24])[0]
            svg=f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="8 8 8 8" style="image-rendering:pixelated"><image width="64" height="{height}" href="data:image/png;base64,{encoded}"/><image x="-32" width="64" height="{height}" href="data:image/png;base64,{encoded}"/></svg>'
            directory.mkdir(parents=True,exist_ok=True)
            if not cache.is_symlink(): cache.write_text(svg,encoding='utf-8')
            return svg
        except (httpx.HTTPError,OSError,ValueError,KeyError,StopIteration):
            failures[name.lower()]=time.monotonic()+300
            return cache.read_text(encoding='utf-8') if cache.is_file() and not cache.is_symlink() else DEFAULT_HEAD
