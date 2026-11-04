"""Launch the frozen binary with isolated data and verify web/API readiness."""
import os
import re
from pathlib import Path
import socket
import subprocess
import tempfile
import time
from urllib.request import build_opener, ProxyHandler
from urllib.error import URLError

urlopen = build_opener(ProxyHandler({})).open

root = Path(__file__).resolve().parents[1]
executable = root / 'dist' / ('atmosphere-panel.exe' if os.name == 'nt' else 'atmosphere-panel')
with tempfile.TemporaryDirectory() as directory:
    data = Path(directory)
    with socket.socket() as probe:
        probe.bind(('127.0.0.1', 0))
        port = probe.getsockname()[1]
    env = dict(os.environ, TMP=str(data), TEMP=str(data), TMPDIR=str(data), ATMOSPHERE_DATA_DIR=str(data), ATMOSPHERE_DB_PATH=str(data / 'panel.sqlite3'))
    with (data / 'startup.log').open('wb') as log:
        process = subprocess.Popen([str(executable), '--host', '127.0.0.1', '--port', str(port)], env=env, stdout=log, stderr=log)
        try:
            for attempt in range(90):
                if process.poll() is not None:
                    raise RuntimeError(f'Frozen binary exited with {process.returncode}')
                try:
                    with urlopen(f'http://127.0.0.1:{port}/api/health', timeout=2) as response:
                        assert response.status == 200
                    with urlopen(f'http://127.0.0.1:{port}/instances/smoke', timeout=2) as response:
                        assert response.status == 200 and b'<html' in response.read().lower()
                    print('Frozen binary web and API smoke check passed')
                    break
                except URLError:
                    time.sleep(1)
            else:
                raise RuntimeError('Frozen binary readiness timed out')
        except BaseException:
            # Flush the child output before the temporary directory is removed.
            log.flush()
            diagnostic = (data / 'startup.log').read_text(encoding='utf-8', errors='replace')
            diagnostic = re.sub(r'(?im)^.*(?:password|瀵嗙爜).*$', '[credential line redacted]', diagnostic)
            destination = root / 'build' / 'diagnostics'
            destination.mkdir(parents=True, exist_ok=True)
            (destination / 'startup.log').write_text(diagnostic, encoding='utf-8')
            print('Frozen startup diagnostics:\n' + diagnostic[-16000:], flush=True)
            raise
        finally:
            # Windows onefile bootloader has a separate application child.
            if os.name == 'nt' and process.poll() is None:
                subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
            elif process.poll() is None:
                process.terminate()
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            if os.name == 'nt':
                time.sleep(1)  # Allow Windows to release mapped DLLs before cleanup.
