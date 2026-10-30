import sys
from loguru import logger
from fastapi import FastAPI

logger.remove()
logger.add(sys.stderr, level='INFO', colorize=True, format='<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{message}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan>')
from fastapi.middleware.cors import CORSMiddleware
from .core.database import init_db
from .routers.auth import ensure_initial_user
from .routers import health, auth, resources, instances, console, files_backups, deployments

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
    @app.on_event('startup')
    def startup():
        init_db()
        ensure_initial_user()
        logger.info('✨ ATMOSPHERE BACKEND · CONTROL PLANE READY / PORT 27777')
        logger.info('🧭 Logs: journalctl -u atmosphere-panel.service -f')
    return app
app=create_app()