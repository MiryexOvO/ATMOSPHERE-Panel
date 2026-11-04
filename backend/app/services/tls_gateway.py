"""独立 HTTPS 入口，保留开发环境 HTTP API 代理。"""
import asyncio, os, shutil, ssl
from pathlib import Path
import httpx, uvicorn
from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import StreamingResponse
from starlette.background import BackgroundTask
from ..core.config import BASE_DIR

TLS_ROOT=BASE_DIR/'tls'
server=None
task=None
active=None


def certificates(self_signed):
    TLS_ROOT.mkdir(parents=True,exist_ok=True)
    cert=TLS_ROOT/('self-cert.pem' if self_signed else 'custom-cert.pem')
    key=TLS_ROOT/('self-key.pem' if self_signed else 'custom-key.pem')
    return cert,key


async def ensure_certificate(self_signed):
    cert,key=certificates(self_signed)
    if self_signed and not (cert.exists() and key.exists()):
        openssl=shutil.which('openssl')
        if not openssl and os.name=='nt':
            candidate=Path(os.environ.get('ProgramFiles','C:/Program Files'))/'Git/usr/bin/openssl.exe'
            if candidate.is_file(): openssl=str(candidate)
        if not openssl: raise ValueError('未找到 OpenSSL，请安装或上传证书和私钥')
        process=await asyncio.create_subprocess_exec(openssl,'req','-x509','-newkey','rsa:2048','-nodes','-keyout',str(key),'-out',str(cert),'-days','365','-subj','/CN=ATMOSPHERE','-addext','subjectAltName=DNS:localhost,IP:127.0.0.1',stdout=asyncio.subprocess.DEVNULL,stderr=asyncio.subprocess.PIPE)
        _,error=await process.communicate()
        if process.returncode: raise RuntimeError('证书生成失败：'+error.decode(errors='replace')[-300:])
        if os.name!='nt': key.chmod(0o600)
    if not cert.exists() or not key.exists(): raise ValueError('请先上传证书及私钥')
    context=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(cert,key)
    return cert,key


async def configure_gateway(settings):
    global server,task,active
    signature=(settings['https_enabled'],settings['https_self_signed'],settings['https_port'],settings['frontend_port'])
    if signature==active and task and not task.done(): return
    if settings['https_port'] in {27777,settings['frontend_port']}: raise ValueError('HTTPS 端口不能与 API 或前端端口相同')
    cert=key=None
    if settings['https_enabled']: cert,key=await ensure_certificate(settings['https_self_signed'])
    # 绑定前检查新端口，避免保存无法使用的开关。
    import socket
    if settings['https_enabled'] and (not active or active[2]!=settings['https_port'] or not task or task.done()):
        probe=socket.socket()
        try: probe.bind(('0.0.0.0',settings['https_port']))
        finally: probe.close()
    if server: server.should_exit=True
    if task: await task
    active=signature;server=None;task=None
    if not settings['https_enabled']: return
    gateway=FastAPI(docs_url=None,redoc_url=None,openapi_url=None)
    @gateway.api_route('/{path:path}',methods=['GET','HEAD','POST','PUT','PATCH','DELETE','OPTIONS'])
    async def forward(path:str,request:Request):
        port=int(os.getenv('ATMOSPHERE_BACKEND_PORT','27777')) if os.getenv('ATMOSPHERE_WEB_DIR') or path=='api' or path.startswith('api/') else settings['frontend_port']
        headers={k:v for k,v in request.headers.items() if k.lower() not in {'host','connection','content-length','x-forwarded-for','x-forwarded-proto'}}
        headers.update({'x-forwarded-proto':'https','x-forwarded-for':request.client.host if request.client else '127.0.0.1'})
        client=httpx.AsyncClient(timeout=httpx.Timeout(30,read=None),follow_redirects=False)
        try:
            upstream=await client.send(client.build_request(request.method,f'http://127.0.0.1:{port}/'+path,params=request.query_params,headers=headers,content=request.stream()),stream=True)
        except Exception:
            await client.aclose();raise
        async def close(): await upstream.aclose();await client.aclose()
        result=StreamingResponse(upstream.aiter_raw(),status_code=upstream.status_code,background=BackgroundTask(close))
        result.raw_headers=[(k,v) for k,v in upstream.headers.raw if k.lower() not in {b'connection',b'transfer-encoding',b'content-length'}]
        return result
    @gateway.websocket('/{path:path}')
    async def forward_socket(websocket:WebSocket,path:str):
        # 同源转发前端 HMR；连接随任一方向关闭而结束。
        from websockets.asyncio.client import connect
        protocols=[v.strip() for v in websocket.headers.get('sec-websocket-protocol','').split(',') if v.strip()]
        try:
            async with connect(f"ws://127.0.0.1:{settings['frontend_port']}/"+path+('?' + websocket.url.query if websocket.url.query else ''),subprotocols=protocols or None) as upstream:
                await websocket.accept(subprotocol=upstream.subprotocol)
                async def incoming():
                    while True:
                        event=await websocket.receive()
                        if event['type']=='websocket.disconnect': return
                        await upstream.send(event.get('text') if event.get('text') is not None else event.get('bytes',b''))
                async def outgoing():
                    async for data in upstream:
                        if isinstance(data,str): await websocket.send_text(data)
                        else: await websocket.send_bytes(data)
                jobs=[asyncio.create_task(incoming()),asyncio.create_task(outgoing())]
                try: await asyncio.wait(jobs,return_when=asyncio.FIRST_COMPLETED)
                finally:
                    for job in jobs: job.cancel()
                    await asyncio.gather(*jobs,return_exceptions=True)
        except Exception: await websocket.close()
    config=uvicorn.Config(gateway,host='0.0.0.0',port=settings['https_port'],ssl_certfile=str(cert),ssl_keyfile=str(key),log_level='warning')
    server=uvicorn.Server(config)
    from contextlib import nullcontext
    server.capture_signals=lambda:nullcontext()
    server.install_signal_handlers=lambda:None
    task=asyncio.create_task(server.serve())
    for _ in range(100):
        if server.started: return
        if task.done(): await task;raise RuntimeError('HTTPS 入口启动失败')
        await asyncio.sleep(.05)
    raise RuntimeError('HTTPS 入口启动超时')


async def stop_gateway():
    if server: server.should_exit=True
    if task: await task
