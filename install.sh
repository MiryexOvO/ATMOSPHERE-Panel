#!/usr/bin/env bash
set -Eeuo pipefail
RESET='\033[0m'; GOLD='\033[38;5;222m'; CYAN='\033[36m'; GREEN='\033[32m'; RED='\033[31m'
REPO_URL='https://github.com/MiryexOvO/ATMOSPHERE-Panel.git'; MIRROR_REPO_URL='https://bgithub.xyz/https://github.com/MiryexOvO/ATMOSPHERE-Panel.git'; DEFAULT_INSTALL_PATH='/root/ATMOSPHERE-Panel'; DEFAULT_BACKEND_PORT=27777; DEFAULT_FRONTEND_PORT=3000; PIP_INDEX='https://pypi.tuna.tsinghua.edu.cn/simple'; NPM_REGISTRY='https://registry.npmmirror.com'; BACKEND_SERVICE='atmosphere-panel.service'; FRONTEND_SERVICE='atmosphere-frontend.service'
info(){ printf '  %b»%b %s\n' "$CYAN" "$RESET" "$1"; }; fail(){ printf '  %b✗%b %s\n' "$RED" "$RESET" "$1" >&2; exit 1; }; box(){ printf '\n%b╔══════════════════════════════════════════════════════════════╗%b\n' "$GOLD" "$RESET"; printf '%b║%b  %-58s%b║%b\n' "$GOLD" "$RESET" "$1" "$GOLD" "$RESET"; printf '%b╚══════════════════════════════════════════════════════════════╝%b\n' "$GOLD" "$RESET"; }
[[ $(id -u) -eq 0 ]] || fail '请使用 root 运行'; read -r -p "安装路径 [$DEFAULT_INSTALL_PATH]: " INSTALL_PATH; INSTALL_PATH=${INSTALL_PATH:-$DEFAULT_INSTALL_PATH}; read -r -p "后端端口 [$DEFAULT_BACKEND_PORT]: " BACKEND_PORT; BACKEND_PORT=${BACKEND_PORT:-$DEFAULT_BACKEND_PORT}; read -r -p "前端端口 [$DEFAULT_FRONTEND_PORT]: " FRONTEND_PORT; FRONTEND_PORT=${FRONTEND_PORT:-$DEFAULT_FRONTEND_PORT}; read -r -p '公网 IP/域名: ' PUBLIC_IP
if command -v apt-get >/dev/null; then export DEBIAN_FRONTEND=noninteractive; apt-get update -y; apt-get install -y ca-certificates curl git python3 python3-venv python3-pip build-essential; elif command -v dnf >/dev/null; then dnf install -y ca-certificates curl git python3 python3-pip gcc gcc-c++ make; else yum install -y ca-certificates curl git python3 python3-pip gcc gcc-c++ make; fi
if ! command -v node >/dev/null || [[ $(node -p 'process.versions.node.split(".")[0]') -lt 22 ]]; then curl -fsSL https://mirrors.ustc.edu.cn/nodesource/deb/setup_22.x | bash - || curl -fsSL https://deb.nodesource.com/setup_22.x | bash -; apt-get install -y nodejs 2>/dev/null || true; fi
corepack enable; corepack prepare pnpm@9.15.0 --activate; mkdir -p "$(dirname "$INSTALL_PATH")"; if [[ -d "$INSTALL_PATH/.git" ]]; then git -C "$INSTALL_PATH" pull --ff-only; else git clone --depth 1 "$REPO_URL" "$INSTALL_PATH" || git clone --depth 1 "$MIRROR_REPO_URL" "$INSTALL_PATH"; fi
box 'BACKEND'; cd "$INSTALL_PATH/backend"; python3 -m venv .venv; .venv/bin/python -m pip install -r requirements.txt -i "$PIP_INDEX"; box 'FRONTEND'; cd "$INSTALL_PATH/frontend"; printf 'registry=%s\nonlyBuiltDependencies[]=esbuild\n' "$NPM_REGISTRY" > .npmrc; printf 'NUXT_PUBLIC_API_BASE=/api\nNUXT_PUBLIC_FRONTEND_PORT=3000\n' > .env; pnpm install --no-frozen-lockfile; pnpm run build; NODE_BIN=$(command -v node)
cat > /etc/systemd/system/$BACKEND_SERVICE <<SERVICE
[Unit]
Description=ATMOSPHERE FastAPI
After=network.target
[Service]
WorkingDirectory=$INSTALL_PATH/backend
ExecStart=$INSTALL_PATH/backend/.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port $BACKEND_PORT
Restart=always
[Install]
WantedBy=multi-user.target
SERVICE
cat > /etc/systemd/system/$FRONTEND_SERVICE <<SERVICE
[Unit]
Description=ATMOSPHERE Nuxt SSR
After=network.target
[Service]
WorkingDirectory=$INSTALL_PATH/frontend
ExecStart=$NODE_BIN $INSTALL_PATH/frontend/.output/server/index.mjs
Environment=NODE_ENV=production
Environment=PORT=3000
Environment=HOST=0.0.0.0
Environment=NUXT_PUBLIC_API_BASE=http://$PUBLIC_IP:$BACKEND_PORT
Restart=always
[Install]
WantedBy=multi-user.target
SERVICE
cat > /etc/nginx/conf.d/atmosphere-panel.conf <<NGINX
map $http_upgrade $connection_upgrade { default upgrade; '' close; }
server {
    listen 5173;
    server_name _;
    location /api {
        proxy_pass http://127.0.0.1:27777;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
        proxy_read_timeout 86400s;
        proxy_buffering off;
    }
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
NGINX
systemctl daemon-reload; systemctl enable --now "$BACKEND_SERVICE" "$FRONTEND_SERVICE"; command -v nginx >/dev/null && nginx -t && systemctl reload nginx || true; box 'READY'; printf '面板地址: http://%s:5173\n' "$PUBLIC_IP"
