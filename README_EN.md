<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="header/header-dark-en.png">
    <source media="(prefers-color-scheme: light)" srcset="header/header-light-en.png">
    <img src="header/header-dark-en.png" width="700" alt="Banner">
  </picture>
</p>

<p align="center">
  <a href="https://developer.mozilla.org/en-US/docs/Web/HTML" target="_blank"><img src="https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white" alt="HTML5"/></a>
  <a href="https://vuejs.org/" target="_blank"><img src="https://img.shields.io/badge/Vue.js-4FC08D?style=for-the-badge&logo=vuedotjs&logoColor=white" alt="Vue.js"/></a>
  <a href="https://tailwindcss.com/" target="_blank"><img src="https://img.shields.io/badge/Tailwind_CSS-38BDF8?style=for-the-badge&logo=tailwindcss&logoColor=white" alt="Tailwind CSS"/></a>
  <a href="https://nuxt.com/" target="_blank"><img src="https://img.shields.io/badge/Nuxt.js-00DC82?style=for-the-badge&logo=nuxtdotjs&logoColor=white" alt="Nuxt.js"/></a>
  <a href="https://www.typescriptlang.org/" target="_blank"><img src="https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white" alt="TypeScript"/></a>
  <a href="https://www.python.org/" target="_blank"><img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/></a>
  <a href="https://fastapi.tiangolo.com/" target="_blank"><img src="https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI"/></a>
  <a href="https://www.sqlite.org/" target="_blank"><img src="https://img.shields.io/badge/SQLite-07405E?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLite"/></a>
  <a href="https://github.com/pyca/bcrypt" target="_blank"><img src="https://img.shields.io/badge/Bcrypt-000000?style=for-the-badge&logo=security&logoColor=white" alt="bcrypt"/></a>
  <a href="https://opensource.org/licenses/MIT" target="_blank"><img src="https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge" alt="MIT License"></a>
</p>

<p align="center">
  English | <a href="./README.md">简体中文</a> | <a href="README_JP.md">日本語</a>
</p>

ATMOSPHERE-PANEL is a web-based Minecraft server management panel. Through an authentication-protected interface, you can register server instances, select server cores and versions, and let the backend API handle deployment and runtime management.

The project consists of two parts:

- `frontend/` — Nuxt-based web interface
- `backend/` — FastAPI service with SQLite storage and deployment API

## Contents

- [Features](#features)
- [Standalone (Single-Process Deployment)](#standalone)
- [Getting the Source](#source)
- [Frontend Development](#frontend-dev)
- [Backend Development](#backend-dev)
- [Service Management](#service-management)
- [Development Checks](#dev-checks)
- [Build & Release (Maintainers)](#maintainer-build)
- [License](#license)
- [Maintenance & Support](#support)

<a id="features"></a>

## Features

- Secure password hashing and session-cookie authentication
- Instance ID, port and runtime status management
- Java Edition, Bedrock Edition and MCDR core/version selection
- `.zip` / `.tar.gz` server core and Modpack uploads with path-traversal and dangerous-file checks during extraction
- Java version and JVM memory settings during deployment
- Official resource references and mirror settings
- Local data storage based on SQLite

<a id="standalone"></a>

## Standalone (Single-Process Deployment)

> - **Zero dependencies**: the release bundle includes the web interface and a standalone Python runtime; no separate Node.js, Python or Nginx deployment is required.
> - **Single-port access**: one process and one port serve the entire panel.
> - **External dependencies**: game/management runtimes such as Java, BDS and MCDR are configured per instance and are not bundled with the panel download.

### Linux / systemd

```bash
# Enable strict mode
bash -c 'set -euo pipefail
# Create a secure temporary file
installer=$(mktemp -t atmosphere-install.XXXXXXXX.sh)
cleanup() { rm -f -- "$installer"; }
# Remove the temporary script on success or failure
trap cleanup EXIT
# Download the official binary installer (install-release.sh)
curl --proto "=https" --tlsv1.2 --fail --show-error --location \
  --retry 3 --connect-timeout 15 --max-time 120 \
  https://raw.githubusercontent.com/MiryexOvO/ATMOSPHERE-Panel/main/scripts/install-release.sh \
  --output "$installer"
# Run the installer as root, passing the trailing arguments through
sudo bash "$installer" "$@"' -- --yes --port 27777
```

Default entry: `http://<server-address>:27777`

| Parameter | Description |
| --- | --- |
| `--yes --port 27777` | Non-interactive install with the specified entry port |
| `--version v0.3.0` | Pin a release version |
| `--dir /opt/atmosphere-panel` | Custom program directory (default; must be under `/opt`) |
| `--plan --no-color` | Preview the installation plan only |

The installer downloads the matching architecture bundle from GitHub Releases, verifies its SHA256, extracts it, registers the `atmosphere-panel` service and checks the web page and API. `curl`, `tar` and `sha256sum` must be installed. Current builds cover Linux x64, Windows x64 and macOS arm64; other architectures must be built locally.

**First use**

- The initial password only appears in the first-start logs: `sudo journalctl -u atmosphere-panel -f`
- Data is stored in `/opt/mc-panel`; updates preserve it — back up before upgrading
- The installer supports fresh installs and directories created by this installer
- Legacy source installs must be backed up, have their database migrated, and have the old frontend and Nginx services stopped
- The panel runs as root because of the existing systemd instance management; game instances use the `mc-panel` account
- Only published Releases can be installed; drafts and failed Actions never become latest

Common commands:

```bash
# Follow panel logs (the initial password appears here too)
sudo journalctl -u atmosphere-panel -f
# Restart the panel service
sudo systemctl restart atmosphere-panel
```

### Windows / macOS

First download the matching platform archive from [Releases](https://github.com/MiryexOvO/ATMOSPHERE-Panel/releases) and extract it:

```powershell
# Windows: run in a terminal after extracting
.\atmosphere-panel.exe --port 27777
```

```bash
# macOS: make it executable, then start
chmod +x ./atmosphere-panel
./atmosphere-panel --port 27777
```

Open `http://127.0.0.1:27777`. Data is stored in `data/` next to the executable by default; place it in a writable directory. Use `ATMOSPHERE_DATA_DIR` and `ATMOSPHERE_DB_PATH` to customize. The macOS build is not yet signed or notarized.

### Installer Notes

- `scripts/install-release.sh`: the binary installer — downloads the release, verifies SHA256, extracts it, registers systemd and checks the web/API
- `install.sh`: compatibility entry point that delegates to `install-release.sh` by default; only `--from-source` enters the legacy source install
- The command above fetches `install-release.sh` directly, saving one network hop and requiring no source clone or local build

<a id="source"></a>

## Getting the Source

```bash
# Clone the source and enter the project directory
git clone https://github.com/MiryexOvO/ATMOSPHERE-Panel.git
cd ATMOSPHERE-Panel
```

Development ports: Web `5173`, backend API `27777`. Nuxt uses client-side rendering and proxies `/api` to FastAPI.

<a id="frontend-dev"></a>

## Frontend Development (Nuxt 4.6.2)

```bash
# Enter the frontend directory
cd frontend
# Install dependencies
pnpm install
# Development server
pnpm dev
# When developing on a server (expose to the network)
pnpm dev --host
# Production build
pnpm build
# Preview the production build
pnpm preview
```

Visit `http://127.0.0.1:5173`. On first startup, the terminal prints the 20-character initial password only once.

<a id="backend-dev"></a>

## Backend Development (FastAPI)

### Linux / macOS

```bash
# Enter the backend directory
cd backend
# Create a virtual environment
python3 -m venv .venv
# Activate the virtual environment
source .venv/bin/activate
# Install Python dependencies
pip install -r requirements.txt
# Set the data directory and start the development server
export ATMOSPHERE_DATA_DIR="$PWD/data"
python -m app.launcher --host 0.0.0.0 --port 27777
```

> Make sure Python 3.11 or newer is installed.

### Windows

```powershell
# Enter the backend directory
cd backend
# Allow script execution for the current session only, avoiding permission errors
Set-ExecutionPolicy -Scope Process Bypass
# Run the Windows startup script provided by the project
.\run_windows.ps1
```

> On Windows use `.venv\Scripts\python.exe`; do not run `.venv/bin/activate`.
>
> If the system pip for Python 3.14 is broken, use Python 3.12 or 3.13 to create the virtual environment.

<a id="service-management"></a>

## Service Management

Available after a source install registers the systemd services:

```bash
# Check service status
sudo atmosphere status
# Follow backend logs
sudo atmosphere logs
# Restart the panel service
sudo atmosphere restart
# Stop the panel service
sudo atmosphere stop
```

<a id="dev-checks"></a>

## Development Checks

```bash
# Frontend production build check
cd frontend && npm run build
# Backend Python syntax check
cd ../backend && find app -name "*.py" -print0 | xargs -0 -n1 python3 -m py_compile
```

<a id="maintainer-build"></a>

## Build & Release (Maintainers)

Install Python 3.12, Node.js 24 and the pnpm version specified by the project on the target system, then run:

```bash
# Install backend dependencies and PyInstaller
python -m pip install -r backend/requirements.txt pyinstaller==6.11.1
# Build the platform release (example version v0.2.0)
python scripts/build-release.py --version v0.2.0
# Run a startup smoke test on the generated release
python scripts/smoke-release.py
```

- Output: platform archives and SHA256 files under `release/`; the script prints their actual size
- Only runtime essentials are packaged; `node_modules`, source databases, Java and server data are excluded
- The single-file executable extracts its runtime on first start

Release flow:

1. Push a `v*` tag to trigger the three-platform build
2. On success, a **draft Release** is created automatically
3. Review the assets, platform results and release notes, then publish manually so the installer can read latest
4. Manual Actions runs only produce build artifacts; tags are not pushed and Releases are not published automatically

<a id="license"></a>

## License

This project is licensed under the [MIT License](LICENSE)

<a id="support"></a>

## Maintenance & Support

Maintained by [Miryex](https://www.astrelia7.com)
