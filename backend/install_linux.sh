#!/usr/bin/env bash
set -euo pipefail
# 以 root 执行：初始化 Atmosphere 的最小运行环境
id -u mcserver >/dev/null 2>&1 || useradd --system --home-dir /opt/mc-panel --shell /usr/sbin/nologin mcserver
install -d -o mcserver -g mcserver -m 0750 /opt/mc-panel/servers /opt/mc-panel/java
chown -R mcserver:mcserver /opt/mc-panel
printf '%s\n' '[READY] mcserver user and /opt/mc-panel initialized.'
