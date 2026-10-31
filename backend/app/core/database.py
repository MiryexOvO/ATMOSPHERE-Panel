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
    CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, created_at INTEGER NOT NULL);
    CREATE TABLE IF NOT EXISTS sessions(token_hash TEXT PRIMARY KEY, user_id INTEGER NOT NULL, expires_at INTEGER NOT NULL, created_at INTEGER NOT NULL);
    CREATE TABLE IF NOT EXISTS instances(id TEXT PRIMARY KEY, name TEXT NOT NULL, port INTEGER UNIQUE NOT NULL, jar_name TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'stopped', created_at INTEGER NOT NULL, core_candidates TEXT NOT NULL DEFAULT '[]', selected_core TEXT);
    """)
    columns = {row['name'] for row in conn.execute("PRAGMA table_info(instances)").fetchall()}
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
        'jvm_args': "TEXT NOT NULL DEFAULT ''",
        'rcon_enabled': 'INTEGER NOT NULL DEFAULT 1',
        'auto_restart': 'INTEGER NOT NULL DEFAULT 0',
        'ignore_eula': 'INTEGER NOT NULL DEFAULT 0',
    }.items():
        if column not in columns:
            conn.execute(f'ALTER TABLE instances ADD COLUMN {column} {definition}')
    conn.commit()
    conn.close()
