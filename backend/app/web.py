"""Serve the built SPA after all API routes."""
import os
from pathlib import Path
from starlette.exceptions import HTTPException
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse

class FrontendFiles(StaticFiles):
    async def get_response(self, path, scope):
        path = path.replace(chr(92), '/').lstrip('/')
        if path == 'api' or path.startswith('api/'):
            raise HTTPException(404)
        try:
            response = await super().get_response(path, scope)
            if response.status_code != 404:
                return response
        except HTTPException as exc:
            if exc.status_code != 404:
                raise
        # StaticFiles may return 404.html instead of raising in HTML mode.
        if '.' in Path(path).name or path.startswith('_nuxt/'):
            raise HTTPException(404)
        return FileResponse(Path(self.directory) / 'index.html')

def mount_frontend(app):
    directory = Path(os.getenv('ATMOSPHERE_WEB_DIR') or Path(__file__).resolve().parents[2] / 'web')
    if (directory / 'index.html').is_file():
        app.mount('/', FrontendFiles(directory=directory, html=True), name='frontend')
