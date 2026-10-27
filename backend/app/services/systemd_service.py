from __future__ import annotations
from pathlib import Path
from ..core.config import SYSTEMD_DIR, SERVER_ROOT, JAVA_ROOT
import subprocess
import re

INSTANCE_RE = re.compile(r'^[a-z0-9][a-z0-9-]{1,30}$')

class SystemdService:
    def unit_path(self, instance_id: str) -> Path:
        if not INSTANCE_RE.fullmatch(instance_id): raise ValueError('实例 ID 无效')
        return SYSTEMD_DIR / f'mc-{instance_id}.service'
    def run(self, *args: str) -> tuple[int, str]:
        try:
            result=subprocess.run(['systemctl',*args],capture_output=True,text=True,timeout=20,check=False)
            return result.returncode,(result.stdout or result.stderr).strip()
        except (FileNotFoundError,OSError) as exc: return 127,str(exc)
