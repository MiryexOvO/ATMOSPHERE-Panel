"""原生基岩版与独立 MCDR 运行环境。"""
import asyncio, json, os, platform, re, ssl, sys, time
from pathlib import Path
import httpx
from ..archive_service import extract_archive


async def bedrock_catalog():
    # 只解析 Mojang 实际发布的链接，不拼接历史版本地址。
    system=platform.system()
    supported=system in {'Windows','Linux'} and platform.machine().lower() in {'amd64','x86_64'}
    if not supported: return {'supported':False,'message':'官方 BDS 仅提供 Windows / Ubuntu x86_64 版本','versions':[]}
    wanted='serverBedrockWindows' if system=='Windows' else 'serverBedrockLinux'
    for proxy in [True,False]:
        try:
            async with httpx.AsyncClient(trust_env=proxy,verify=ssl.create_default_context(),timeout=20) as client:
                response=await client.get('https://net-secondary.web.minecraft-services.net/api/v1.0/download/links');response.raise_for_status()
                versions=[]
                for link in response.json()['result']['links']:
                    if link['downloadType']!=wanted: continue
                    url=link['downloadUrl']
                    match=re.fullmatch(r'https://www\.minecraft\.net/bedrockdedicatedserver/bin-(?:win|linux)/bedrock-server-([\d.]+)\.zip',url)
                    if match: versions.append({'id':match[1],'label':match[1]+' · OFFICIAL','url':url})
                if not versions: raise RuntimeError('官方接口没有返回适用于本机的正式版')
                return {'supported':True,'platform':system,'versions':versions}
        except httpx.TransportError:
            if not proxy: raise


async def prepare_bedrock(root,version,report):
    catalog=await bedrock_catalog()
    selected=next((item for item in catalog['versions'] if item['id']==version),None)
    if not selected: raise ValueError(catalog.get('message') or '所选基岩版已不在官方发布目录，请刷新版本')
    archive=root/'bedrock.zip'
    # 下载完整 ZIP 后校验解压；实例尚未对外发布。
    async with httpx.AsyncClient(trust_env=False,verify=ssl.create_default_context(),follow_redirects=True,timeout=httpx.Timeout(20,read=90),headers={'User-Agent':'Mozilla/5.0 ATMOSPHERE-Panel'}) as client:
        await download_bedrock(client,selected['url'],archive,report)
    await report(84,'正在校验并解压基岩版服务端…')
    await asyncio.to_thread(extract_archive,archive,root)
    archive.unlink()
    name='bedrock_server.exe' if os.name=='nt' else 'bedrock_server'
    binary=root/name
    if not binary.is_file(): raise RuntimeError('官方压缩包缺少 BDS 可执行文件')
    if os.name!='nt': binary.chmod(0o750)
    (root/'.atmosphere-runtime.json').write_text(json.dumps({'mode':'bedrock','version':version}),encoding='utf-8')
    return name


async def download_bedrock(client,url,archive,report):
    # 官方支持 Range 时并行八段；每段核验 Content-Range 和实际长度。
    async with client.stream('GET',url,headers={'Range':'bytes=0-0'}) as probe:
        probe.raise_for_status()
        match=re.fullmatch(r'bytes 0-0/(\d+)',probe.headers.get('content-range','')) if probe.status_code==206 else None
        total=int(match[1]) if match else 0
    if total>1024**3: raise ValueError('BDS 压缩包超过 1 GB 限制')
    received=0;last_report=0
    async def update(size):
        nonlocal received,last_report
        received+=size
        if received>1024**3: raise ValueError('BDS 压缩包超过大小限制')
        if time.monotonic()-last_report>.5:
            last_report=time.monotonic()
            await report(min(80,20+int(received/total*60)) if total else 20,f'正在下载官方 BDS · {received/1048576:.1f} MB')
    if total>=8*1048576:
        with archive.open('wb') as output: output.truncate(total)
        async def part(index):
            start=total*index//8;end=total*(index+1)//8-1;size=0
            async with client.stream('GET',url,headers={'Range':f'bytes={start}-{end}'}) as response:
                if response.status_code!=206 or response.headers.get('content-range')!=f'bytes {start}-{end}/{total}': raise RuntimeError('BDS 下载分段响应不匹配')
                with archive.open('r+b') as output:
                    output.seek(start)
                    async for chunk in response.aiter_bytes(262144):
                        size+=len(chunk)
                        if size>end-start+1: raise RuntimeError('BDS 分段超出范围')
                        output.write(chunk);await update(len(chunk))
                if size!=end-start+1: raise RuntimeError('BDS 分段下载不完整')
        results=await asyncio.gather(*(part(i) for i in range(8)),return_exceptions=True)
        error=next((result for result in results if isinstance(result,BaseException)),None)
        if error: raise error
    else:
        async with client.stream('GET',url) as response:
            response.raise_for_status()
            with archive.open('wb') as output:
                async for chunk in response.aiter_bytes(262144): output.write(chunk);await update(len(chunk))
    if total and received!=total: raise RuntimeError('BDS 下载大小不匹配')


async def prepare_mcdr(root,report,core='paper'):
    await report(85,'正在创建实例专用 Python 环境并安装 MCDR…')
    async def run(*args,timeout=600,environment=None):
        process=await asyncio.create_subprocess_exec(*map(str,args),env=environment,cwd=root,stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.STDOUT)
        try: output,_=await asyncio.wait_for(process.communicate(),timeout)
        except (TimeoutError,asyncio.CancelledError): process.kill();await process.wait();raise
        with (root/'panel-install.log').open('ab') as log: log.write(output)
        if process.returncode: raise RuntimeError('MCDR 环境准备失败，请查看 panel-install.log：'+output.decode(errors='replace')[-500:])
    await run(sys.executable,'-m','venv',root/'.mcdr-venv')
    python=root/'.mcdr-venv'/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
    pip_args=[python,'-m','pip','install','--disable-pip-version-check','--retries','1','--timeout','20','mcdreforged>=2.13,<3']
    try: await run(*pip_args)
    except RuntimeError:
        await report(85,'Python 软件源连接失败，正在尝试系统证书直连…')
        direct={key:value for key,value in os.environ.items() if key.lower() not in {'http_proxy','https_proxy','all_proxy'}}
        await run(*pip_args,environment=direct)
    await run(python,'-m','mcdreforged','init',timeout=30)
    (root/'.atmosphere-runtime.json').write_text(json.dumps({'mode':'mcdr','core':core}),encoding='utf-8')


def runtime_mode(root):
    path=root/'.atmosphere-runtime.json'
    if not path.is_file(): return 'java'
    mode=json.loads(path.read_text(encoding='utf-8')).get('mode','java')
    if mode not in {'java','bedrock','mcdr'}: raise ValueError('实例运行模式无效')
    return mode


async def mcdr_command(root,java_args):
    python=root/'.mcdr-venv'/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
    if not python.is_file(): raise RuntimeError('MCDR Python 环境不存在，请重新部署或修复环境')
    # JSON 字符串列表兼容 YAML，启动命令不经过 shell。
    config=root/'config.yml'
    core=json.loads((root/'.atmosphere-runtime.json').read_text()).get('core','paper')
    handler='forge_handler' if core in {'forge','neoforge'} else 'bukkit_handler' if core in {'paper','purpur','spigot','folia'} else 'vanilla_handler'
    values={'working_directory':'.','start_command':java_args,'handler':handler,'encoding':'utf8','decoding':'utf8','plugin_directories':['mcdr_plugins'],'advanced_console':False,'disable_console_color':True,'telemetry':False,'check_update':False}
    # 使用 MCDR 自身的 YAML 依赖保留注释和扩展键，避免文本替换损坏列表。
    code="""import json,sys,os
from pathlib import Path
from ruamel.yaml import YAML
yaml=YAML(typ='rt');path=Path('config.yml')
data=yaml.load(path.read_text(encoding='utf-8')) if path.exists() else {}
if not isinstance(data,dict):raise ValueError('MCDR config must be a mapping')
data.update(json.loads(sys.stdin.read()))
temporary=path.with_suffix('.yml.panel-tmp')
with temporary.open('w',encoding='utf-8') as output:yaml.dump(data,output)
if path.exists():os.chmod(temporary,path.stat().st_mode)
os.replace(temporary,path)
"""
    process=await asyncio.create_subprocess_exec(str(python),'-c',code,cwd=root,stdin=asyncio.subprocess.PIPE,stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.PIPE)
    try: _,error=await asyncio.wait_for(process.communicate(json.dumps(values,ensure_ascii=False).encode('utf-8')),15)
    except (TimeoutError,asyncio.CancelledError):process.kill();await process.wait();raise
    if process.returncode:raise ValueError('MCDR config.yml 无法安全更新，请检查配置：'+error.decode(errors='replace')[-500:])
    (root/'mcdr_plugins').mkdir(exist_ok=True)
    return [str(python),'-m','mcdreforged']
