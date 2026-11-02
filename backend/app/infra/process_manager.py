from __future__ import annotations

import asyncio
import os
import shutil
import sys
import shlex
import re
import logging
import time
from ..services.runtime_modes import runtime_mode,mcdr_command
from contextlib import closing
from ..core.database import connect
from abc import ABC, abstractmethod
from pathlib import Path
from typing import AsyncIterator

from ..core.config import JAVA_ROOT, SERVER_ROOT

RUNNING_PROCESSES: dict[str, asyncio.subprocess.Process] = {}
PROCESS_WATCHERS: dict[str, asyncio.Task] = {}
EXPECTED_STOPS: set[str] = set()
PROCESS_LOCKS: dict[str, asyncio.Lock] = {}
RESTART_COUNTS: dict[str, int] = {}
logger = logging.getLogger(__name__)


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
    async def start(self, instance_id: str, jar_name: str = 'server.jar', memory_mb: int = 4096, _automatic=False) -> int:
        # 同一实例串行操作，避免重复开服。
        async with PROCESS_LOCKS.setdefault(instance_id, asyncio.Lock()):
            if not _automatic:
                RESTART_COUNTS[instance_id] = 0
            return await self._start(instance_id, jar_name, memory_mb)

    async def _start(self, instance_id, jar_name, memory_mb):
        existing_pid = await self.get_pid(instance_id)
        root = safe_instance_root(instance_id)
        with closing(connect()) as conn:
            row = conn.execute('SELECT * FROM instances WHERE id=?', (instance_id,)).fetchone()
        options = dict(row) if row else {}
        jar_name = options.get('selected_core') or options.get('jar_name') or jar_name
        memory_mb = options.get('memory_mb', memory_mb)
        mode=runtime_mode(root)
        jar = (root / jar_name.removeprefix('@')).resolve()
        if root not in jar.parents or not jar.is_file():
            raise ValueError(f'核心文件不存在或路径非法: {jar_name}')
        if mode=='bedrock':
            if existing_pid is not None: return existing_pid
            environment={**os.environ,'LD_LIBRARY_PATH':str(root)+os.pathsep+os.environ.get('LD_LIBRARY_PATH','')}
            return await self._launch(instance_id,root,[str(jar)],environment)
        from ..services.core_package import is_installer
        installer = not jar_name.startswith('@') and is_installer(jar)
        if existing_pid is not None and not installer:
            return existing_pid
        candidates = [options.get('java_path')] if options.get('java_path') else []
        # 仅使用符合所选主版本的 Java。
        if not candidates:
            version = options.get('java_version', '21')
            for env in (f'JAVA_HOME_{version}', f'JAVA{version}_HOME', 'JAVA_HOME'):
                if os.environ.get(env):
                    candidates.append(str(Path(os.environ[env]) / 'bin' / ('java.exe' if os.name == 'nt' else 'java')))
            candidates.extend(str(path) for path in JAVA_ROOT.glob('**/bin/java.exe' if os.name == 'nt' else '**/bin/java'))
            if os.name == 'nt':
                candidates.extend(str(path) for path in (Path(os.environ.get('ProgramFiles', 'C:/Program Files')) / 'Java').glob('*/bin/java.exe'))
            candidates.append(shutil.which('java'))
        java = None
        for candidate in dict.fromkeys(filter(None, candidates)):
            try:
                check = await asyncio.create_subprocess_exec(candidate, '-version', stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
                try:
                    output, _ = await asyncio.wait_for(check.communicate(), 5)
                except asyncio.TimeoutError:
                    check.kill()
                    await check.wait()
                    continue
                match = re.search(r'version "(?:1\.)?(\d+)', output.decode(errors='replace'))
                if check.returncode == 0 and match and match[1] == str(options.get('java_version', '21')):
                    java = candidate
                    break
            except OSError:
                continue
        if not java:
            raise RuntimeError(f'未找到 Java {options.get("java_version", "21")}，请安装对应版本或在实例设置中填写 Java 可执行文件路径')
        if installer:
            # 只结束已确认的安装器进程，不结束游戏服务端。
            if existing_pid is not None:
                import psutil
                old = psutil.Process(existing_pid)
                if Path(old.cwd()).resolve() != root: raise RuntimeError('安装器进程目录不匹配')
                EXPECTED_STOPS.add(instance_id)
                old.terminate()
                await asyncio.to_thread(old.wait, 10)
            from ..routers.deployments import _install_forge
            async def report_install(progress, message):
                with (root / 'panel-console.log').open('a', encoding='utf-8') as output:
                    output.write(f'[INSTALL {progress}%] {message}\n')
            jar_name = await _install_forge(root, report_install, str(jar.relative_to(root)), java)
            with closing(connect()) as conn:
                conn.execute('UPDATE instances SET jar_name=?,selected_core=? WHERE id=?',(jar_name,jar_name,instance_id));conn.commit()
            jar = (root / jar_name.removeprefix('@')).resolve()
        jvm_args = shlex.split(options.get('jvm_args') or '', posix=True)
        if any(arg in {'-jar', '-cp', '-classpath', '--class-path'} or arg.startswith(('@', '-Xmx', '-Xms')) for arg in jvm_args):
            raise ValueError('JVM 参数不能覆盖启动目标或内存，请使用对应设置项')
        launch_args = [jar_name] if jar_name.startswith('@') else ['-jar', str(jar.relative_to(root))]
        runtime_temp = root / '.runtime-tmp'
        runtime_temp.mkdir(exist_ok=True)
        EXPECTED_STOPS.discard(instance_id)
        command=[java,f'-Xmx{memory_mb}M',f'-Djava.io.tmpdir={runtime_temp}','-Dfile.encoding=UTF-8',*jvm_args,*launch_args,'nogui']
        if mode=='mcdr': command=await mcdr_command(root,command)
        return await self._launch(instance_id,root,command,{**os.environ,'PYTHONIOENCODING':'utf-8','PYTHONUTF8':'1'} if mode=='mcdr' else None)

    async def _launch(self,instance_id,root,command,environment=None):
        # 三种运行模式统一接管标准输入、日志与退出监测。
        EXPECTED_STOPS.discard(instance_id)
        process = await asyncio.create_subprocess_exec(*command,env=environment,cwd=str(root),stdin=asyncio.subprocess.PIPE,stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.STDOUT,limit=1024*1024)
        RUNNING_PROCESSES[instance_id] = process
        PROCESS_WATCHERS[instance_id] = asyncio.create_task(self._watch(instance_id, process, root))
        await asyncio.sleep(0.75)
        if process.returncode is not None:
            raise RuntimeError(f'服务端启动后退出，退出码 {process.returncode}，请查看控制台日志')
        return process.pid

    async def _watch(self, instance_id, process, root):
        # 单独消费 stdout，所有控制台从日志文件订阅。
        started_at = time.monotonic()
        with (root / 'panel-console.log').open('a', encoding='utf-8', buffering=1) as output:
            output.write('\n[ATMOSPHERE] Starting server process\n')
            while line := await process.stdout.readline():
                output.write(line.decode(errors='replace'))
        code = await process.wait()
        if RUNNING_PROCESSES.get(instance_id) is not process:
            return
        with closing(connect()) as conn:
            conn.execute('UPDATE instances SET status=? WHERE id=?', ('stopped' if code == 0 or instance_id in EXPECTED_STOPS else 'error', instance_id))
            conn.commit()
            row = conn.execute('SELECT auto_restart FROM instances WHERE id=?', (instance_id,)).fetchone()
        if code != 0 and instance_id not in EXPECTED_STOPS and row and row['auto_restart']:
            if time.monotonic() - started_at >= 60:
                RESTART_COUNTS[instance_id] = 0
            RESTART_COUNTS[instance_id] = RESTART_COUNTS.get(instance_id, 0) + 1
            if RESTART_COUNTS[instance_id] > 3:
                logger.error('实例连续异常退出，已停止自动重启: %s', instance_id)
                return
            await asyncio.sleep(5)
            if instance_id not in EXPECTED_STOPS:
                try:
                    await self.start(instance_id, _automatic=True)
                    with closing(connect()) as conn:
                        conn.execute('UPDATE instances SET status=? WHERE id=?', ('running', instance_id))
                        conn.commit()
                except (OSError, RuntimeError, ValueError):
                    logger.exception('实例自动重启失败: %s', instance_id)

    async def stop(self, instance_id: str) -> None:
        async with PROCESS_LOCKS.setdefault(instance_id, asyncio.Lock()):
            await self._stop(instance_id)

    async def _stop(self, instance_id):
        EXPECTED_STOPS.add(instance_id)
        process = RUNNING_PROCESSES.get(instance_id)
        if process is None or process.returncode is not None:
            RUNNING_PROCESSES.pop(instance_id, None)
            pid = await self.get_pid(instance_id)
            if pid is None:
                return
            with closing(connect()) as conn:
                row = conn.execute('SELECT rcon_host,rcon_port,rcon_password FROM instances WHERE id=?', (instance_id,)).fetchone()
            if not row or not row['rcon_password']:
                raise RuntimeError('此实例由上次后端启动，请在服务端控制台执行 stop 后重试')
            from ..services.rcon_service import execute_rcon_command
            await execute_rcon_command(row['rcon_host'] or '127.0.0.1', row['rcon_port'] or 25575, row['rcon_password'], 'stop')
            for _ in range(60):
                if await self.get_pid(instance_id) is None:
                    return
                await asyncio.sleep(0.5)
            raise RuntimeError('实例仍在保存世界，请等待关闭后重试')
        if process.stdin:
            try:
                stop='!!MCDR server stop_exit' if runtime_mode(safe_instance_root(instance_id))=='mcdr' else 'stop'
                process.stdin.write((stop+'\n').encode())
                await process.stdin.drain()
            except (BrokenPipeError, ConnectionResetError):
                pass
        try:
            await asyncio.wait_for(process.wait(), timeout=60)
        except asyncio.TimeoutError:
            raise RuntimeError('实例仍未退出，请检查控制台日志；为保护世界数据未强制结束进程')
        RUNNING_PROCESSES.pop(instance_id, None)

    async def is_running(self, instance_id: str) -> bool:
        return await self.get_pid(instance_id) is not None

    async def get_pid(self, instance_id: str) -> int | None:
        process = RUNNING_PROCESSES.get(instance_id)
        if process and process.returncode is None:
            return process.pid
        # Reconnect to a Java server left running across a backend restart.
        try:
            import psutil
            root = (SERVER_ROOT / instance_id).resolve()
            mode=runtime_mode(root)
            candidates = []
            for process in psutil.process_iter(['pid', 'name']):
                name=(process.info['name'] or '').lower()
                accepted=name in {'java','java.exe','javaw.exe'} if mode=='java' else name in {'bedrock_server','bedrock_server.exe'} if mode=='bedrock' else name.startswith('python')
                if not accepted:
                    continue
                try:
                    if Path(process.cwd()).resolve() == root and process.is_running():
                        candidates.append(process)
                except (psutil.NoSuchProcess, psutil.AccessDenied, OSError):
                    continue
            if candidates:
                return candidates[-1].pid
        except ImportError:
            pass
        return None

    async def get_logs(self, instance_id: str) -> AsyncIterator[str]:
        root = safe_instance_root(instance_id)
        # 回放最近日志，再增量跟随；读者互不争抢。
        path = root / 'panel-console.log'
        if not path.exists() or (instance_id not in RUNNING_PROCESSES and await self.is_running(instance_id)):
            path = root / 'logs' / 'latest.log'
        position = 0
        if path.exists():
            with path.open('rb') as stream:
                stream.seek(0, 2)
                end = stream.tell()
                stream.seek(max(0, end - 128 * 1024))
                recent = stream.read().decode(errors='replace').splitlines()
                for line in recent[-200:]:
                    yield line
                position = stream.tell()
        idle = 0
        while True:
            preferred = root / ('panel-console.log' if instance_id in RUNNING_PROCESSES else 'logs/latest.log')
            if preferred.exists() and preferred != path:
                path, position = preferred, 0
            if path.exists():
                with path.open('rb') as stream:
                    if path.stat().st_size < position:
                        position = 0
                    stream.seek(position)
                    for line in stream:
                        yield line.decode(errors='replace').rstrip()
                    position = stream.tell()
            idle += 1
            if idle % 20 == 0:
                yield ''
            await asyncio.sleep(0.5)


def get_process_manager() -> BaseProcessManager:
    # 整个面板由 systemd 托管，实例直接运行；旧部署可显式使用单服单元。
    return LinuxSystemdManager() if sys.platform.startswith('linux') and os.getenv('ATMOSPHERE_INSTANCE_DRIVER')=='systemd' else WindowsMacManager()
