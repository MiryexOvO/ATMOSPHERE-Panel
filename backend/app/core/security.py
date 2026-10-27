from __future__ import annotations
import hashlib, time
from fastapi import Request
from fastapi.responses import JSONResponse
from .config import SESSION_HOURS
from .database import connect

def current_user(request: Request):
    token = request.cookies.get('mc_panel_session')
    if not token: return None
    conn = connect()
    row = conn.execute("SELECT users.id, users.username FROM sessions JOIN users ON users.id=sessions.user_id WHERE token_hash=? AND expires_at>?", (hashlib.sha256(token.encode()).hexdigest(), int(time.time()))).fetchone()
    conn.close()
    return row

def require_user(request: Request):
    user = current_user(request)
    return user if user else JSONResponse({'ok': False, 'message': '未登录'}, status_code=401)
