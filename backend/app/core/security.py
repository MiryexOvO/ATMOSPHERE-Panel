from __future__ import annotations
import hashlib, time, json
from fastapi import Request
from fastapi.responses import JSONResponse
from .config import SESSION_HOURS
from .database import connect

def current_user(request: Request):
    token = request.cookies.get('mc_panel_session')
    if not token: return None
    conn = connect()
    row = conn.execute("SELECT users.id, users.username,users.role FROM sessions JOIN users ON users.id=sessions.user_id WHERE token_hash=? AND expires_at>? AND users.enabled=1", (hashlib.sha256(token.encode()).hexdigest(), int(time.time()))).fetchone()
    conn.close()
    return row

def require_user(request: Request):
    user = current_user(request)
    # 每次请求重新核验实例授权，撤权立即生效。
    instance_id = request.path_params.get('instance_id')
    if user and user['role']!='admin' and request.method=='POST' and request.url.path in {'/api/instances/deploy','/api/instances/package','/api/instances/package/inspect','/api/deploy/modes'}:
        return JSONResponse({'message':'创建实例需要管理员权限'},status_code=403)
    if user and instance_id and not can_access(user, instance_id, permission_for(request)):
        return JSONResponse({'message': '没有此实例的操作权限'}, status_code=403)
    # 只读账户不能调用写入接口。
    if user and user['role'] == 'viewer' and request.method not in {'GET', 'HEAD', 'OPTIONS'}:
        return JSONResponse({'ok': False, 'message': '当前账户只有只读权限'}, status_code=403)
    if user and user['role'] == 'viewer' and request.url.path.startswith('/api/instances/'):
        # 配置与文件可能包含 RCON 密码，不向观察账户暴露。
        path = request.url.path
        if '/files' in path or path.endswith(('/settings', '/properties', '/export')):
            return JSONResponse({'ok': False, 'message': '只读账户仅可查看状态、监测和日志'}, status_code=403)
    return user if user else JSONResponse({'ok': False, 'message': '未登录'}, status_code=401)


def permission_for(request: Request):
    path = request.url.path
    if request.method=='DELETE' and path.rstrip('/').count('/')==3: return 'delete'
    for segment, permission in [('files','files'),('backups','backups'),('export','files'),('players','players'),('addons','files'),('icon','settings'),('settings','settings'),('properties','settings'),('command','command'),('power','power'),('logs','console')]:
        if segment in path.split('/'): return permission
    return 'view'


def can_access(user, instance_id, permission='view'):
    if user['role'] == 'admin': return True
    conn = connect()
    row = conn.execute('SELECT permissions FROM user_access WHERE user_id=? AND instance_id=?',(user['id'],instance_id)).fetchone()
    conn.close()
    return bool(row and (permission == 'view' or permission in json.loads(row['permissions'])))


def require_admin(request: Request):
    user = current_user(request)
    if user and user['role'] != 'admin':
        return JSONResponse({'ok': False, 'message': '需要管理员权限'}, status_code=403)
    return user if user else JSONResponse({'ok': False, 'message': '未登录'}, status_code=401)
