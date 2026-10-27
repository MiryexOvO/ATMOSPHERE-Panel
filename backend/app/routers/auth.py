from __future__ import annotations
import hashlib, secrets, string, time, bcrypt
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from ..core.config import SESSION_HOURS
from ..core.database import connect
from ..core.security import current_user
router = APIRouter()
class LoginPayload(BaseModel):
    username: str = Field(min_length=1, max_length=32)
    password: str = Field(min_length=1, max_length=256)

def ensure_initial_user() -> None:
    conn = connect()
    row = conn.execute("SELECT id FROM users WHERE username='Atmo7'").fetchone()
    if row:
        conn.close()
        return
    legacy = conn.execute("SELECT id FROM users WHERE username='admin'").fetchone()
    if legacy:
        conn.execute("UPDATE users SET username='Atmo7' WHERE id=?", (legacy['id'],))
        conn.commit(); conn.close(); return
    alphabet = string.ascii_letters + string.digits + '!@#$%^&*_-+=?'
    password = ''.join(secrets.choice(alphabet) for _ in range(20))
    conn.execute('INSERT INTO users(username,password_hash,created_at) VALUES(?,?,?)', ('Atmo7', bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode(), int(time.time())))
    conn.commit(); conn.close()
    print('\n' + '╔' + '═' * 70 + '╗')
    print('║' + ' ' * 18 + 'ATMOSPHERE / INITIAL ACCESS' + ' ' * 24 + '║')
    print('║  [INIT] 面板初始密码: ' + password + ' ' * max(0, 70 - 20 - len(password)) + '║')
    print('║  请立即登录并修改密码。明文只在首次初始化时输出。' + ' ' * 20 + '║')
    print('╚' + '═' * 70 + '╝\n', flush=True)

@router.post('/api/login')
@router.post('/login')
def login(payload: LoginPayload):
    conn=connect(); row=conn.execute('SELECT id,password_hash FROM users WHERE username=?',(payload.username,)).fetchone()
    if not row or not bcrypt.checkpw(payload.password.encode(), row['password_hash'].encode()): conn.close(); return JSONResponse({'ok':False,'message':'用户名或密码错误'},status_code=401)
    token=secrets.token_urlsafe(48); now=int(time.time()); conn.execute('INSERT INTO sessions VALUES(?,?,?,?)',(hashlib.sha256(token.encode()).hexdigest(),row['id'],now+SESSION_HOURS*3600,now)); conn.commit(); conn.close(); response=JSONResponse({'ok':True,'user':{'username':payload.username}}); response.set_cookie('mc_panel_session',token,max_age=SESSION_HOURS*3600,httponly=True,samesite='lax'); return response
@router.get('/api/me')
@router.get('/me')
def me(request: Request):
    user=current_user(request); return {'ok':True,'user':{'username':user['username']}} if user else JSONResponse({'ok':False,'message':'未登录'},status_code=401)
@router.post('/api/logout')
@router.post('/logout')
def logout(request: Request):
    token=request.cookies.get('mc_panel_session'); conn=connect()
    if token: conn.execute('DELETE FROM sessions WHERE token_hash=?',(hashlib.sha256(token.encode()).hexdigest(),)); conn.commit()
    conn.close(); response=JSONResponse({'ok':True}); response.delete_cookie('mc_panel_session'); return response
