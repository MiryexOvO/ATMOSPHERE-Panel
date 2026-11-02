#!/usr/bin/env bash
# 由根目录 install.sh 加载；所有步骤输出到私有安装日志。

install_node() {
  if [[ $(command -v node || true) =~ ^/usr/(local/)?bin/node$ ]] && node -e 'let [a,b]=process.versions.node.split(".").map(Number);process.exit(a>=24||(a===22&&b>=12)?0:1)'; then NODE_BIN=$(command -v node); return; fi
  local arch archive directory base
  case "$(uname -m)" in x86_64) arch=x64;; aarch64|arm64) arch=arm64;; *) fail '不支持此 CPU 架构';; esac
  directory=$(mktemp -d);base='https://nodejs.org/dist/latest-v24.x'
  curl --fail --location --retry 3 "$base/SHASUMS256.txt" -o "$directory/sums"
  archive=$(awk -v suffix="linux-$arch.tar.xz" '$2 ~ suffix"$" {print $2;exit}' "$directory/sums")
  [[ -n "$archive" ]] || fail 'Node 官方目录未提供本机架构'
  curl --fail --location --retry 3 "$base/$archive" -o "$directory/$archive"
  (cd "$directory"; awk -v file="$archive" '$2==file' sums | sha256sum --check -)
  NODE_HOME="$INSTALL_PATH/.tools/node";mkdir -p "$NODE_HOME"
  tar -xJf "$directory/$archive" -C "$NODE_HOME" --strip-components=1
  NODE_BIN="$NODE_HOME/bin/node";export PATH="$NODE_HOME/bin:$PATH"
  rm -f -- "$directory/$archive" "$directory/sums";rmdir "$directory"
}

prepare_backend() {
  local candidate
  PYTHON_BIN=''
  for candidate in python3.13 python3.12 python3.11 python3; do
    if command -v "$candidate" >/dev/null && "$candidate" -c 'import sys; assert sys.version_info >= (3,11)' 2>/dev/null; then PYTHON_BIN=$(command -v "$candidate");break;fi
  done
  [[ -n "$PYTHON_BIN" ]] || fail '需要 Python 3.11+，推荐 Ubuntu 24.04+ / Debian 12+；安装后重新执行即可'
  "$PYTHON_BIN" -m venv "$INSTALL_PATH/backend/.venv"
  "$INSTALL_PATH/backend/.venv/bin/python" -m pip install --disable-pip-version-check -r "$INSTALL_PATH/backend/requirements.txt" --index-url "$PIP_INDEX"
}

prepare_frontend() {
  local manager
  manager=$("$NODE_BIN" -p "require('$INSTALL_PATH/frontend/package.json').packageManager")
  [[ "$manager" =~ ^pnpm@[0-9]+\.[0-9]+\.[0-9]+$ ]] || fail 'packageManager 不是已锁定的 pnpm 版本'
  npm install --global --prefix "$INSTALL_PATH/.tools/pnpm" "$manager" --registry "$NPM_REGISTRY"
  export PATH="$INSTALL_PATH/.tools/pnpm/bin:$(dirname "$NODE_BIN"):$PATH"
  cd "$INSTALL_PATH/frontend"
  npm_config_registry="$NPM_REGISTRY" pnpm install --frozen-lockfile
  NUXT_PUBLIC_API_BASE=/api pnpm build
}

install_java() {
  # 使用官方元数据中的下载地址与摘要，保留已有 Java 安装。
  local target directory
  target="$DATA_PATH/java/temurin-21"
  [[ -x "$target/bin/java" ]] && return
  [[ ! -e "$target" ]] || fail 'Java 目标目录已有不完整内容，请先检查后再重试'
  directory=$(mktemp -d)
  "$PYTHON_BIN" - "$directory" <<'PY'
import hashlib,json,pathlib,platform,urllib.request,sys
root=pathlib.Path(sys.argv[1]);arch='aarch64' if platform.machine() in ('aarch64','arm64') else 'x64'
with urllib.request.urlopen(f'https://api.adoptium.net/v3/assets/latest/21/hotspot?architecture={arch}&image_type=jre&os=linux&vendor=eclipse',timeout=30) as response: package=json.load(response)[0]['binary']['package']
archive=root/'java.tar.gz';digest=hashlib.sha256()
with urllib.request.urlopen(package['link'],timeout=90) as response,archive.open('wb') as output:
 while chunk:=response.read(1024*1024):output.write(chunk);digest.update(chunk)
if digest.hexdigest()!=package['checksum']:raise SystemExit('Java SHA256 mismatch')
PY
  mkdir -p "$target";tar -xzf "$directory/java.tar.gz" -C "$target" --strip-components=1
  "$target/bin/java" -version
  rm -f -- "$directory/java.tar.gz";rmdir "$directory"
}

write_services() {
  # 独立服务用户运行面板；不覆盖已有 nginx 站点。
  local service_user=atmosphere service_group
  if [[ $(stat -c '%U' "$DATA_PATH") == mcserver ]];then service_user=mcserver;fi
  id "$service_user" >/dev/null 2>&1 || useradd --system --home-dir "$DATA_PATH" --shell /usr/sbin/nologin "$service_user"
  service_group=$(id -gn "$service_user")
  mkdir -p "$DATA_PATH";chown -R "$service_user:$service_group" "$INSTALL_PATH" "$DATA_PATH"
  cat > "/etc/systemd/system/$BACKEND_SERVICE" <<SERVICE
[Unit]
Description=ATMOSPHERE Control Plane
After=network-online.target
Wants=network-online.target
[Service]
Type=simple
User=$service_user
Group=$service_group
WorkingDirectory=$INSTALL_PATH/backend
Environment=PYTHONUNBUFFERED=1
Environment=PYTHONDONTWRITEBYTECODE=1
Environment=ATMOSPHERE_DATA_DIR=$DATA_PATH
Environment=ATMOSPHERE_BACKEND_PORT=$BACKEND_PORT
Environment=ATMOSPHERE_FRONTEND_PORT=$INTERNAL_FRONTEND_PORT
Environment=ATMOSPHERE_INSTANCE_DRIVER=process
Environment=NO_COLOR=1
ExecStart=$INSTALL_PATH/backend/.venv/bin/python -m app.launcher --host 127.0.0.1 --port $BACKEND_PORT
Restart=on-failure
RestartSec=3
KillMode=process
NoNewPrivileges=true
UMask=0077
[Install]
WantedBy=multi-user.target
SERVICE
  cat > "/etc/systemd/system/$FRONTEND_SERVICE" <<SERVICE
[Unit]
Description=ATMOSPHERE Web Interface
After=network-online.target atmosphere-panel.service
[Service]
User=$service_user
Group=$service_group
WorkingDirectory=$INSTALL_PATH/frontend
ExecStart=$NODE_BIN $INSTALL_PATH/frontend/.output/server/index.mjs
Environment=NODE_ENV=production
Environment=PORT=$INTERNAL_FRONTEND_PORT
Environment=HOST=127.0.0.1
Environment=NUXT_PUBLIC_API_BASE=/api
Restart=on-failure
RestartSec=3
NoNewPrivileges=true
[Install]
WantedBy=multi-user.target
SERVICE
  cat > /etc/nginx/conf.d/atmosphere-panel.conf <<'NGINX'
server {
    listen __PUBLIC_PORT__;
    server_name _;
    client_max_body_size 501m;
    location /api/ {
        proxy_pass http://127.0.0.1:__BACKEND_PORT__;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400s;
        proxy_request_buffering off;
        proxy_buffering off;
    }
    location / {
        proxy_pass http://127.0.0.1:__FRONTEND_PORT__;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
NGINX
  sed -i "s/__PUBLIC_PORT__/$FRONTEND_PORT/g;s/__BACKEND_PORT__/$BACKEND_PORT/g;s/__FRONTEND_PORT__/$INTERNAL_FRONTEND_PORT/g" /etc/nginx/conf.d/atmosphere-panel.conf
  nginx -t
  systemctl daemon-reload
  systemctl enable "$BACKEND_SERVICE" "$FRONTEND_SERVICE" nginx
  systemctl restart "$BACKEND_SERVICE" "$FRONTEND_SERVICE"
  systemctl is-active --quiet nginx && systemctl reload nginx || systemctl start nginx
}

install_cli() {
  cat > /usr/local/bin/atmosphere <<'CLI'
#!/usr/bin/env bash
set -euo pipefail
case "${1:-status}" in
 status) systemctl --no-pager status atmosphere-panel atmosphere-frontend;;
 logs) journalctl -u atmosphere-panel -f --no-hostname;;
 restart) systemctl restart atmosphere-panel atmosphere-frontend;;
 stop) systemctl stop atmosphere-panel atmosphere-frontend;;
 *) printf 'ATMOSPHERE · atmosphere [status|logs|restart|stop]\n';exit 2;;
esac
CLI
  chmod 0755 /usr/local/bin/atmosphere
}

verify_install() {
  local attempt
  for attempt in {1..30}; do
    if curl --silent --fail "http://127.0.0.1:$FRONTEND_PORT/api/health" >/dev/null; then return;fi
    sleep 1
  done
  fail '健康检查失败，请运行 atmosphere logs 查看错误；安装数据已保留'
}

installer_run() {
  DATA_PATH=${ATMOSPHERE_DATA_DIR:-/opt/mc-panel}
  case "$DATA_PATH" in /|/opt|/usr|/usr/local|/etc|/var|/var/lib|/home|/root|/bin|/sbin) fail '运行数据必须使用专用目录';;esac
  [[ "$DATA_PATH" =~ ^/[a-zA-Z0-9_/-]+$ && "$DATA_PATH" != / ]] || fail '运行数据目录格式无效'
  [[ $(realpath -m "$DATA_PATH") == "$DATA_PATH" ]] || fail '运行数据目录不能包含符号链接或非标准路径'
  mkdir -p "$DATA_PATH/java"
  run_step '02 / 08  Node.js 运行环境' install_node
  # 后台步骤不向父 Shell 回传变量，运行环境在此重新定位。
  if [[ -x "$INSTALL_PATH/.tools/node/bin/node" ]];then NODE_BIN="$INSTALL_PATH/.tools/node/bin/node";else NODE_BIN=$(command -v node);fi
  export PATH="$(dirname "$NODE_BIN"):$PATH"
  for candidate in python3.13 python3.12 python3.11 python3;do
    if command -v "$candidate" >/dev/null && "$candidate" -c 'import sys;assert sys.version_info>=(3,11)' 2>/dev/null;then PYTHON_BIN=$(command -v "$candidate");break;fi
  done
  run_step '03 / 08  Python 后端依赖'  prepare_backend
  run_step '04 / 08  前端依赖与生产构建' prepare_frontend
  run_step '05 / 08  Java 21 官方运行环境' install_java
  run_step '06 / 08  服务与反向代理' write_services
  run_step '07 / 08  ATMOSPHERE 管理命令' install_cli
  run_step '08 / 08  面板健康检查' verify_install
  box 'ATMOSPHERE  /  ONLINE'
  printf '  面板入口  %bhttp://%s:%s%b\n' "$GREEN" "$PUBLIC_IP" "$FRONTEND_PORT" "$RESET"
  printf '  管理命令  atmosphere status / logs / restart / stop\n  安装日志  %s\n  实例数据  %s\n' "$INSTALL_LOG" "$DATA_PATH"
  printf '  初始账号与密码仅在首次初始化日志中出现：\n  sudo journalctl -u atmosphere-panel --no-pager | grep -A 4 "INITIAL ACCESS"\n\n'
}
