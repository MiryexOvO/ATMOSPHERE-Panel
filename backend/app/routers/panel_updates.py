"""只从本项目发布源检查并缓存更新包。"""
import asyncio, hashlib, json, os, platform, time, ssl
from pathlib import Path
from fastapi import APIRouter, Request, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse, FileResponse
import httpx
from ..core.security import require_admin
from ..core.config import BASE_DIR
from ..services.panel_settings import read_settings, audit
from ..services.tls_gateway import certificates

router=APIRouter(prefix='/api/panel',tags=['panel-updates'])
REPOSITORY='MiryexOvO/ATMOSPHERE-Panel'
CURRENT_VERSION='0.2.0'
UPDATE_ROOT=BASE_DIR/'updates'
lock=asyncio.Lock()
state={'status':'idle','progress':0,'error':''}


async def release():
    # 系统代理不可用时尝试直连，始终验证系统信任证书。
    for use_proxy in [True,False]:
        try:
            async with httpx.AsyncClient(trust_env=use_proxy,verify=ssl.create_default_context(),timeout=20,follow_redirects=True,headers={'Accept':'application/vnd.github+json','User-Agent':'ATMOSPHERE-Panel'}) as client:
                response=await client.get(f'https://api.github.com/repos/{REPOSITORY}/releases/latest')
                if response.status_code==404: return {'current':CURRENT_VERSION,'available':False,'message':'发布源尚无可访问的正式版本','assets':[]}
                response.raise_for_status();data=response.json();break
        except httpx.TransportError:
            if not use_proxy: raise
    assets=[{'id':a['id'],'name':a['name'],'size':a['size'],'url':a['browser_download_url'],'digest':a.get('digest')} for a in data.get('assets',[]) if a['name'].lower().endswith(('.zip','.tar.gz','.exe','.dmg','.appimage'))]
    from re import findall
    def version(value): return tuple(int(n) for n in findall(r'\d+',value)[:3])
    return {'current':CURRENT_VERSION,'latest':data['tag_name'],'available':version(data['tag_name'])>version(CURRENT_VERSION),'notes':data.get('body',''),'page':data['html_url'],'assets':assets}


async def download_update(asset_id=None):
    if lock.locked(): raise ValueError('更新包正在下载')
    async with lock:
        try:
            info=await release()
            if not info['available']: raise ValueError(info.get('message') or '当前已是最新版本')
            assets=info['assets']
            if asset_id is not None: assets=[a for a in assets if a['id']==asset_id]
            else:
                label={'Windows':'win','Darwin':'mac','Linux':'linux'}.get(platform.system(),'')
                assets=[a for a in assets if label in a['name'].lower()] or [a for a in assets if a['name'].lower().endswith('.zip')]
            if not assets: raise ValueError('发布中没有适用于本机的更新包')
            asset=assets[0];name=Path(asset['name']).name
            if name!=asset['name'] or asset['size']>1024**3 or not asset['url'].startswith(f'https://github.com/{REPOSITORY}/releases/download/'): raise ValueError('发布包信息无效')
            UPDATE_ROOT.mkdir(parents=True,exist_ok=True);target=UPDATE_ROOT/name;temporary=target.with_suffix(target.suffix+'.part')
            state.update(status='downloading',progress=0,error='');digest=hashlib.sha256();total=0
            try:
                async with httpx.AsyncClient(trust_env=False,verify=ssl.create_default_context(),timeout=httpx.Timeout(20,read=60),follow_redirects=True) as client:
                    async with client.stream('GET',asset['url']) as response:
                        response.raise_for_status()
                        with temporary.open('wb') as output:
                            async for chunk in response.aiter_bytes(262144):
                                total+=len(chunk)
                                if total>1024**3: raise ValueError('更新包超出大小限制')
                                output.write(chunk);digest.update(chunk);state['progress']=int(total/max(1,asset['size'])*100)
                if total!=asset['size']: raise ValueError('更新包大小不匹配')
                expected=asset.get('digest')
                if expected and expected!='sha256:'+digest.hexdigest(): raise ValueError('更新包摘要校验失败')
                os.replace(temporary,target)
            finally: temporary.unlink(missing_ok=True)
            metadata={'name':name,'version':info['latest'],'sha256':digest.hexdigest(),'verified_digest':bool(expected),'downloaded_at':int(time.time())}
            (UPDATE_ROOT/'ready.json').write_text(json.dumps(metadata),encoding='utf-8');state.update(status='ready',progress=100)
            return metadata
        except Exception as exc: state.update(status='error',error=str(exc));raise


@router.get('/updates')
async def check_updates(request:Request):
    if isinstance(user:=require_admin(request),JSONResponse): return user
    try: info=await release()
    except (httpx.HTTPError,ValueError,KeyError) as exc: raise HTTPException(502,'检查更新失败：'+str(exc))
    ready=None
    if (UPDATE_ROOT/'ready.json').is_file(): ready=json.loads((UPDATE_ROOT/'ready.json').read_text())
    return {**info,'download':state,'ready':ready}


@router.post('/updates/download')
async def request_download(request:Request):
    if isinstance(user:=require_admin(request),JSONResponse): return user
    try: result=await download_update()
    except (httpx.HTTPError,ValueError,OSError) as exc: raise HTTPException(422,str(exc))
    audit(user['id'],'panel.update.download',result['version']);return result


@router.get('/updates/package')
def package(request:Request):
    if isinstance(user:=require_admin(request),JSONResponse): return user
    if not (UPDATE_ROOT/'ready.json').is_file(): raise HTTPException(404,'尚未下载更新包')
    data=json.loads((UPDATE_ROOT/'ready.json').read_text());target=UPDATE_ROOT/Path(data['name']).name
    if not target.is_file(): raise HTTPException(404,'更新包不存在')
    return FileResponse(target,filename=target.name)


@router.post('/tls/certificate')
async def upload_cert(request:Request,certificate:UploadFile=File(...),private_key:UploadFile=File(...)):
    if isinstance(user:=require_admin(request),JSONResponse): return user
    if read_settings()['https_enabled']: raise HTTPException(409,'请先关闭 HTTPS 再替换证书')
    cert,key=certificates(False);certificate_data=await certificate.read(65537);key_data=await private_key.read(65537)
    if len(certificate_data)>65536 or len(key_data)>65536: raise HTTPException(422,'证书文件过大')
    import ssl
    temporary_cert=cert.with_suffix('.pending');temporary_key=key.with_suffix('.pending')
    try:
        temporary_cert.write_bytes(certificate_data);temporary_key.write_bytes(key_data)
        if os.name!='nt': temporary_key.chmod(0o600)
        context=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);context.load_cert_chain(temporary_cert,temporary_key)
        os.replace(temporary_cert,cert);os.replace(temporary_key,key)
    except (OSError,ssl.SSLError) as exc: raise HTTPException(422,'证书与私钥不匹配或格式错误：'+str(exc))
    finally: temporary_cert.unlink(missing_ok=True);temporary_key.unlink(missing_ok=True)
    audit(user['id'],'panel.tls.certificate');return {'ok':True}


async def auto_updates():
    while True:
        await asyncio.sleep(3600)
        if read_settings()['update_auto_download']:
            try:
                info=await release()
                ready=UPDATE_ROOT/'ready.json'
                if info['available'] and (not ready.exists() or json.loads(ready.read_text()).get('version')!=info['latest']): await download_update()
            except Exception as exc: state.update(status='error',error=str(exc))
