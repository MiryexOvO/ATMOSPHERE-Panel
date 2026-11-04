"""Launch the frozen binary with isolated data and verify web/API readiness."""
import os
from pathlib import Path
import socket
import subprocess
import tempfile
import time
from urllib.request import urlopen
from urllib.error import URLError

root = Path(__file__).resolve().parents[1]
executable = root / 'dist' / ('atmosphere-panel.exe' if os.name == 'nt' else 'atmosphere-panel')
with tempfile.TemporaryDirectory() as directory:
    data = Path(directory)
    with socket.socket() as probe:
        probe.bind(('127.0.0.1', 0))
        port = probe.getsockname()[1]
    env = dict(os.environ, ATMOSPHERE_DATA_DIR=str(data), ATMOSPHERE_DB_PATH=str(data / 'panel.sqlite3'))
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
        finally:
            process.terminate()
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
