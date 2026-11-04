"""Build on the target OS: python scripts/build-release.py --version v0.2.0"""
import argparse
import hashlib
import platform
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

def run(*args, cwd=ROOT):
    subprocess.run(args, cwd=cwd, check=True)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', required=True)
    args = parser.parse_args()
    import re
    if not re.fullmatch(r'v?\d+\.\d+\.\d+(?:[-.][A-Za-z0-9.-]+)?', args.version):
        parser.error('Expected a semantic version')
    system = {'Windows': 'win', 'Linux': 'linux', 'Darwin': 'macos'}[platform.system()]
    arch = {'AMD64': 'x64', 'x86_64': 'x64', 'arm64': 'arm64', 'aarch64': 'arm64'}[platform.machine()]
    pnpm = shutil.which('pnpm')
    if not pnpm:
        raise RuntimeError('Install pnpm matching frontend/package.json first')
    run(pnpm, 'install', '--frozen-lockfile', cwd=ROOT / 'frontend')
    run(pnpm, 'exec', 'nuxt', 'generate', cwd=ROOT / 'frontend')
    web = ROOT / 'frontend/.output/public'
    if not (web / 'index.html').is_file():
        raise RuntimeError('Static frontend index.html missing')
    run(sys.executable, '-m', 'PyInstaller', '--noconfirm', '--clean', '--onefile',
        '--name', 'atmosphere-panel', '--paths', str(ROOT / 'backend'),
        '--collect-submodules', 'app', '--collect-submodules', 'uvicorn',
        '--collect-submodules', 'websockets', '--collect-submodules', 'httptools',
        '--add-data', str(web) + ':web', str(ROOT / 'scripts/frozen_entry.py'))
    output = ROOT / 'release'
    output.mkdir(exist_ok=True)
    name = f'atmosphere-panel-{args.version}-{system}-{arch}'
    import tempfile
    with tempfile.TemporaryDirectory() as temporary:
        stage = Path(temporary)
        executable = 'atmosphere-panel' + ('.exe' if system == 'win' else '')
        shutil.copy2(ROOT / 'dist' / executable, stage / executable)
        shutil.copy2(ROOT / 'LICENSE', stage / 'LICENSE')
        archive = Path(shutil.make_archive(str(output / name), 'zip' if system == 'win' else 'gztar', stage))
    digest = hashlib.file_digest(archive.open('rb'), 'sha256').hexdigest()
    archive.with_name(archive.name + '.sha256').write_text(f'{digest}  {archive.name}\n')
    print(f'{archive.name}: {archive.stat().st_size / 1024 / 1024:.2f} MiB')

if __name__ == '__main__':
    main()
