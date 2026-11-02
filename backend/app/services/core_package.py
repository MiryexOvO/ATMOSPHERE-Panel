import zipfile
import asyncio
import hashlib
import json
import httpx
from pathlib import Path


def is_installer(path: Path) -> bool:
    # 以 JAR 内容判断，不能把安装器当服务端运行。
    try:
        with zipfile.ZipFile(path) as jar:
            manifest = jar.read('META-INF/MANIFEST.MF').decode(errors='replace')
            return 'install_profile.json' in jar.namelist() and 'SimpleInstaller' in manifest
    except (OSError, KeyError, zipfile.BadZipFile):
        return False


async def prepare_libraries(root: Path, installer: Path, report):
    # 用面板网络栈补齐依赖，避免 Java 直连 Maven 超时。
    artifacts = {}
    with zipfile.ZipFile(installer) as jar:
        for name in ('install_profile.json', 'version.json'):
            if name not in jar.namelist(): continue
            for library in json.loads(jar.read(name)).get('libraries', []):
                artifact = library.get('downloads', {}).get('artifact', {})
                if artifact.get('url') and artifact.get('path'): artifacts[artifact['path']] = artifact
    gate = asyncio.Semaphore(4)
    base = (root / 'libraries').resolve()
    async with httpx.AsyncClient(timeout=httpx.Timeout(60,connect=12),follow_redirects=True,headers={'User-Agent':'ATMOSPHERE-PANEL/1.0'}) as client:
        async def fetch(relative, artifact):
            async with gate:
                target = (base / relative).resolve()
                if base not in target.parents: raise ValueError('安装器依赖路径越界')
                expected = artifact.get('sha1')
                if target.is_file() and expected and hashlib.sha1(target.read_bytes()).hexdigest() == expected: return
                urls = [artifact['url'], 'https://bmclapi2.bangbang93.com/maven/' + relative]
                errors = []
                for url in urls:
                    temp = target.with_suffix(target.suffix + '.part')
                    try:
                        target.parent.mkdir(parents=True,exist_ok=True)
                        digest = hashlib.sha1(); size = 0
                        async with client.stream('GET',url) as response:
                            response.raise_for_status()
                            with temp.open('wb') as output:
                                async for chunk in response.aiter_bytes(1024*1024):
                                    size += len(chunk)
                                    if size > 100*1024*1024: raise ValueError('依赖文件超过 100MB')
                                    digest.update(chunk);output.write(chunk)
                        if expected and digest.hexdigest() != expected: raise ValueError('依赖 SHA1 校验失败')
                        temp.replace(target)
                        await report(90, '依赖已准备: ' + target.name)
                        return
                    except (httpx.HTTPError,ValueError) as exc:
                        errors.append(str(exc));temp.unlink(missing_ok=True)
                raise RuntimeError(f'依赖下载失败 {relative}: ' + '; '.join(errors))
        results = await asyncio.gather(*(fetch(relative,artifact) for relative,artifact in artifacts.items()), return_exceptions=True)
        errors = [str(result) for result in results if isinstance(result, Exception)]
        if errors: raise RuntimeError('; '.join(errors[:3]))
