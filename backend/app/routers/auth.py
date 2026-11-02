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
    code: str = Field(default='',max_length=6)

def ensure_initial_user() -> None:
    conn = connect()
    row = conn.execute('SELECT id FROM users LIMIT 1').fetchone()
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
def login(request:Request,payload: LoginPayload):
    from ..services.panel_settings import read_settings
    from ..services.login_security import matching_step,client_ip,login_event
    ip=client_ip(request)
    # 长密码先校验长度，避免 bcrypt 抛出未处理异常。
    if len(payload.password.encode()) > 72:
        return JSONResponse({'ok':False,'message':'用户名或密码错误'},status_code=401)
    conn=connect()
    # 同一来源十分钟内连续失败十次，短暂限制暴力尝试。
    failures=conn.execute('SELECT count(*) FROM login_events WHERE ip=? AND success=0 AND created_at>?',(ip,int(time.time())-600)).fetchone()[0]
    if failures>=10: conn.close();return JSONResponse({'message':'登录尝试过多，请稍后重试'},status_code=429)
    row=conn.execute('SELECT id,password_hash,enabled,role,totp_secret FROM users WHERE username=?',(payload.username,)).fetchone()
    if not row or not row['enabled'] or not bcrypt.checkpw(payload.password.encode(),row['password_hash'].encode()):
        conn.close();login_event(payload.username,ip,False,row['id'] if row else None);return JSONResponse({'ok':False,'message':'用户名或密码错误'},status_code=401)
    step=matching_step(row['totp_secret'],payload.code) if row['totp_secret'] else None
    if row['totp_secret'] and step is None:
        conn.close()
        if payload.code: login_event(payload.username,ip,False,row['id'])
        return JSONResponse({'message':'请输入验证器中的六位验证码','totp_required':True},status_code=401)
    if row['totp_secret']:
        claimed=conn.execute('UPDATE users SET last_totp_step=? WHERE id=? AND last_totp_step<?',(step,row['id'],step)).rowcount
        if not claimed:
            conn.close();return JSONResponse({'message':'验证码已使用，请等待下一个验证码'},status_code=401)
    token=secrets.token_urlsafe(48);now=int(time.time());hours=read_settings()['session_hours']
    conn.execute('INSERT INTO sessions VALUES(?,?,?,?)',(hashlib.sha256(token.encode()).hexdigest(),row['id'],now+hours*3600,now))
    conn.commit();conn.close()
    unusual=login_event(payload.username,ip,True,row['id'])
    response=JSONResponse({'ok':True,'user':{'username':payload.username,'role':row['role']},'unusual_login':unusual})
    response.set_cookie('mc_panel_session',token,max_age=hours*3600,httponly=True,samesite='lax',secure=request.url.scheme=='https')
    return response
@router.get('/api/me')
@router.get('/me')
def me(request: Request):
    user=current_user(request); return {'ok':True,'user':{'username':user['username'],'role':user['role'],'id':user['id']}} if user else JSONResponse({'ok':False,'message':'未登录'},status_code=401)
@router.post('/api/logout')
@router.post('/logout')
def logout(request: Request):
    token=request.cookies.get('mc_panel_session'); conn=connect()
    if token: conn.execute('DELETE FROM sessions WHERE token_hash=?',(hashlib.sha256(token.encode()).hexdigest(),)); conn.commit()
    conn.close(); response=JSONResponse({'ok':True}); response.delete_cookie('mc_panel_session'); return response
