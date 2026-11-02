"""账户二步验证与新网络登录提醒。"""
import base64, secrets, hashlib
from contextlib import closing
from urllib.parse import quote
import bcrypt
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel, Field
from ..core.database import connect
from ..core.security import current_user
from ..services.login_security import verify
from ..services.panel_settings import audit

router=APIRouter(prefix='/api/account',tags=['account-security'])


class Proof(BaseModel):
    password:str=Field(min_length=1,max_length=72)
    code:str=Field(default='',max_length=6)


def account(request):
    user=current_user(request)
    if not user: raise HTTPException(401,'未登录')
    with closing(connect()) as conn: row=conn.execute('SELECT * FROM users WHERE id=?',(user['id'],)).fetchone()
    return row


def check_password(row,payload):
    if len(payload.password.encode())>72 or not bcrypt.checkpw(payload.password.encode(),row['password_hash'].encode()): raise HTTPException(403,'密码错误')


@router.get('/security')
def security(request:Request):
    row=account(request)
    with closing(connect()) as conn:
        events=[dict(event) for event in conn.execute('SELECT id,ip,network,success,unusual,created_at FROM login_events WHERE user_id=? ORDER BY id DESC LIMIT 30',(row['id'],))]
    return {'totp_enabled':bool(row['totp_secret']),'events':events}


@router.post('/totp/setup')
def setup(request:Request,payload:Proof):
    row=account(request);check_password(row,payload)
    if row['totp_secret']: raise HTTPException(409,'二步验证已启用')
    secret=base64.b32encode(secrets.token_bytes(20)).decode()
    with closing(connect()) as conn:
        conn.execute('UPDATE users SET totp_pending=? WHERE id=?',(secret,row['id']));conn.commit()
    return {'secret':secret,'uri':'otpauth://totp/'+quote('ATMOSPHERE:'+row['username'],safe='')+'?secret='+secret+'&issuer=ATMOSPHERE'}


@router.post('/totp/confirm')
def confirm(request:Request,payload:Proof):
    row=account(request);check_password(row,payload)
    if not row['totp_pending'] or not verify(row['totp_pending'],payload.code): raise HTTPException(422,'验证码错误或过期')
    with closing(connect()) as conn:
        conn.execute("UPDATE users SET totp_secret=totp_pending,totp_pending='',last_totp_step=0 WHERE id=?",(row['id'],))
        token_hash=hashlib.sha256((request.cookies.get('mc_panel_session') or '').encode()).hexdigest()
        conn.execute('DELETE FROM sessions WHERE user_id=? AND token_hash<>?',(row['id'],token_hash));conn.commit()
    audit(row['id'],'account.totp.enable');return {'ok':True}


@router.post('/totp/disable')
def disable(request:Request,payload:Proof):
    row=account(request);check_password(row,payload)
    if not row['totp_secret'] or not verify(row['totp_secret'],payload.code): raise HTTPException(422,'验证码错误或过期')
    with closing(connect()) as conn:
        conn.execute("UPDATE users SET totp_secret='',totp_pending='' WHERE id=?",(row['id'],));conn.commit()
    audit(row['id'],'account.totp.disable');return {'ok':True}
