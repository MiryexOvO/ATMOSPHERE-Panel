import sys, asyncio
from loguru import logger
from fastapi import FastAPI

from .terminal import configure_logs,show_banner
configure_logs()
from fastapi.middleware.cors import CORSMiddleware
from .core.database import init_db
from .routers.auth import ensure_initial_user
from .routers import health, auth, resources, instances, console, files_backups, deployments, admin, instance_tools, schedules, account_security, panel_updates

def create_app() -> FastAPI:
    app = FastAPI(title='Atmosphere API', version='0.2.0')
    app.add_middleware(CORSMiddleware, allow_origins=['http://localhost:3000', 'http://localhost:5173'], allow_credentials=True, allow_methods=['*'], allow_headers=['*'])
    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(resources.router)
    app.include_router(instances.router)
    app.include_router(console.router)
    app.include_router(files_backups.router)
    app.include_router(deployments.router)
    app.include_router(admin.router)
    app.include_router(instance_tools.router)
    app.include_router(schedules.router)
    app.include_router(account_security.router)
    app.include_router(panel_updates.router)
    @app.middleware('http')
    async def audit_writes(request, call_next):
        from .core.security import current_user
        from .services.panel_settings import audit
        response=await call_next(request)
        # 不记录请求正文，避免密码和 RCON 凭据进入审计。
        if request.method in {'POST','PUT','PATCH','DELETE'} and response.status_code<400:
            user=current_user(request)
            if user: audit(user['id'],'http.'+request.method.lower(),request.url.path)
        return response
    @app.on_event('startup')
    async def startup():
        init_db()
        ensure_initial_user()
        # 后端统一托管调度器，关闭时停止后台任务。
        from .services.scheduler import run_scheduler
        app.state.scheduler = asyncio.create_task(run_scheduler())
        from .services.tls_gateway import configure_gateway
        from .services.panel_settings import read_settings
        from .routers.panel_updates import auto_updates
        try: await configure_gateway(read_settings())
        except Exception as exc: logger.error('HTTPS 入口未启动: {}',exc)
        app.state.updater=asyncio.create_task(auto_updates())
        show_banner()
    @app.on_event('shutdown')
    async def shutdown():
        app.state.scheduler.cancel()
        app.state.updater.cancel()
        await asyncio.gather(app.state.scheduler,app.state.updater,return_exceptions=True)
        from .services.tls_gateway import stop_gateway
        await stop_gateway()
    from .web import mount_frontend
    mount_frontend(app)
    return app
app=create_app()
