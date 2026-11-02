import hashlib
import json
import time
from contextlib import closing
import bcrypt
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from ..core.database import connect
from ..core.security import current_user, require_admin
from ..services.panel_settings import read_settings, audit

router = APIRouter(prefix='/api', tags=['administration'])


class PanelSettings(BaseModel):
    download_source: str = Field(pattern='^(default|official|fastmirror|polars)$')
    metrics_interval_seconds: int = Field(ge=2, le=60)
    session_hours: int = Field(ge=1, le=168)
    default_locale: str = Field(pattern='^(zh|en|ja)$')
    upload_limit_mb: int = Field(ge=1, le=500)
    update_auto_download:bool=False
    https_enabled:bool=False
    https_self_signed:bool=True
    https_port:int=Field(default=8443,ge=1024,le=65535)
    frontend_port:int=Field(default=5173,ge=1024,le=65535)


@router.get('/panel/settings')
def get_settings(request: Request):
    if not current_user(request): return JSONResponse({'message': '未登录'}, status_code=401)
    return {'ok': True, 'settings': read_settings()}


@router.put('/panel/settings')
async def save_settings(request: Request, payload: PanelSettings):
    if isinstance(user := require_admin(request), JSONResponse): return user
    from ..services.tls_gateway import configure_gateway
    try: await configure_gateway(payload.model_dump())
    except (OSError,RuntimeError,ValueError) as exc: return JSONResponse({'message':str(exc)},status_code=422)
    with closing(connect()) as conn:
        conn.executemany('INSERT INTO panel_settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value',
                         [(key, json.dumps(value)) for key, value in payload.model_dump().items()])
        conn.commit()
    audit(user['id'], 'settings.update')
    return {'ok': True, 'settings': read_settings()}


class UserPayload(BaseModel):
    username: str = Field(min_length=2, max_length=32, pattern=r'^[A-Za-z0-9_-]+$')
    password: str = Field(default='', max_length=72)
    role: str = Field(default='operator', pattern='^(admin|operator|viewer)$')
    enabled: bool = True
    nickname: str = Field(default='',max_length=60)
    instance_ids: list[str] = Field(default_factory=list,max_length=500)
    permissions: list[str] = Field(default_factory=lambda:['view','console'],max_length=12)


def save_access(conn,user_id,payload):
    # 管理员全实例访问；其余账户逐实例分配能力。
    allowed={'view','console','command','power','files','backups','settings','players','schedule','delete'}
    if not set(payload.permissions)<=allowed: raise ValueError('未知权限')
    ids=set(payload.instance_ids)
    existing={row[0] for row in conn.execute('SELECT id FROM instances')}
    if not ids<=existing: raise ValueError('分配的实例不存在')
    conn.execute('UPDATE users SET nickname=? WHERE id=?',(payload.nickname,user_id))
    conn.execute('DELETE FROM user_access WHERE user_id=?',(user_id,))
    conn.executemany('INSERT INTO user_access VALUES(?,?,?)',[(user_id,instance_id,json.dumps(payload.permissions)) for instance_id in ids])


class PasswordPayload(BaseModel):
    current_password: str = Field(min_length=1, max_length=72)
    new_password: str = Field(min_length=8, max_length=72)


@router.post('/account/password')
def change_password(request: Request, payload: PasswordPayload):
    # 所有角色都能修改自身密码，注销其他登录会话。
    user = current_user(request)
    if not user: return JSONResponse({'message':'未登录'},status_code=401)
    if len(payload.current_password.encode()) > 72 or not 8 <= len(payload.new_password.encode()) <= 72:
        return JSONResponse({'message':'密码需要 8–72 字节'},status_code=422)
    with closing(connect()) as conn:
        row=conn.execute('SELECT password_hash FROM users WHERE id=?',(user['id'],)).fetchone()
        if not bcrypt.checkpw(payload.current_password.encode(),row['password_hash'].encode()): return JSONResponse({'message':'当前密码不正确'},status_code=403)
        conn.execute('UPDATE users SET password_hash=? WHERE id=?',(bcrypt.hashpw(payload.new_password.encode(),bcrypt.gensalt()).decode(),user['id']))
        token_hash=hashlib.sha256((request.cookies.get('mc_panel_session') or '').encode()).hexdigest()
        conn.execute('DELETE FROM sessions WHERE user_id=? AND token_hash<>?',(user['id'],token_hash));conn.commit()
    audit(user['id'],'account.password')
    return {'ok':True}


@router.get('/users')
def list_users(request: Request):
    if isinstance(user := require_admin(request), JSONResponse): return user
    with closing(connect()) as conn:
        users = [dict(row) for row in conn.execute('SELECT id,username,nickname,role,enabled,created_at,last_login FROM users ORDER BY id')]
        for item in users:
            access=conn.execute('SELECT instance_id,permissions FROM user_access WHERE user_id=?',(item['id'],)).fetchall()
            item['instance_ids']=[row['instance_id'] for row in access]
            item['permissions']=sorted({permission for row in access for permission in json.loads(row['permissions'])})
    return {'ok': True, 'users': users, 'current_id': user['id']}


@router.post('/users')
def create_user(request: Request, payload: UserPayload):
    if isinstance(user := require_admin(request), JSONResponse): return user
    if len(payload.password.encode()) < 8 or len(payload.password.encode()) > 72:
        return JSONResponse({'message': '密码需要 8–72 字节'}, status_code=422)
    with closing(connect()) as conn:
        if conn.execute('SELECT 1 FROM users WHERE username=?', (payload.username,)).fetchone():
            return JSONResponse({'message': '用户名已存在'}, status_code=409)
        cursor=conn.execute('INSERT INTO users(username,password_hash,role,enabled,created_at) VALUES(?,?,?,?,?)',
                     (payload.username,bcrypt.hashpw(payload.password.encode(),bcrypt.gensalt()).decode(),payload.role,int(payload.enabled),int(time.time())))
        try: save_access(conn,cursor.lastrowid,payload)
        except ValueError as exc: conn.rollback();return JSONResponse({'message':str(exc)},status_code=422)
        conn.commit()
    audit(user['id'], 'user.create', payload.username)
    return {'ok': True}


@router.put('/users/{user_id}')
def update_user(request: Request, user_id: int, payload: UserPayload):
    if isinstance(user := require_admin(request), JSONResponse): return user
    # 防止当前管理员锁住自己的账户。
    if user_id == user['id'] and (not payload.enabled or payload.role != 'admin'):
        return JSONResponse({'message': '不能禁用或降低自己的管理员权限'}, status_code=409)
    with closing(connect()) as conn:
        if not conn.execute('SELECT 1 FROM users WHERE id=?', (user_id,)).fetchone(): return JSONResponse({'message': '账户不存在'},status_code=404)
        if conn.execute('SELECT 1 FROM users WHERE username=? AND id<>?',(payload.username,user_id)).fetchone(): return JSONResponse({'message':'用户名已存在'},status_code=409)
        if payload.password:
            if not 8 <= len(payload.password.encode()) <= 72: return JSONResponse({'message':'密码需要 8–72 字节'},status_code=422)
            conn.execute('UPDATE users SET password_hash=? WHERE id=?',(bcrypt.hashpw(payload.password.encode(),bcrypt.gensalt()).decode(),user_id))
        conn.execute('UPDATE users SET username=?,role=?,enabled=? WHERE id=?',(payload.username,payload.role,int(payload.enabled),user_id))
        try: save_access(conn,user_id,payload)
        except ValueError as exc: conn.rollback();return JSONResponse({'message':str(exc)},status_code=422)
        if user_id == user['id']:
            current_hash=hashlib.sha256((request.cookies.get('mc_panel_session') or '').encode()).hexdigest()
            conn.execute('DELETE FROM sessions WHERE user_id=? AND token_hash<>?',(user_id,current_hash))
        else:
            conn.execute('DELETE FROM sessions WHERE user_id=?',(user_id,))
        conn.commit()
    audit(user['id'],'user.update',str(user_id))
    return {'ok':True}


@router.delete('/users/{user_id}')
def delete_user(request: Request, user_id: int):
    if isinstance(user := require_admin(request), JSONResponse): return user
    if user_id == user['id']: return JSONResponse({'message':'不能删除当前账户'},status_code=409)
    with closing(connect()) as conn:
        conn.execute('DELETE FROM sessions WHERE user_id=?',(user_id,));conn.execute('DELETE FROM user_access WHERE user_id=?',(user_id,));conn.execute('DELETE FROM users WHERE id=?',(user_id,));conn.commit()
    audit(user['id'],'user.delete',str(user_id))
    return {'ok':True}


@router.delete('/users/{user_id}/sessions')
def revoke_sessions(request: Request, user_id: int):
    if isinstance(user := require_admin(request), JSONResponse): return user
    with closing(connect()) as conn:
        conn.execute('DELETE FROM sessions WHERE user_id=?',(user_id,));conn.commit()
    audit(user['id'],'session.revoke',str(user_id))
    return {'ok':True}


@router.get('/audit')
def recent_audit(request: Request):
    if isinstance(user := require_admin(request), JSONResponse): return user
    with closing(connect()) as conn:
        rows=conn.execute('SELECT audit_log.*,users.username FROM audit_log LEFT JOIN users ON users.id=audit_log.user_id ORDER BY audit_log.id DESC LIMIT 100').fetchall()
    return {'ok':True,'events':[dict(row) for row in rows]}
