from fastapi import FastAPI
from .core.database import init_db
from .routers import health, auth, resources, instances

def create_app() -> FastAPI:
    app=FastAPI(title='Atmosphere API',version='0.2.0')
    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(resources.router)
    app.include_router(instances.router)
    @app.on_event('startup')
    def startup(): init_db()
    return app
app=create_app()
