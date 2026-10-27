from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / 'panel.sqlite3'
SERVER_ROOT = Path('/opt/mc-panel/servers')
SYSTEMD_DIR = Path('/etc/systemd/system')
JAVA_ROOT = Path('/opt/mc-panel/java')
SESSION_HOURS = 24
MAX_PACKAGE_BYTES = 500 * 1024 * 1024
MAX_JAR_BYTES = 300 * 1024 * 1024
