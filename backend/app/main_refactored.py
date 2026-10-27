from fastapi import FastAPI
from .core.database import init_db
from .routers.auth import ensure_initial_user
from .routers import health, auth, resources, instances, console, files_backups, deployments

def create_app() -> FastAPI:
    app=FastAPI(title='Atmosphere API',version='0.2.0')
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
        print('╔' + '═' * 70 + '╗')
        print('║' + ' ' * 24 + 'ATMOSPHERE BACKEND' + ' ' * 28 + '║')
        print('║' + ' ' * 18 + 'CONTROL PLANE READY / PORT 27777' + ' ' * 19 + '║')
        print('╚' + '═' * 70 + '╝', flush=True)
    return app
app=create_app()