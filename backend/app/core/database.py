from __future__ import annotations
import sqlite3
from .config import DB_PATH

def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db() -> None:
    conn = connect()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS panel_settings(key TEXT PRIMARY KEY,value TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS user_access(user_id INTEGER NOT NULL,instance_id TEXT NOT NULL,permissions TEXT NOT NULL DEFAULT '[]',PRIMARY KEY(user_id,instance_id));
    CREATE TABLE IF NOT EXISTS login_events(id INTEGER PRIMARY KEY,user_id INTEGER,username TEXT NOT NULL,ip TEXT NOT NULL,network TEXT NOT NULL,success INTEGER NOT NULL,unusual INTEGER NOT NULL DEFAULT 0,created_at INTEGER NOT NULL);
    CREATE TABLE IF NOT EXISTS schedules(id INTEGER PRIMARY KEY,name TEXT NOT NULL,instance_id TEXT NOT NULL,cron TEXT NOT NULL,action TEXT NOT NULL,command TEXT NOT NULL DEFAULT '',enabled INTEGER NOT NULL DEFAULT 1,owner_id INTEGER NOT NULL,next_run INTEGER NOT NULL,last_run INTEGER,last_result TEXT NOT NULL DEFAULT '');
    CREATE TABLE IF NOT EXISTS audit_log(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER,action TEXT NOT NULL,detail TEXT NOT NULL,created_at INTEGER NOT NULL);
    CREATE TABLE IF NOT EXISTS deployment_jobs(id TEXT PRIMARY KEY, port INTEGER NOT NULL, status TEXT NOT NULL, error TEXT NOT NULL DEFAULT '', created_at INTEGER NOT NULL);
    CREATE UNIQUE INDEX IF NOT EXISTS deployment_job_port ON deployment_jobs(port) WHERE status='deploying';
    CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, created_at INTEGER NOT NULL);
    CREATE TABLE IF NOT EXISTS sessions(token_hash TEXT PRIMARY KEY, user_id INTEGER NOT NULL, expires_at INTEGER NOT NULL, created_at INTEGER NOT NULL);
    CREATE TABLE IF NOT EXISTS instances(id TEXT PRIMARY KEY, name TEXT NOT NULL, port INTEGER UNIQUE NOT NULL, jar_name TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'stopped', created_at INTEGER NOT NULL, core_candidates TEXT NOT NULL DEFAULT '[]', selected_core TEXT);
    """)
    # 后端重启后释放中断任务，保留失败原因。
    conn.execute("UPDATE deployment_jobs SET status='error',error='后端重启，部署中断' WHERE status='deploying'")
    columns = {row['name'] for row in conn.execute("PRAGMA table_info(instances)").fetchall()}
    # 基岩版独立预留 IPv6 端口，避免多实例互相占用。
    if 'secondary_port' not in columns: conn.execute('ALTER TABLE instances ADD COLUMN secondary_port INTEGER')
    if 'secondary_port' not in {row['name'] for row in conn.execute('PRAGMA table_info(deployment_jobs)')}:
        conn.execute('ALTER TABLE deployment_jobs ADD COLUMN secondary_port INTEGER')
    # 旧账户保留管理员权限，新账户可配置角色。
    user_columns = {row['name'] for row in conn.execute('PRAGMA table_info(users)')}
    for column, definition in {'role': "TEXT NOT NULL DEFAULT 'admin'", 'enabled': 'INTEGER NOT NULL DEFAULT 1', 'totp_secret': "TEXT NOT NULL DEFAULT ''", 'totp_pending': "TEXT NOT NULL DEFAULT ''", 'last_totp_step': 'INTEGER NOT NULL DEFAULT 0', 'last_login': 'INTEGER', 'nickname': "TEXT NOT NULL DEFAULT ''"}.items():
        if column not in user_columns:
            conn.execute(f'ALTER TABLE users ADD COLUMN {column} {definition}')
    if 'rcon_host' not in columns:
        conn.execute("ALTER TABLE instances ADD COLUMN rcon_host TEXT")
    if 'rcon_port' not in columns:
        conn.execute("ALTER TABLE instances ADD COLUMN rcon_port INTEGER")
    if 'rcon_password_hash' not in columns:
        conn.execute("ALTER TABLE instances ADD COLUMN rcon_password_hash TEXT")
    if 'rcon_password' not in columns:
        conn.execute("ALTER TABLE instances ADD COLUMN rcon_password TEXT")
    if 'memory_mb' not in columns:
        conn.execute("ALTER TABLE instances ADD COLUMN memory_mb INTEGER NOT NULL DEFAULT 4096")
    for column, definition in {
        'java_version': "TEXT NOT NULL DEFAULT '21'",
        'java_path': "TEXT NOT NULL DEFAULT ''",
        'jvm_args': "TEXT NOT NULL DEFAULT ''",
        'rcon_enabled': 'INTEGER NOT NULL DEFAULT 1',
        'auto_restart': 'INTEGER NOT NULL DEFAULT 0',
        'ignore_eula': 'INTEGER NOT NULL DEFAULT 0',
    }.items():
        if column not in columns:
            conn.execute(f'ALTER TABLE instances ADD COLUMN {column} {definition}')
    conn.commit()
    conn.close()
