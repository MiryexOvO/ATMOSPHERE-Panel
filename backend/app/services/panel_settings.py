import json,os
import sqlite3
from contextlib import closing
from ..core.database import connect

DEFAULTS = {'download_source': 'default', 'metrics_interval_seconds': 5,
            'session_hours': 24, 'default_locale': 'zh', 'upload_limit_mb': 500,
            'update_auto_download':False, 'https_enabled':False, 'https_self_signed':True,
            'https_port':8443,'frontend_port':int(os.getenv('ATMOSPHERE_FRONTEND_PORT','5173'))}


def read_settings():
    # 数据库存储设置，重启后仍保留。
    try:
        with closing(connect()) as conn:
            values = {row['key']: json.loads(row['value']) for row in conn.execute('SELECT key,value FROM panel_settings')}
    except sqlite3.OperationalError:
        values = {}
    return {key:values.get(key,value) for key,value in DEFAULTS.items()}


def audit(user_id, action, detail=''):
    with closing(connect()) as conn:
        conn.execute("INSERT INTO audit_log(user_id,action,detail,created_at) VALUES(?,?,?,strftime('%s','now'))", (user_id, action, detail))
        conn.commit()
