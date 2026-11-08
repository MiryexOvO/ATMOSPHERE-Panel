#!/usr/bin/env bash
set -Eeuo pipefail
repo=MiryexOvO/ATMOSPHERE-Panel
version=latest
install_dir=/opt/atmosphere-panel
port=27777
plan=0
yes=0
failed=''
# 可选 GitHub 代理，例如 ATMOSPHERE_GH_PROXY=https://ghfast.top
gh_proxy=${ATMOSPHERE_GH_PROXY:-}
color=''; green=''; reset=''
if [[ -t 1 && -z ${NO_COLOR:-} && ${TERM:-dumb} != dumb ]]; then color='\033[1;36m'; green='\033[1;32m'; reset='\033[0m'; fi
step(){ printf '\n%b  [%s/5] %s%b\n' "$color" "$1" "$2" "$reset"; }
# 老版本 curl 不支持 --retry-all-errors，按能力追加。
retry_opts=(--retry 3 --retry-delay 2)
curl --help 2>/dev/null | grep -q -- '--retry-all-errors' && retry_opts+=(--retry-all-errors)
download(){ curl --proto '=https' --tlsv1.2 --fail --show-error --location "${retry_opts[@]}" --connect-timeout 15 --max-time 600 "$@"; }
# 配置代理后，GitHub 地址统一加上代理前缀。
gh_url(){ if [[ -n "$gh_proxy" ]]; then printf '%s/%s' "${gh_proxy%/}" "$1"; else printf '%s' "$1"; fi; }
fail(){ failed=1; printf '\n  FAILED · %s\n' "$*" >&2; exit 1; }
# 读取本机用于访问面板的 IPv4：优先默认路由出口，其次主机名与全局网卡。
detect_ip(){
  local ip=''
  ip=$(ip route get 1.1.1.1 2>/dev/null | awk '{for(i=1;i<=NF;i++) if($i=="src"){print $(i+1); exit}}')
  [[ -n "$ip" ]] || ip=$(hostname -I 2>/dev/null | tr ' ' '\n' | grep -E '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$' | head -n1)
  [[ -n "$ip" ]] || ip=$(ip -4 -o addr show scope global 2>/dev/null | awk '{print $4; exit}' | cut -d/ -f1)
  printf '%s' "$ip"
}
# 查询公网出口 IP：只用于展示入口地址，失败时留空不影响安装。
detect_public_ip(){
  local ip='' url
  for url in https://api.ipify.org https://ifconfig.me/ip https://icanhazip.com; do
    ip=$(curl -fsS --proto '=https' --max-time 3 "$url" 2>/dev/null | tr -d '[:space:]')
    if [[ "$ip" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then printf '%s' "$ip"; return; fi
    ip=''
  done
  printf '%s' "$ip"
}
# 解析最新版本：依次尝试直连网页、直连 API、代理网页、代理 API。
resolve_version(){
  local url json tag
  local -a urls=("https://github.com/$repo/releases/latest" "https://api.github.com/repos/$repo/releases/latest")
  if [[ -n "$gh_proxy" ]]; then
    urls+=("$(gh_url "https://github.com/$repo/releases/latest")" "$(gh_url "https://api.github.com/repos/$repo/releases/latest")")
  fi
  for url in "${urls[@]}"; do
    if [[ "$url" == *api.github.com* ]]; then
      json=$(download --silent --retry 1 --max-time 10 "$url" 2>/dev/null || true)
      tag=$(printf '%s' "$json" | sed -n 's/.*"tag_name": *"\([^"]*\)".*/\1/p' | head -n1)
      [[ -n "$tag" ]] && { printf '%s' "$tag"; return 0; }
    else
      json=$(download --silent --retry 1 --max-time 10 -o /dev/null -w '%{url_effective}' "$url" 2>/dev/null || true)
      tag=${json##*/}
      [[ "$tag" =~ ^v[0-9]+\.[0-9]+\.[0-9]+ ]] && { printf '%s' "$tag"; return 0; }
    fi
  done
  return 1
}

while (($#)); do
  case "$1" in
    --help|-h) printf 'ATMOSPHERE / RELEASE INSTALLER\n  --yes --plan --no-color --dir PATH --port PORT --version vX.Y.Z\n  Env: ATMOSPHERE_GH_PROXY=https://your-github-proxy\nData: /opt/mc-panel; requires Linux + systemd + curl + tar + sha256sum.\n'; exit 0;;
    --yes) yes=1; shift;;
    --plan) plan=1; yes=1; shift;;
    --no-color) color=''; reset=''; shift;;
    --dir|--port|--version)
      (($#>=2)) || fail "Missing value: $1"
      case "$1" in --dir) install_dir=$2;; --port) port=$2;; --version) version=$2;; esac
      shift 2;;
    *) fail "Unknown option: $1";;
  esac
done
printf '\n%b  A T M O S P H E R E\n  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n  CONTROL PLANE / STANDALONE RELEASE%b\n' "$color" "$reset"
if ((yes==0)); then
  read -r -p "  Panel port [$port]: " answer < /dev/tty
  port=${answer:-$port}
fi
[[ "$install_dir" =~ ^/opt/[a-zA-Z0-9_-]+$ ]] || fail 'Use a dedicated directory directly under /opt'
[[ ! -L "$install_dir" ]] || fail 'Installation directory must not be a symlink'
[[ "$port" =~ ^[0-9]{1,5}$ ]] && ((10#$port>=1024 && 10#$port<=65535)) || fail 'Port must be 1024–65535'
port=$((10#$port))
[[ "$version" == latest || "$version" =~ ^v[0-9]+\.[0-9]+\.[0-9]+([-\.][a-zA-Z0-9.-]+)?$ ]] || fail 'Invalid version tag'
case "$(uname -m)" in x86_64) arch=x64;; aarch64|arm64) arch=arm64;; *) fail 'Unsupported CPU';; esac
server_ip=$(detect_ip)
[[ -n "$server_ip" ]] || server_ip='<server>'
public_ip=$(detect_public_ip)
printf '\n  TARGET  %s / linux-%s\n  HOME    %s\n  ENTRY   http://%s:%s\n' "$version" "$arch" "$install_dir" "$server_ip" "$port"
[[ -n "$public_ip" && "$public_ip" != "$server_ip" ]] && printf '  PUBLIC  http://%s:%s\n' "$public_ip" "$port"
((plan==0)) || exit 0
[[ $(uname -s) == Linux && -d /run/systemd/system ]] || fail 'Linux with systemd required'
((EUID==0)) || fail 'Run with sudo bash'
for tool in curl tar sha256sum systemctl; do command -v "$tool" >/dev/null || fail "Install required tool: $tool"; done
work=$(mktemp -d)
# 只在主 shell 打印一次失败提示，避免 set -E 让子 shell 重复输出。
trap 'status=$?; if [[ ${BASHPID:-$$} -eq $$ ]]; then rm -rf -- "$work"; if ((status != 0)) && [[ -z ${failed:-} ]]; then printf "\n  Installation failed; previous releases and data retained.\n" >&2; fi; fi' EXIT
step 1 'Resolve official release'
if [[ "$version" == latest ]]; then
  version=$(resolve_version) || fail 'Could not resolve the latest release (GitHub unreachable). Retry later, set ATMOSPHERE_GH_PROXY=https://gh-proxy.com, or pin --version v0.3.0'
fi
name="atmosphere-panel-$version-linux-$arch.tar.gz"
base=$(gh_url "https://github.com/$repo/releases/download/$version")
step 2 'Download binary / no Node.js or Python installation'
download --progress-bar "$base/$name" -o "$work/$name"
download --silent "$base/$name.sha256" -o "$work/checksum"
step 3 'Verify SHA256 and unpack'
expected=$(awk 'NR==1 {print $1}' "$work/checksum")
[[ "$expected" =~ ^[a-fA-F0-9]{64}$ ]] || fail 'Invalid checksum'
printf '%s  %s\n' "$expected" "$name" > "$work/verified"
(cd "$work"; sha256sum -c verified)
mkdir "$work/unpacked"
tar -xzf "$work/$name" -C "$work/unpacked" --no-same-owner
[[ -f "$work/unpacked/atmosphere-panel" ]] || fail 'Executable missing'
chmod 0755 "$work/unpacked/atmosphere-panel"
step 4 'Register single systemd service'
# The existing instance manager requires privileged systemd operations.
# mc-panel owns game instance files; the control plane runs as root.
id mc-panel >/dev/null 2>&1 || useradd --system --home-dir /opt/mc-panel --shell /usr/sbin/nologin mc-panel
mkdir -p "$install_dir/releases" /opt/mc-panel/servers /opt/mc-panel/backups /opt/mc-panel/java
chown mc-panel:mc-panel /opt/mc-panel/servers /opt/mc-panel/backups /opt/mc-panel/java
# Keep the old target for rollback if health verification fails.
previous=$(readlink "$install_dir/current" || true)
# Re-running the same version should reinstall it instead of failing.
if [[ -e "$install_dir/releases/$version" ]]; then
  printf '  Version %s already present; replacing it.\n' "$version"
  systemctl stop atmosphere-panel 2>/dev/null || true
  rm -rf "$install_dir/releases/$version"
  # 覆盖的正是当前版本时，回滚目标已不存在。
  if [[ -n "$previous" && "$previous" == "$install_dir/releases/$version" ]]; then previous=''; fi
fi
cp -a "$work/unpacked" "$install_dir/releases/$version"
ln -s "$install_dir/releases/$version" "$install_dir/current.new"
mv -Tf "$install_dir/current.new" "$install_dir/current"
cat > /etc/systemd/system/atmosphere-panel.service <<UNIT
[Unit]
Description=ATMOSPHERE Panel
After=network-online.target
Wants=network-online.target
[Service]
Type=simple
WorkingDirectory=$install_dir
Environment=ATMOSPHERE_DATA_DIR=/opt/mc-panel
Environment=ATMOSPHERE_DB_PATH=/opt/mc-panel/panel.sqlite3
Environment=ATMOSPHERE_FRONTEND_PORT=$port
ExecStart=$install_dir/current/atmosphere-panel --host 0.0.0.0 --port $port
Restart=on-failure
RestartSec=5
[Install]
WantedBy=multi-user.target
UNIT
systemctl daemon-reload
systemctl enable atmosphere-panel
systemctl restart atmosphere-panel
step 5 'Check HTTP readiness'
for attempt in {1..60}; do
  if curl --noproxy '*' --connect-timeout 2 --max-time 5 -fsS "http://127.0.0.1:$port/api/health" >/dev/null && curl --noproxy '*' --connect-timeout 2 --max-time 5 -fsS "http://127.0.0.1:$port/" >/dev/null; then
    printf '\n  %b✓ ATMOSPHERE 安装完成 / INSTALLATION COMPLETE%b\n\n' "$green" "$reset"
    printf '  面板入口  / PANEL ENTRY   http://%s:%s\n' "$server_ip" "$port"
    if [[ -n "$public_ip" && "$public_ip" != "$server_ip" ]]; then
      printf '  公网地址  / PUBLIC IP     http://%s:%s\n' "$public_ip" "$port"
    fi
    printf '  运行日志  / LOGS          sudo journalctl -u atmosphere-panel -f\n'
    printf '  初始密码  / PASSWORD      first-start service logs\n'
    printf '  数据目录  / DATA          /opt/mc-panel (preserved across updates)\n'
    if [[ -n "$public_ip" && "$public_ip" != "$server_ip" ]]; then
      printf '\n  在浏览器中粘贴上方入口地址：同一网络用内网地址，外网请用公网地址或你的域名\n'
      printf '  Paste the address above into your browser: use the LAN address on the same network, or the public address or your domain from outside.\n'
    elif [[ "$server_ip" == '<server>' ]]; then
      printf '\n  在浏览器中粘贴上方入口地址 把 <server> 换成这台服务器的公网 IP 或域名\n'
      printf '  Paste the panel address above into your browser, replacing <server> with this server public IP or domain.\n'
    else
      printf '\n  在浏览器中粘贴上方入口地址；或把 %s 换成本机域名（外网访问请用公网 IP）\n' "$server_ip"
      printf '  Paste the address above into your browser, or replace %s with your own domain (use the public IP for external access).\n' "$server_ip"
    fi
    printf '\n  首次账号与密码见首次启动日志 / Initial credentials appear in the first-start logs.\n\n'
    exit 0
  fi
  sleep 1
done
if [[ -n "$previous" ]]; then
  ln -s "$previous" "$install_dir/rollback.new"
  mv -Tf "$install_dir/rollback.new" "$install_dir/current"
  systemctl restart atmosphere-panel
fi
fail 'Readiness failed; inspect journalctl -u atmosphere-panel'
