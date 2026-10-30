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
    def create_unit(self, instance_id: str, jar_name: str, memory_mb: int = 4096) -> Path:
        unit = self.unit_path(instance_id)
        server_root = SERVER_ROOT / instance_id
        java = JAVA_ROOT / 'bin' / 'java'
        unit.parent.mkdir(parents=True, exist_ok=True)
        unit.write_text(
            '[Unit]\n'
            f'Description=Minecraft server {instance_id}\n'
            'After=network.target\n\n'
            '[Service]\n'
            'Type=simple\n'
            f'WorkingDirectory={server_root}\n'
            f'ExecStart={java} -Xms{memory_mb}M -Xmx{memory_mb}M -jar {server_root / jar_name} nogui\n'
            'Restart=on-failure\n'
            'RestartSec=5\n'
            'User=mc-panel\n\n'
            '[Install]\n'
            'WantedBy=multi-user.target\n', encoding='utf-8'
        )
        return unit

    def deploy(self, instance_id: str, jar_name: str, memory_mb: int = 4096) -> tuple[int, str]:
        self.create_unit(instance_id, jar_name, memory_mb)
        code, output = self.run('daemon-reload')
        if code != 0: return code, output
        return self.run('enable', '--now', f'mc-{instance_id}')

    def remove_unit(self, instance_id: str) -> None:
        self.unit_path(instance_id).unlink(missing_ok=True)

    def run(self, *args: str) -> tuple[int, str]:
        try:
            result=subprocess.run(['systemctl',*args],capture_output=True,text=True,timeout=20,check=False)
            return result.returncode,(result.stdout or result.stderr).strip()
        except (FileNotFoundError,OSError) as exc: return 127,str(exc)
