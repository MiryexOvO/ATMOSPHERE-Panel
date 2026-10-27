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
    conn.commit()
    conn.close()
