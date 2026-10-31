from __future__ import annotations

import asyncio
import os
import shutil
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import AsyncIterator

from ..core.config import JAVA_ROOT, SERVER_ROOT

RUNNING_PROCESSES: dict[str, asyncio.subprocess.Process] = {}


def safe_instance_root(instance_id: str) -> Path:
    if not instance_id or '/' in instance_id or '\\' in instance_id or '..' in instance_id:
        raise ValueError('实例 ID 无效')
    root = (SERVER_ROOT / instance_id).resolve()
    base = SERVER_ROOT.resolve()
    if root == base or base not in root.parents:
        raise ValueError('实例目录路径非法')
    root.mkdir(parents=True, exist_ok=True)
    return root


class BaseProcessManager(ABC):
    @abstractmethod
    async def start(self, instance_id: str, jar_name: str = 'server.jar', memory_mb: int = 4096) -> int: ...

    @abstractmethod
    async def stop(self, instance_id: str) -> None: ...

    @abstractmethod
    async def get_logs(self, instance_id: str) -> AsyncIterator[str]: ...

    @abstractmethod
    async def is_running(self, instance_id: str) -> bool: ...

    @abstractmethod
    async def get_pid(self, instance_id: str) -> int | None: ...


class LinuxSystemdManager(BaseProcessManager):
    async def _systemctl(self, *args: str) -> tuple[int, str]:
        process = await asyncio.create_subprocess_exec('systemctl', *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
        output = await process.stdout.read() if process.stdout else b''
        await process.wait()
        return process.returncode or 0, output.decode(errors='replace').strip()

    async def start(self, instance_id: str, jar_name: str = 'server.jar', memory_mb: int = 4096) -> int:
        code, output = await self._systemctl('enable', '--now', f'mc-{instance_id}')
        if code:
            raise RuntimeError(output or 'systemd 启动失败')
        pid = await self.get_pid(instance_id)
        if pid is None:
            raise RuntimeError('systemd 未返回有效进程 PID')
        return pid

    async def stop(self, instance_id: str) -> None:
        code, output = await self._systemctl('stop', f'mc-{instance_id}')
        if code:
            raise RuntimeError(output or 'systemd 停止失败')

    async def get_pid(self, instance_id: str) -> int | None:
        code, output = await self._systemctl('show', '-p', 'MainPID', '--value', f'mc-{instance_id}')
        if code or not output or output == '0':
            return None
        return int(output)

    async def is_running(self, instance_id: str) -> bool:
        code, _ = await self._systemctl('is-active', '--quiet', f'mc-{instance_id}')
        return code == 0

    async def get_logs(self, instance_id: str) -> AsyncIterator[str]:
        process = await asyncio.create_subprocess_exec('journalctl', '-u', f'mc-{instance_id}', '-n', '50', '-f', '--output=cat', stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
        try:
            while process.stdout and (line := await process.stdout.readline()):
                yield line.decode(errors='replace').rstrip()
        finally:
            process.terminate()
            await process.wait()


class WindowsMacManager(BaseProcessManager):
    async def start(self, instance_id: str, jar_name: str = 'server.jar', memory_mb: int = 4096) -> int:
        root = safe_instance_root(instance_id)
        jar = (root / jar_name).resolve()
        if root not in jar.parents or not jar.is_file():
            raise ValueError('核心文件不存在或路径非法')
        java = shutil.which('java')
        if not java:
            raise RuntimeError('未检测到 Java，请安装 Java 并加入 PATH')
        process = await asyncio.create_subprocess_exec(java, f'-Xmx{memory_mb}M', '-jar', jar.name, 'nogui', cwd=str(root), stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
        RUNNING_PROCESSES[instance_id] = process
        return process.pid

    async def stop(self, instance_id: str) -> None:
        process = RUNNING_PROCESSES.get(instance_id)
        if process is None or process.returncode is not None:
            RUNNING_PROCESSES.pop(instance_id, None)
            return
        if process.stdin:
            process.stdin.write(b'stop\n')
            await process.stdin.drain()
        try:
            await asyncio.wait_for(process.wait(), timeout=10)
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
        RUNNING_PROCESSES.pop(instance_id, None)

    async def is_running(self, instance_id: str) -> bool:
        process = RUNNING_PROCESSES.get(instance_id)
        return process is not None and process.returncode is None

    async def get_pid(self, instance_id: str) -> int | None:
        process = RUNNING_PROCESSES.get(instance_id)
        return process.pid if process and process.returncode is None else None

    async def get_logs(self, instance_id: str) -> AsyncIterator[str]:
        process = RUNNING_PROCESSES.get(instance_id)
        if not process or not process.stdout:
            return
        while process.returncode is None:
            line = await process.stdout.readline()
            if line:
                yield line.decode(errors='replace').rstrip()
            else:
                await asyncio.sleep(0.05)
        RUNNING_PROCESSES.pop(instance_id, None)


def get_process_manager() -> BaseProcessManager:
    return LinuxSystemdManager() if sys.platform.startswith('linux') else WindowsMacManager()
