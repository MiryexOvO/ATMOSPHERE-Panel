import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE_DIR = Path.cwd() / 'data' if sys.platform.startswith('win') else Path('/opt/mc-panel')
DB_PATH = ROOT / 'panel.sqlite3'
SERVER_ROOT = BASE_DIR / 'servers'
BACKUP_ROOT = BASE_DIR / 'backups'
SYSTEMD_DIR = Path.cwd() / 'data' / 'systemd' if sys.platform.startswith('win') else Path('/etc/systemd/system')
JAVA_ROOT = BASE_DIR / 'java'

def ensure_data_dirs() -> None:
    try:
        for directory in (BASE_DIR, SERVER_ROOT, BACKUP_ROOT):
            os.makedirs(directory, exist_ok=True)
    except PermissionError as exc:
        raise RuntimeError(f'数据目录无写入权限，请检查路径: {directory}') from exc


ensure_data_dirs()
SESSION_HOURS = 24
MAX_PACKAGE_BYTES = 500 * 1024 * 1024
MAX_JAR_BYTES = 300 * 1024 * 1024
