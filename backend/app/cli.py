"""非服务模式的命令行入口：查看初始凭据、重置密码。

由 `atmosphere-panel --show-password / --reset-password` 调用，
不启动 Web 服务，因此可以安全地在 systemd 服务停止时运行。
"""
from __future__ import annotations

import secrets
import string
import sys
from contextlib import closing

import bcrypt

from .core.config import CREDENTIALS_PATH
from .core.database import connect, init_db
from .routers.auth import clear_credentials, write_credentials

ALPHABET = string.ascii_letters + string.digits + '!@#$%^&*_-+=?'


def show_credentials() -> int:
    """仅在凭据文件存在时显示；文件被删除后不再提供任何找回途径。"""
    if not CREDENTIALS_PATH.exists():
        print('未找到初始凭据文件。', file=sys.stderr)
        print('初始密码只在首次部署时生成；如果已经修改过密码，就无法再显示。', file=sys.stderr)
        print('需要重置密码时运行: sudo atmosphere reset-password', file=sys.stderr)
        return 1
    try:
        text = CREDENTIALS_PATH.read_text(encoding='utf-8')
    except OSError as exc:
        print(f'无法读取凭据文件，请使用 root 运行: {exc}', file=sys.stderr)
        return 1
    print(text.rstrip())
    return 0


def reset_password(username: str = '', password: str = '') -> int:
    """生成新密码并写入数据库与凭据文件，同时注销该账号的所有会话。"""
    init_db()
    if password and not 8 <= len(password.encode()) <= 72:
        print('密码需要 8–72 字节', file=sys.stderr)
        return 2
    if not password:
        password = ''.join(secrets.choice(ALPHABET) for _ in range(20))
    with closing(connect()) as conn:
        if username:
            row = conn.execute('SELECT id,username FROM users WHERE username=?', (username,)).fetchone()
        else:
            row = conn.execute("SELECT id,username FROM users WHERE role='admin' ORDER BY id LIMIT 1").fetchone()
            row = row or conn.execute('SELECT id,username FROM users ORDER BY id LIMIT 1').fetchone()
        if not row:
            print('没有可重置的账号。请先启动面板生成初始账号，或在面板中创建账号。', file=sys.stderr)
            return 1
        conn.execute('UPDATE users SET password_hash=? WHERE id=?',
                     (bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode(), row['id']))
        conn.execute('DELETE FROM sessions WHERE user_id=?', (row['id'],))
        conn.commit()
        user_id, username = row['id'], row['username']
    # 先丢弃旧凭据，再写入新的，保证任何时刻文件内容都与数据库一致。
    clear_credentials(user_id)
    write_credentials(user_id, username, password)
    print('密码已重置 / PASSWORD RESET')
    print(f'  账号 / USER      {username}')
    print(f'  密码 / PASSWORD  {password}')
    print(f'  凭据文件 / FILE  {CREDENTIALS_PATH}')
    print('  修改密码后凭据文件会自动删除 / The file is removed once the password is changed.')
    return 0
