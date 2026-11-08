<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="header/header-dark.png">
    <source media="(prefers-color-scheme: light)" srcset="header/header-light.png">
    <img src="header/header-dark.png" width="700" alt="Banner">
  </picture>
</p>

<p align="center">
  <!-- HTML5 -->
  <a href="https://developer.mozilla.org/en-US/docs/Web/HTML" target="_blank"><img src="https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white" alt="HTML5"/></a>
  <!-- Vue.js -->
  <a href="https://vuejs.org/" target="_blank"><img src="https://img.shields.io/badge/Vue.js-4FC08D?style=for-the-badge&logo=vuedotjs&logoColor=white" alt="Vue.js"/></a>
  <!-- Tailwind CSS -->
  <a href="https://tailwindcss.com/" target="_blank"><img src="https://img.shields.io/badge/Tailwind_CSS-38BDF8?style=for-the-badge&logo=tailwindcss&logoColor=white" alt="Tailwind CSS"/></a>
  <!-- Nuxt.js -->
  <a href="https://nuxt.com/" target="_blank"><img src="https://img.shields.io/badge/Nuxt.js-00DC82?style=for-the-badge&logo=nuxtdotjs&logoColor=white" alt="Nuxt.js"/></a>
  <!-- TypeScript -->
  <a href="https://www.typescriptlang.org/" target="_blank"><img src="https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white" alt="TypeScript"/></a>
  <!-- Python -->
  <a href="https://www.python.org/" target="_blank"><img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/></a>
  <!-- FastAPI -->
  <a href="https://fastapi.tiangolo.com/" target="_blank"><img src="https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI"/></a>
  <!-- SQLite -->
  <a href="https://www.sqlite.org/" target="_blank"><img src="https://img.shields.io/badge/SQLite-07405E?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLite"/></a>
  <!-- bcrypt -->
  <a href="https://github.com/pyca/bcrypt" target="_blank"><img src="https://img.shields.io/badge/Bcrypt-000000?style=for-the-badge&logo=security&logoColor=white" alt="bcrypt"/></a>
  <!-- License -->
  <a href="https://opensource.org/licenses/MIT" target="_blank"><img src="https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge" alt="MIT License"></a>
</p>

<p align="center">
  <a href="./README_EN.md">English</a> | 简体中文 | <a href="README_JP.md">日本語</a>
</p>

ATMOSPHERE-PANEL 是一个基于 Web 的 **Minecraft 服务器管理面板**。通过受身份验证保护的界面，可以注册服务器实例、选择服务端核心与版本，并由后端 API 完成部署与运行管理

项目由两个部分组成：

- `frontend/` — 基于 Nuxt 的 Web 界面
- `backend/` — 具备 SQLite 存储和部署 API 的 FastAPI 服务

## 目录

- [功能](#功能)
- [开箱即用（单进程部署）](#standalone)
- [获取源码](#获取源码)
- [前端开发](#frontend-dev)
- [后端开发](#backend-dev)
- [服务管理](#服务管理)
- [开发检查](#开发检查)
- [构建发布（维护者）](#maintainer-build)
- [许可证](#许可证)
- [维护与支持](#维护与支持)

## 功能

- 安全密码哈希与会话 Cookie 身份验证
- 实例 ID、端口与运行状态管理
- Java 版、基岩版及 MCDR 核心与版本选择
- `.zip` / `.tar.gz` 服务器核心与 Modpack 上传，解压时检查路径遍历与危险文件
- 部署时的 Java 版本与 JVM 内存设置
- 官方资源参考与镜像源设置
- 基于 SQLite 的本地数据存储

<a id="standalone"></a>

## 开箱即用（单进程部署）

> - **零依赖运行**：发布包内置 Web 界面与独立 Python 运行时 无需额外部署 Node.js、Python、Nginx
> - **单端口访问**：一个进程 单个端口即可拉起全站服务
> - **外部依赖说明**：Java、BDS、MCDR 等管理运行环境需根据具体实例按需配置 不打包在面板下载包内

### Linux / systemd

一行命令安装：

```bash
# 拉取 install.sh 并执行，参数原样传给安装器（非 root 时自动提权）
curl -fsSL https://raw.githubusercontent.com/MiryexOvO/ATMOSPHERE-Panel/main/install.sh \
  | bash -s -- --yes --port 27777
```

交互式安装：

```bash
# 会询问端口，进程替换不占用 stdin
bash <(curl -fsSL https://raw.githubusercontent.com/MiryexOvO/ATMOSPHERE-Panel/main/install.sh)
```

> 下载发布包时如果遇到 GitHub 504 或超时，可让下载走 GitHub 代理（不影响其它流量）：

```bash
curl -fsSL https://raw.githubusercontent.com/MiryexOvO/ATMOSPHERE-Panel/main/install.sh \
  | ATMOSPHERE_GH_PROXY=https://gh-proxy.com bash -s -- --yes --port 27777
```

默认入口：`http://<服务器地址>:27777`  
  
| 参数 | 作用 |
| --- | --- |
| `--yes --port 27777` | 非交互安装，指定入口端口 |
| `--version v0.3.0` | 锁定发布版本 |
| `--dir /opt/atmosphere-panel` | 自定义程序目录（默认值，须位于 `/opt` 下） |
| `--plan --no-color` | 只预览安装计划 |  
  
安装器会从 GitHub Releases 下载架构包、校验 SHA256、解压、注册 `atmosphere-panel` 服务，检查网页与 API。需预装 `curl`、`tar`、`sha256sum`。当前提供 Linux x64、Windows x64、macOS arm64，其他架构需自行构建

**首次使用**

- 初始密码只在首次启动日志中出现：`sudo journalctl -u atmosphere-panel -f`
- 数据保存在 `/opt/mc-panel`；更新会保留数据，升级前请先备份
- 安装器适用于全新安装，以及由它自己创建的目录
- 旧版源码安装需先备份、迁移数据库，并停用旧前端与 Nginx 服务
- 面板因 systemd 实例管理机制以 root 运行；游戏实例使用 `mc-panel` 账号
- 仅已公开的 Release 可安装，草稿或失败的 Actions 不会成为 latest

常用命令：

```bash
# 跟踪面板日志（首次密码也会出现在这里）
sudo journalctl -u atmosphere-panel -f
# 重启面板服务
sudo systemctl restart atmosphere-panel
```

### Windows / macOS

首先从 [Releases](https://github.com/MiryexOvO/ATMOSPHERE-Panel/releases) 下载对应平台压缩包并解压：

```powershell
# Windows：解压后在终端运行
.\atmosphere-panel.exe --port 27777
```

```bash
# macOS：赋予执行权限后启动
chmod +x ./atmosphere-panel
./atmosphere-panel --port 27777
```

打开 `http://127.0.0.1:27777`。数据默认位于可执行文件旁的 `data/`，请放在可写目录  
可用 `ATMOSPHERE_DATA_DIR` 与 `ATMOSPHERE_DB_PATH` 自定义。macOS 包暂未签名或公证

### 安装器说明

- `scripts/install-release.sh`：二进制安装器，下载发布包、校验 SHA256、解压、注册 systemd、检查API
- `install.sh`：兼容入口，默认转交给 `install-release.sh`加上 `--from-source` 进入旧版源码安装
- 一行命令获取 `install.sh`，由它下载并运行 `install-release.sh`；无需克隆源码或现场编译

## 获取源码

```bash
# 克隆源码并进入项目目录
git clone https://github.com/MiryexOvO/ATMOSPHERE-Panel.git
cd ATMOSPHERE-Panel
```

开发端口：Web `5173` 后端 API `27777`。Nuxt 使用客户端渲染 `/api` 通过代理转发到 FastAPI。

<a id="frontend-dev"></a>

## 前端开发（Nuxt 4.6.2）

```bash
# 进入前端目录
cd frontend
# 安装依赖
pnpm install
# 开发服务器
pnpm dev
# 服务器开发时
pnpm dev --host
# 生产构建
pnpm build
# 预览生产版本
pnpm preview
```

访问 `http://127.0.0.1:5173` 首次启动时，终端只打印一次 20 位初始密码

<a id="backend-dev"></a>

## 后端开发（FastAPI）

### Linux / MacOs

```bash
# 进入后端目录
cd backend
# 创建虚拟环境
python3 -m venv .venv
# 激活虚拟环境
source .venv/bin/activate
# 安装 Python 依赖
pip install -r requirements.txt
# 指定数据目录，启动开发服务器
export ATMOSPHERE_DATA_DIR="$PWD/data"
python -m app.launcher --host 0.0.0.0 --port 27777
```

> 请确保已拥有 Python 3.11 以上的版本

### Windows

```powershell
# 进入后端目录
cd backend
# 仅当前会话允许执行脚本，避免权限报错
Set-ExecutionPolicy -Scope Process Bypass
# 运行项目提供的 Windows 启动脚本
.\run_windows.ps1
```

> Windows 请使用 `.venv\Scripts\python.exe`，不要执行 `.venv/bin/activate`
> 如果 Python 3.14 的系统 pip 已损坏，建议改用 Python 3.12 或 3.13 创建虚拟环境

## 服务管理

源码安装注册 systemd 服务后可用：

```bash
# 查看服务状态
sudo atmosphere status
# 跟踪后端日志
sudo atmosphere logs
# 重启面板服务
sudo atmosphere restart
# 停止面板服务
sudo atmosphere stop
```

## 开发检查

```bash
# 前端生产构建检查
cd frontend && npm run build
# 后端 Python 语法检查
cd ../backend && find app -name "*.py" -print0 | xargs -0 -n1 python3 -m py_compile
```

<a id="maintainer-build"></a>

## 构建发布（维护者）

在目标系统安装 Python 3.12、Node.js 24 和项目指定的 pnpm，然后执行：

```bash
# 安装后端依赖与 PyInstaller
python -m pip install -r backend/requirements.txt pyinstaller==6.11.1
# 生成平台发布包（示例版本 v0.2.0）
python scripts/build-release.py --version v0.2.0
# 对生成的发布包做启动冒烟测试
python scripts/smoke-release.py
```

- 产物：`release/` 下的平台压缩包与 SHA256 文件，脚本会打印实际体积
- 仅打包运行所需内容，不包含 `node_modules`、源码数据库、Java 或服务器数据
- 单文件程序首次启动需要临时解压运行时

发布流程：

1. 推送 `v*` 标签触发三平台构建
2. 全部成功后自动创建 **Release 草稿**
3. 检查附件、平台结果与更新说明后手动发布，安装器才能读取 latest
4. Actions 手动运行只生成构建附件；当前不会自动推送标签或自动公开 Release

## 许可证

本项目采用 [MIT License](LICENSE)

## 维护与支持

Maintained by [Miryex](https://www.astrelia7.com)
