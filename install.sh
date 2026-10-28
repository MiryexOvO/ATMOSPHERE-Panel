#!/usr/bin/env bash
set -Eeuo pipefail

RESET="\033[0m"; GOLD="\033[38;5;222m"; CYAN="\033[36m"; GREEN="\033[32m"; RED="\033[31m"
REPO_URL="https://github.com/MiryexOvO/ATMOSPHERE-Panel.git"
DEFAULT_PATH="/opt/atmosphere-panel"; DEFAULT_PORT="27777"; SERVICE_NAME="atmosphere-panel.service"

info(){ printf "  %b»%b %s\n" "$CYAN" "$RESET" "$1"; }
fail(){ printf "  %b✗%b %s\n" "$RED" "$RESET" "$1" >&2; exit 1; }
box(){ printf "\n%b╔══════════════════════════════════════════════════════════════╗%b\n" "$GOLD" "$RESET"; printf "%b║%b  %-58s%b║%b\n" "$GOLD" "$RESET" "$1" "$GOLD" "$RESET"; printf "%b╚══════════════════════════════════════════════════════════════╝%b\n" "$GOLD" "$RESET"; }

[[ "$(id -u)" -eq 0 ]] || fail "请使用 root 运行：sudo bash install.sh"
box "ATMOSPHERE PANEL · LINUX INSTALLER"
printf "%b   Control plane provisioning / interactive deployment%b\n" "\033[2m" "$RESET"

if command -v apt-get >/dev/null; then export DEBIAN_FRONTEND=noninteractive; apt-get update -y; apt-get install -y git python3 python3-venv python3-pip nodejs npm curl; elif command -v yum >/dev/null; then yum install -y git python3 python3-pip nodejs npm curl; else fail "未找到 apt-get 或 yum"; fi
for cmd in git python3 node npm; do command -v "$cmd" >/dev/null || fail "$cmd 安装失败"; done
read -r -p "  安装路径 [/opt/atmosphere-panel]: " INSTALL_PATH; INSTALL_PATH="${INSTALL_PATH:-$DEFAULT_PATH}"
read -r -p "  后端端口 [27777]: " PANEL_PORT; PANEL_PORT="${PANEL_PORT:-$DEFAULT_PORT}"
[[ "$PANEL_PORT" =~ ^[0-9]+$ ]] && ((PANEL_PORT>=1&&PANEL_PORT<=65535)) || fail "端口无效"
box "01 · SOURCE CHECKOUT"
if [[ -d "$INSTALL_PATH/.git" ]]; then git -C "$INSTALL_PATH" pull --ff-only; else [[ ! -e "$INSTALL_PATH" ]] || fail "目标路径不是 Git 仓库"; git clone "$REPO_URL" "$INSTALL_PATH"; fi
box "02 · BACKEND ENVIRONMENT"
cd "$INSTALL_PATH/backend"; python3 -m venv .venv; .venv/bin/python -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
box "03 · INITIAL ACCESS"
INIT_LOG="$(mktemp)"; timeout 20s .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port "$PANEL_PORT" >"$INIT_LOG" 2>&1 || true
INITIAL_PASSWORD="$(grep -oE "面板初始密码: [^（[:space:]]+" "$INIT_LOG" | head -n1 | sed "s/面板初始密码: //")"; rm -f "$INIT_LOG"
INITIAL_PASSWORD="${INITIAL_PASSWORD:-请查看首次启动日志或已初始化数据库}"
box "04 · FRONTEND BUILD"
cd "$INSTALL_PATH/frontend"; npm config set registry https://registry.npmmirror.com; npm install; npm run build
box "05 · SYSTEMD SERVICE"
cat > "/etc/systemd/system/$SERVICE_NAME" <<SERVICE
[Unit]
Description=ATMOSPHERE Minecraft Control Panel
After=network.target
[Service]
Type=simple
User=root
WorkingDirectory=INSTALL_PATH_PLACEHOLDER/backend
ExecStart=INSTALL_PATH_PLACEHOLDER/backend/.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port PORT_PLACEHOLDER
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1
[Install]
WantedBy=multi-user.target
SERVICE
sed -i "s#INSTALL_PATH_PLACEHOLDER#$INSTALL_PATH#g; s#PORT_PLACEHOLDER#$PANEL_PORT#g" "/etc/systemd/system/$SERVICE_NAME"
systemctl daemon-reload; systemctl enable "$SERVICE_NAME"; systemctl restart "$SERVICE_NAME"
HOST_IP="$(hostname -I 2>/dev/null | awk "{print $1}")"; HOST_IP="${HOST_IP:-127.0.0.1}"
box "ATMOSPHERE PANEL · READY"
printf "  %b面板地址%b http://%s:%s\n" "$GOLD" "$RESET" "$HOST_IP" "$PANEL_PORT"
printf "  %b初始密码%b %s\n" "$GOLD" "$RESET" "$INITIAL_PASSWORD"
printf "  日志：journalctl -u %s -f\n" "$SERVICE_NAME"
