from __future__ import annotations
import hashlib, os, secrets, string, time, bcrypt
from loguru import logger
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from ..core.config import CREDENTIALS_PATH, SESSION_HOURS
from ..core.database import connect
from ..core.security import current_user
router = APIRouter()
class LoginPayload(BaseModel):
    username: str = Field(min_length=1, max_length=32)
    password: str = Field(min_length=1, max_length=256)
    code: str = Field(default='',max_length=6)

def write_credentials(user_id: int, username: str, password: str) -> None:
    """把一次性初始凭据写入数据目录，安装器和 atmosphere 命令据此显示密码。"""
    body = (
        'ATMOSPHERE PANEL · 初始凭据 / INITIAL CREDENTIALS\n'
        f'id: {user_id}\n'
        f'user: {username}\n'
        f'password: {password}\n'
        f'created: {time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}\n'
        '首次登录后请立即修改密码，修改后此文件会自动删除。\n'
        'Change the password after the first login; this file is deleted automatically.\n'
    )
    try:
        fd = os.open(CREDENTIALS_PATH, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, 'w', encoding='utf-8') as file:
            file.write(body)
        os.chmod(CREDENTIALS_PATH, 0o600)
    except OSError as exc:
        logger.warning('初始凭据文件写入失败: {}', exc)

def credentials_field(name: str) -> str:
    """读取凭据文件中的单个字段，文件不存在或不可读时返回空串。"""
    try:
        for line in CREDENTIALS_PATH.read_text(encoding='utf-8').splitlines():
            if line.startswith(f'{name}: '):
                return line[len(name) + 2:].strip()
    except OSError:
        pass
    return ''

def clear_credentials(user_id: int | None = None) -> None:
    """密码不再是初始值时删除凭据文件；指定 ID 时只处理该账号的文件。"""
    if user_id is not None:
        stored = credentials_field('id')
        if stored and stored != str(user_id):
            return
    try:
        CREDENTIALS_PATH.unlink()
    except FileNotFoundError:
        pass
    except OSError as exc:
        logger.warning('初始凭据文件删除失败: {}', exc)

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
    cursor = conn.execute('INSERT INTO users(username,password_hash,created_at) VALUES(?,?,?)', ('Atmo7', bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode(), int(time.time())))
    conn.commit(); conn.close()
    write_credentials(cursor.lastrowid, 'Atmo7', password)
    print('\n' + '╔' + '═' * 70 + '╗')
    print('║' + ' ' * 18 + 'ATMOSPHERE / INITIAL ACCESS' + ' ' * 24 + '║')
    print('║  [INIT] 面板初始密码: ' + password + ' ' * max(0, 70 - 20 - len(password)) + '║')
    print('║  请立即登录并修改密码。明文只在首次初始化时输出。' + ' ' * 20 + '║')
    print('╚' + '═' * 70 + '╝')
    print('  凭据文件 / CREDENTIALS  ' + str(CREDENTIALS_PATH) + '\n', flush=True)

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
