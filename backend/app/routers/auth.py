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
@router.post('/api/login')
@router.post('/login')
def login(payload: LoginPayload):
    conn=connect(); row=conn.execute('SELECT id,password_hash FROM users WHERE username=?',(payload.username,)).fetchone()
    if not row or not bcrypt.checkpw(payload.password.encode(), row['password_hash'].encode()):
        conn.close(); return JSONResponse({'ok':False,'message':'用户名或密码错误'},status_code=401)
    token=secrets.token_urlsafe(48); now=int(time.time()); conn.execute('INSERT INTO sessions VALUES(?,?,?,?)',(hashlib.sha256(token.encode()).hexdigest(),row['id'],now+SESSION_HOURS*3600,now)); conn.commit(); conn.close()
    response=JSONResponse({'ok':True,'user':{'username':payload.username}}); response.set_cookie('mc_panel_session',token,max_age=SESSION_HOURS*3600,httponly=True,samesite='lax'); return response
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
