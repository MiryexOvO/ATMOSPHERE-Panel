from __future__ import annotations

import os
import subprocess
from pathlib import Path

from ..core.config import JAVA_ROOT, SERVER_ROOT, SYSTEMD_DIR

INSTANCE_RE = __import__('re').compile(r'^[a-z0-9][a-z0-9-]{1,30}$')

def run_systemctl(*args: str) -> tuple[int, str]:
    try:
        result = subprocess.run(['systemctl', *args], capture_output=True, text=True, timeout=20, check=False)
        return result.returncode, (result.stdout or result.stderr).strip()
    except (FileNotFoundError, OSError) as exc:
        return 127, str(exc)


def unit_path(instance_id: str) -> Path:
    if not INSTANCE_RE.fullmatch(instance_id): raise ValueError('实例 ID 无效')
    return SYSTEMD_DIR / f'mc-{instance_id}.service'


def write_unit(instance_id: str, selected_core: str, java_version: str = '17', memory: str = '4G') -> Path:
    root = (SERVER_ROOT / instance_id).resolve(); core = (root / selected_core).resolve()
    if root not in core.parents or not core.is_file(): raise ValueError('核心文件不存在或路径非法')
    java = (JAVA_ROOT / java_version / 'bin' / 'java').resolve()
    if not java.is_file(): java = Path('/usr/bin/java')
    unit = f'''[Unit]\nDescription=Atmosphere Minecraft Server {instance_id}\nAfter=network.target\n\n[Service]\nType=simple\nUser=mcserver\nWorkingDirectory={root}\nExecStart={java} -Xms{memory} -Xmx{memory} -jar {core} nogui\nRestart=always\nRestartSec=10\nMemoryMax={memory}\nStandardOutput=journal\nStandardError=journal\n\n[Install]\nWantedBy=multi-user.target\n'''
    path = unit_path(instance_id); path.parent.mkdir(parents=True, exist_ok=True); path.write_text(unit, encoding='utf-8'); return path


def prepare_mcdr_environment(root: Path, system_python: str) -> str:
    venv = (root / '.venv').resolve()
    if root not in venv.parents:
        raise ValueError('MCDR 虚拟环境路径非法')
    subprocess.run([system_python, '-m', 'venv', str(venv)], check=True, capture_output=True, text=True, timeout=120)
    python_path = venv / ('Scripts' if os.name == 'nt' else 'bin') / ('python.exe' if os.name == 'nt' else 'python')
    if not python_path.is_file():
        raise RuntimeError('Python 虚拟环境创建失败')
    subprocess.run([str(python_path), '-m', 'pip', 'install', '--disable-pip-version-check', 'mcdreforged'], check=True, capture_output=True, text=True, timeout=180)
    return str(python_path)


def write_mcdr_unit(instance_id: str, python: str, memory: str = '4G') -> Path:
    root = (SERVER_ROOT / instance_id).resolve()
    script = (root / 'start_mcdr.py').resolve()
    if root not in script.parents or not script.is_file():
        raise ValueError('MCDR 启动脚本不存在或路径非法')
    unit = f'''[Unit]\nDescription=Atmosphere MCDR Server {instance_id}\nAfter=network.target\n\n[Service]\nType=simple\nUser=mcserver\nWorkingDirectory={root}\nExecStart={python} {script}\nRestart=always\nRestartSec=10\nMemoryMax={memory}\nStandardOutput=journal\nStandardError=journal\n\n[Install]\nWantedBy=multi-user.target\n'''
    path = unit_path(instance_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(unit, encoding='utf-8')
    return path


