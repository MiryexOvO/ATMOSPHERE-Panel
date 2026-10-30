#!/usr/bin/env bash
set -Eeuo pipefail

CYAN='\033[1;36m'
GREEN='\033[1;32m'
RED='\033[0;31m'
NC='\033[0m'
RESET="$NC"
GOLD="$CYAN"
REPO_URL='https://github.com/MiryexOvO/ATMOSPHERE-Panel.git'
MIRROR_REPO_URL='https://ghfast.top/https://github.com/MiryexOvO/ATMOSPHERE-Panel.git'
DEFAULT_INSTALL_PATH='/opt/ATMOSPHERE-Panel'
DEFAULT_BACKEND_PORT=27777
DEFAULT_FRONTEND_PORT=3000
PIP_INDEX='https://pypi.tuna.tsinghua.edu.cn/simple'
NPM_REGISTRY='https://registry.npmmirror.com'
BACKEND_SERVICE='atmosphere-panel.service'
FRONTEND_SERVICE='atmosphere-frontend.service'

info(){ printf '  %b»%b %s\n' "$CYAN" "$RESET" "$1"; }
fail(){ printf '  %b✗%b %s\n' "$RED" "$RESET" "$1" >&2; exit 1; }
box(){ printf '\n%b╔══════════════════════════════════════════════════════════════╗%b\n' "$CYAN" "$RESET"; printf '%b║%b  %-58s%b║%b\n' "$CYAN" "$RESET" "$1" "$CYAN" "$RESET"; printf '%b╚══════════════════════════════════════════════════════════════╝%b\n' "$CYAN" "$RESET"; }

get_user_config() {
  clear || true
  box '准备部署 ATMOSPHERE PANEL'
  printf '%b交互式安装向导 · 配置完成后开始部署%b\n\n' "$CYAN" "$RESET"

  echo -e "${CYAN}【安装路径】${NC}"
  echo '1) 默认路径 (/opt/ATMOSPHERE-Panel)'
  echo '2) 自定义绝对路径'
  while true; do
    read -r -p '请选择 [1-2] (默认 1): ' choice; choice=${choice:-1}
    case "$choice" in
      1) INSTALL_PATH="$DEFAULT_INSTALL_PATH"; break ;;
      2) read -r -p '请输入绝对路径: ' INSTALL_PATH; [[ -n "$INSTALL_PATH" && "$INSTALL_PATH" = /* ]] && break; echo -e "${RED}路径必须是非空绝对路径。${NC}" ;;
      *) echo -e "${RED}输入无效，请选 1 或 2。${NC}" ;;
    esac
  done
  echo
  echo -e "${CYAN}【后端端口】${NC}"
  echo '1) 默认端口 (27777)'; echo '2) 自定义端口'
  while true; do
    read -r -p '请选择 [1-2] (默认 1): ' choice; choice=${choice:-1}
    case "$choice" in
      1) BACKEND_PORT=27777; break ;;
      2) read -r -p '请输入端口 (1-65535): ' BACKEND_PORT; [[ "$BACKEND_PORT" =~ ^[0-9]+$ ]] && ((BACKEND_PORT>=1&&BACKEND_PORT<=65535)) && break; echo -e "${RED}端口无效。${NC}" ;;
      *) echo -e "${RED}输入无效，请选 1 或 2。${NC}" ;;
    esac
  done
  echo
  echo -e "${CYAN}【前端端口】${NC}"
  echo '1) 默认端口 (3000)'; echo '2) 自定义端口'
  while true; do
    read -r -p '请选择 [1-2] (默认 1): ' choice; choice=${choice:-1}
    case "$choice" in
      1) FRONTEND_PORT=3000; break ;;
      2) read -r -p '请输入端口 (1-65535): ' FRONTEND_PORT; [[ "$FRONTEND_PORT" =~ ^[0-9]+$ ]] && ((FRONTEND_PORT>=1&&FRONTEND_PORT<=65535)) && break; echo -e "${RED}端口无效。${NC}" ;;
      *) echo -e "${RED}输入无效，请选 1 或 2。${NC}" ;;
    esac
  done
  echo
  echo -e "${CYAN}【IP 设置】${NC}"
  echo '1) 自动检测本机 IP'; echo '2) 自定义 IP / 域名'
  while true; do
    read -r -p '请选择 [1-2] (默认 1): ' choice; choice=${choice:-1}
    case "$choice" in
      1) 
        if [[ "$OSTYPE" == "darwin"* ]]; then
          # macOS
          PUBLIC_IP="$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo "")"
        else
          # Linux
          PUBLIC_IP="$(hostname -I 2>/dev/null | awk '{print $1}')"
        fi
        [[ -n "$PUBLIC_IP" ]] && break
        echo -e "${RED}自动检测失败，请选择自定义。${NC}" 
        ;;
      2) read -r -p '请输入 IP 或域名: ' PUBLIC_IP; [[ -n "$PUBLIC_IP" ]] && break; echo -e "${RED}IP/域名不能为空。${NC}" ;;
      *) echo -e "${RED}输入无效，请选 1 或 2。${NC}" ;;
    esac
  done
  [[ "$BACKEND_PORT" != "$FRONTEND_PORT" ]] || fail '前后端端口不能相同'
  printf '\n%b✓ 配置完成%b\n' "$GREEN" "$RESET"
  printf '安装路径: %b%s%b\n' "$CYAN" "$INSTALL_PATH" "$RESET"
  printf '后端端口: %b%s%b\n' "$CYAN" "$BACKEND_PORT" "$RESET"
  printf '前端端口: %b%s%b\n' "$CYAN" "$FRONTEND_PORT" "$RESET"
  printf '公网 IP: %b%s%b\n\n' "$CYAN" "$PUBLIC_IP" "$RESET"
  read -r -p '按回车开始部署，Ctrl+C 取消... ' _confirm
}

get_user_config


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
Environment=NUXT_PUBLIC_API_BASE=/api
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