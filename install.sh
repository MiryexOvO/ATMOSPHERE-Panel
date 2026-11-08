#!/usr/bin/env bash
set -Eeuo pipefail
# Default: download the standalone release installer. Legacy source installation is opt-in.
if [[ ${1:-} != --from-source ]]; then
  installer=$(mktemp "${TMPDIR:-/tmp}/atmosphere-install.XXXXXX")
  trap 'rm -f -- "$installer"' EXIT
  curl --proto '=https' --tlsv1.2 --fail --show-error --location --retry 3 --connect-timeout 15 --max-time 120 https://raw.githubusercontent.com/MiryexOvO/ATMOSPHERE-Panel/main/scripts/install-release.sh -o "$installer"
  # 非 root 时自动提权
  if ((EUID == 0)); then
    bash "$installer" "$@"
  else
    sudo bash "$installer" "$@"
  fi
  exit $?
fi
shift


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
DEFAULT_FRONTEND_PORT=5173
PIP_INDEX=${PIP_INDEX:-https://pypi.org/simple}
NPM_REGISTRY=${NPM_REGISTRY:-https://registry.npmjs.org}
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
      1) BACKEND_PORT="$DEFAULT_BACKEND_PORT"; break ;;
      2) read -r -p '请输入端口 (1-65535): ' BACKEND_PORT; [[ "$BACKEND_PORT" =~ ^[0-9]+$ ]] && ((BACKEND_PORT>=1&&BACKEND_PORT<=65535)) && break; echo -e "${RED}端口无效。${NC}" ;;
      *) echo -e "${RED}输入无效，请选 1 或 2。${NC}" ;;
    esac
  done
  echo
  echo -e "${CYAN}【前端端口】${NC}"
  echo '1) 默认入口端口 (5173)'; echo '2) 自定义端口'
  while true; do
    read -r -p '请选择 [1-2] (默认 1): ' choice; choice=${choice:-1}
    case "$choice" in
      1) FRONTEND_PORT="$DEFAULT_FRONTEND_PORT"; break ;;
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
  printf '访问地址: %b%s%b\n\n' "$CYAN" "$PUBLIC_IP" "$RESET"
  read -r -p '按回车开始部署，Ctrl+C 取消... ' _confirm
}

# 帮助与计划模式不安装依赖、不修改系统。
usage(){ cat <<'HELP'
ATMOSPHERE / INSTALLER
  sudo bash install.sh                          Interactive installation
  sudo bash install.sh --yes --dir /opt/ATMOSPHERE-Panel --port 5173
  bash install.sh --plan                        Preview only
Options:
  --dir PATH           Installation directory (absolute, no spaces)
  --port PORT          Public panel entry (default 5173)
  --backend-port PORT  Internal API (default 27777)
  --internal-port PORT Internal web service (default 3000)
  --host HOST          Address displayed after installation
  --yes                Accept noninteractive defaults
  --no-color           Disable ANSI colors
  --plan               Show installation plan without changes
  --help               Show this help
Requires: Linux, systemd, Python >=3.11. Recommended: Ubuntu 24.04+ / Debian 12+.
HELP
}
ASSUME_YES=0;PLAN=0;INSTALL_PATH=$DEFAULT_INSTALL_PATH
BACKEND_PORT=$DEFAULT_BACKEND_PORT;FRONTEND_PORT=$DEFAULT_FRONTEND_PORT
INTERNAL_FRONTEND_PORT=3000;PUBLIC_IP=127.0.0.1
while (($#));do
  case "$1" in
    --help|-h) usage;exit 0;;
    --yes) ASSUME_YES=1;shift;;
    --plan) PLAN=1;ASSUME_YES=1;shift;;
    --no-color) export NO_COLOR=1;shift;;
    --dir|--port|--backend-port|--internal-port|--host)
      (($#>=2)) || { printf 'Missing argument: %s\n' "$1" >&2;exit 2; }
      case "$1" in --dir) INSTALL_PATH=$2;;--port) FRONTEND_PORT=$2;;--backend-port) BACKEND_PORT=$2;;--internal-port) INTERNAL_FRONTEND_PORT=$2;;--host) PUBLIC_IP=$2;;esac
      shift 2;;
    *) printf 'Unknown option: %s\n' "$1" >&2;exit 2;;
  esac
done
if [[ ! -t 1 || -n ${NO_COLOR:-} || ${TERM:-dumb} == dumb ]];then CYAN='';GREEN='';RED='';NC='';RESET='';GOLD='';fi
if ((ASSUME_YES==0));then DEFAULT_INSTALL_PATH=$INSTALL_PATH;DEFAULT_BACKEND_PORT=$BACKEND_PORT;DEFAULT_FRONTEND_PORT=$FRONTEND_PORT;get_user_config;fi
[[ "$INSTALL_PATH" =~ ^/[a-zA-Z0-9_/-]+$ && "$INSTALL_PATH" != *..* ]] || fail '安装路径只能包含字母、数字、下划线、连字符和斜线'
[[ ! -L "$INSTALL_PATH" ]] || fail '安装目录不能是符号链接'
case "$INSTALL_PATH" in /|/opt|/usr|/usr/local|/etc|/var|/var/lib|/home|/root|/bin|/sbin) fail '请指定专用项目目录，不能使用系统目录本身';;esac
for key in BACKEND_PORT FRONTEND_PORT INTERNAL_FRONTEND_PORT;do
  value=${!key};[[ "$value" =~ ^[0-9]+$ ]] && ((10#$value>=1024&&10#$value<=65535)) || fail '服务端口需要在 1024–65535 之间'
  printf -v "$key" '%d' "$((10#$value))"
done
[[ "$BACKEND_PORT" != "$FRONTEND_PORT" && "$BACKEND_PORT" != "$INTERNAL_FRONTEND_PORT" && "$FRONTEND_PORT" != "$INTERNAL_FRONTEND_PORT" ]] || fail '三个端口必须各不相同'
[[ "$PUBLIC_IP" =~ ^[a-zA-Z0-9.:-]+$ ]] || fail '地址格式无效'
if ((PLAN));then
  box 'ATMOSPHERE / INSTALLATION PLAN'
  printf 'Directory: %s\nPublic: %s  API: %s  Web: %s\n' "$INSTALL_PATH" "$FRONTEND_PORT" "$BACKEND_PORT" "$INTERNAL_FRONTEND_PORT"
  printf '01 source and packages\n02 Node.js (verified SHA256)\n03 Python backend\n04 locked frontend build\n05 Java 21 (verified SHA256)\n06 services + nginx\n07 management command\n08 HTTP health check\n'
  printf 'Existing Node.js / Python dependencies / Java are reused when detected.\n'
  exit 0
fi
[[ $(uname -s) == Linux ]] || fail '一键安装仅面向 Linux；Windows 请使用 backend/run_windows.ps1'
((EUID==0)) || fail '请使用 sudo bash install.sh 运行安装器'
command -v systemctl >/dev/null && [[ -d /run/systemd/system ]] || fail '需要启用 systemd 的 Linux 主机'
INSTALL_LOG=$(mktemp /tmp/atmosphere-install.XXXXXX.log);chmod 0600 "$INSTALL_LOG"
COMMAND_PID=''
trap 'printf "\n%s安装中断。日志：%s%s\n" "$RED" "$INSTALL_LOG" "$RESET" >&2;exit 1' ERR
trap '[[ -z "$COMMAND_PID" ]] || kill -TERM "$COMMAND_PID" 2>/dev/null || true;printf "\n安装已取消。日志：%s\n" "$INSTALL_LOG";exit 130' INT TERM
# 长步骤保留完整日志，终端只显示阶段与耗时。
run_step(){
  local title=$1;shift;local started=$SECONDS status=0 frame=0
  local -a frames=('⠋' '⠙' '⠹' '⠸')
  printf '\n  %b%s%b\n' "$GOLD" "$title" "$RESET"
  "$@" >>"$INSTALL_LOG" 2>&1 & COMMAND_PID=$!
  while kill -0 "$COMMAND_PID" 2>/dev/null;do
    if [[ -t 1 ]];then printf '\r  %b[%s] 正在处理 · %ss%b' "$CYAN" "${frames[$frame]}" "$((SECONDS-started))" "$RESET";fi
    frame=$(((frame+1)%4));sleep .25
  done
  wait "$COMMAND_PID" || status=$?;COMMAND_PID=''
  if ((status));then printf '\r  %b[FAILED] %s%b\n' "$RED" "$title" "$RESET";tail -n 15 "$INSTALL_LOG" >&2;fail "请查看安装日志：$INSTALL_LOG";fi
  printf '\r  %b[OK] %s · %ss%b\n' "$GREEN" "$title" "$((SECONDS-started))" "$RESET"
}
bootstrap(){
  local missing=0 cmd
  # 系统依赖齐全时跳过包管理器更新与安装，避免每次重复拉取。
  for cmd in curl git python3 nginx tar xz make gcc sha256sum; do
    command -v "$cmd" >/dev/null 2>&1 || missing=1
  done
  [[ -d /etc/ssl/certs ]] || missing=1
  python3 -c 'import venv' >/dev/null 2>&1 || missing=1
  python3 -m pip --version >/dev/null 2>&1 || missing=1
  if ((missing==0)); then info '系统依赖已存在，跳过软件包安装'; return; fi
  if command -v apt-get >/dev/null;then export DEBIAN_FRONTEND=noninteractive;apt-get update;apt-get install -y ca-certificates curl git python3 python3-venv python3-pip nginx xz-utils tar build-essential
  elif command -v dnf >/dev/null;then dnf install -y ca-certificates curl git python3 python3-pip nginx xz tar gcc make
  else fail '当前安装器支持 apt / dnf，请使用受支持系统';fi
  mkdir -p "$(dirname "$INSTALL_PATH")"
  if [[ -d "$INSTALL_PATH/.git" ]];then
    [[ -z $(git -c safe.directory="$INSTALL_PATH" -C "$INSTALL_PATH" status --porcelain) ]] || fail '仓库存在未提交修改，已保留原文件；请处理修改后重试'
    git -c safe.directory="$INSTALL_PATH" -C "$INSTALL_PATH" pull --ff-only
  else
    [[ ! -e "$INSTALL_PATH" || -z $(ls -A "$INSTALL_PATH") ]] || fail '目标目录非空，已保留原文件'
    git clone --depth 1 "$REPO_URL" "$INSTALL_PATH"
  fi
}
box 'ATMOSPHERE / CONTROL PLANE INSTALLER'
run_step '01 / 08  系统依赖与项目源代码' bootstrap
[[ -f "$INSTALL_PATH/scripts/install-runtime.sh" ]] || fail '仓库缺少新版安装模块，请确认下载的是当前分支'
source "$INSTALL_PATH/scripts/install-runtime.sh"
installer_run
