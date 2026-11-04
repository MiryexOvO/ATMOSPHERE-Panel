#!/usr/bin/env bash
set -Eeuo pipefail
repo=MiryexOvO/ATMOSPHERE-Panel
version=latest
install_dir=/opt/atmosphere-panel
port=27777
plan=0
yes=0
color=''; reset=''
if [[ -t 1 && -z ${NO_COLOR:-} && ${TERM:-dumb} != dumb ]]; then color='\033[1;36m'; reset='\033[0m'; fi
step(){ printf '\n%b  [%s/5] %s%b\n' "$color" "$1" "$2" "$reset"; }
fail(){ printf '\n  FAILED · %s\n' "$*" >&2; exit 1; }
while (($#)); do
  case "$1" in
    --help|-h) printf 'ATMOSPHERE / RELEASE INSTALLER\n  --yes --plan --no-color --dir PATH --port PORT --version vX.Y.Z\nData: /opt/mc-panel; requires Linux + systemd + curl + tar + sha256sum.\n'; exit 0;;
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
printf '\n  TARGET  %s / linux-%s\n  HOME    %s\n  ENTRY   http://<server>:%s\n' "$version" "$arch" "$install_dir" "$port"
((plan==0)) || exit 0
[[ $(uname -s) == Linux && -d /run/systemd/system ]] || fail 'Linux with systemd required'
((EUID==0)) || fail 'Run with sudo bash'
for tool in curl tar sha256sum systemctl; do command -v "$tool" >/dev/null || fail "Install required tool: $tool"; done
work=$(mktemp -d)
trap 'rm -rf -- "$work"' EXIT
trap 'printf "\n  Installation failed; previous releases and data retained.\n" >&2' ERR
step 1 'Resolve official release'
if [[ "$version" == latest ]]; then
  effective=$(curl -fsSL --retry 3 -o /dev/null -w '%{url_effective}' "https://github.com/$repo/releases/latest")
  version=${effective##*/}
  [[ "$version" =~ ^v[0-9]+\.[0-9]+\.[0-9]+([-\.][a-zA-Z0-9.-]+)?$ ]] || fail 'No published release found'
fi
name="atmosphere-panel-$version-linux-$arch.tar.gz"
base="https://github.com/$repo/releases/download/$version"
step 2 'Download binary / no Node.js or Python installation'
curl -fL --retry 3 --progress-bar "$base/$name" -o "$work/$name"
curl -fsSL --retry 3 "$base/$name.sha256" -o "$work/checksum"
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
[[ ! -e "$install_dir/releases/$version" ]] || fail 'Version already installed; use systemctl restart atmosphere-panel'
cp -a "$work/unpacked" "$install_dir/releases/$version"
# Keep the old target for rollback if health verification fails.
previous=$(readlink "$install_dir/current" || true)
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
  if curl -fsS "http://127.0.0.1:$port/api/health" >/dev/null && curl -fsS "http://127.0.0.1:$port/" >/dev/null; then
    printf '\n  ONLINE / http://<server>:%s\n  Logs: sudo journalctl -u atmosphere-panel -f\n  Initial password: first-start service logs\n  Data: /opt/mc-panel (preserved across updates)\n' "$port"
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
