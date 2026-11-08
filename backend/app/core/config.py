import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE_DIR = Path(os.getenv('ATMOSPHERE_DATA_DIR') or (Path.cwd() / 'data' if sys.platform.startswith('win') else Path('/opt/mc-panel')))
DB_PATH = Path(os.getenv('ATMOSPHERE_DB_PATH') or ROOT / 'panel.sqlite3')
# 初始密码只以哈希入库，明文只在首次生成时写入这个 0600 文件。
# 文件存在即代表密码仍是初始值；用户修改密码后会自动删除。
CREDENTIALS_PATH = BASE_DIR / 'initial-password.txt'
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
