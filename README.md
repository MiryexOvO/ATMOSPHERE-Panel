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

## 概要

ATMOSPHERE-PANEL 是一个基于 Web 的 Minecraft 服务器管理面板。通过受身份验证保护的界面，您可以进行服务器实例的注册、服务器核心与版本的选择，以及利用后端 API 部署服务器文件

项目由两个部分组成：

- `frontend/` — 基于 Nuxt 的 Web 界面
- `backend/` — 具备 SQLite 存储和部署 API 的 FastAPI 服务

## 功能

- 采用安全密码哈希与会话 Cookie 的身份验证功能
- 管理实例 ID 和端口的 Minecraft 服务器实例管理
- 支持多款 Java 版、基岩版及 MCDR 核心与版本选择
- 支持 `.zip` 和 `.tar.gz` 格式的服务器核心及 Modpack 压缩包处理
- 检查路径遍历和危险文件的安全压缩包解压
- 部署时的 Java 版本与 JVM 内存设置
- 针对部分资源提供官方资源参考与镜像设置
- 基于 SQLite 的本地数据存储

## 快速安装（单进程）

正式发布包内含网页与 Python 运行时，一个进程、一个端口即可访问全站，无需安装 Node.js、Python 或 Nginx。Java、BDS 和 MCDR 运行环境按实例需求另行准备，不打进面板下载包。发布包大小以 Release 附件为准。

### Linux / systemd

```bash
curl -fL --retry 3 https://raw.githubusercontent.com/MiryexOvO/ATMOSPHERE-Panel/main/install.sh -o /tmp/atmosphere-install.sh
sudo bash /tmp/atmosphere-install.sh
```

默认入口 `http://服务器地址:27777`。安装器从 GitHub Releases 下载本机架构包、验证 SHA256、注册 `atmosphere-panel` 服务并检查网页与 API。需要预装 curl、tar、sha256sum；当前流水线提供 Linux x64、Windows x64、macOS arm64，其他架构需在对应机器构建。

```bash
sudo bash /tmp/atmosphere-install.sh --yes --port 27777 --version v0.2.0
bash /tmp/atmosphere-install.sh --plan
sudo journalctl -u atmosphere-panel -f
sudo systemctl restart atmosphere-panel
```

首次密码见首次启动日志。数据保存于 `/opt/mc-panel`，更新保留数据；更新前请备份。安装器适用于全新安装和此发布安装器创建的目录。旧版源码安装需先备份、迁移数据库并停用旧前端和 Nginx 服务，避免继续访问旧站点。控制面板因现有 systemd 实例管理机制以 root 运行；游戏实例使用 mc-panel 账号。

### Windows / macOS

从 [Releases](https://github.com/MiryexOvO/ATMOSPHERE-Panel/releases) 下载对应平台压缩包并解压：

```powershell
# Windows
.\atmosphere-panel.exe --port 27777
```

```bash
# macOS
chmod +x ./atmosphere-panel
./atmosphere-panel --port 27777
```

打开 `http://127.0.0.1:27777`。数据默认位于可执行文件旁 `data/`，请放在可写目录；可用 `ATMOSPHERE_DATA_DIR` 与 `ATMOSPHERE_DB_PATH` 自定义。macOS 包暂未签名或公证。

### 维护者：构建与发布

在目标操作系统安装 Python 3.12、Node.js 24 和项目指定的 pnpm，然后执行：

```bash
python -m pip install -r backend/requirements.txt pyinstaller==6.11.1
python scripts/build-release.py --version v0.2.0
python scripts/smoke-release.py
```

脚本生成静态网页、打包单文件可执行程序，在 `release/` 输出压缩包及 SHA256 文件，并打印实际体积。仅打包运行所需内容，不包含 node_modules、源码数据库、Java 或服务器数据。单文件程序首次启动需要临时解压运行时。

推送 `v*` 标签触发三平台构建，全部成功后创建 **Release 草稿**；检查附件、平台运行结果与更新说明后发布草稿，安装器才能读取 latest。Actions 手动运行只生成可下载构建附件。当前不包含自动推送标签或自动公开发布。

## 源码开发

```bash
git clone https://github.com/MiryexOvO/ATMOSPHERE-Panel.git
cd ATMOSPHERE-Panel
```

## 前端开发（[Nuxt 4.6.2](https://nuxt.com/docs/getting-started/introduction)）

```bash
# 1.进入项目文件夹
cd frontend

# 2.安装依赖
pnpm install

# 3.启动开发服务器
pnpm dev

# 4.部署到生产环境
pnpm build

# 5.本地预览正式版本
pnpm preview
```

开发 Web 端口：`5173`；后端 API：`27777`
访问 `http://127.0.0.1:5173`。当前 Nuxt 使用客户端渲染，API 通过 `/api` 代理到 FastAPI `27777`  
首次启动时，终端只打印一次 20 位初始密码

## 后端开发（[FastAPI](https://fastapi.tiangolo.com/)）

### Linux 手动部署

```bash
# 1.进入项目文件夹
cd backend

# 2.创建虚拟环境
python3 -m venv .venv

# 3.激活虚拟环境
source .venv/bin/activate  # Windows 用户请使用: .venv\Scripts\activate

# 4.安装依赖
pip install -r requirements.txt

# 5.启动开发服务器
export ATMOSPHERE_DATA_DIR="$PWD/data"
python -m app.launcher --host 0.0.0.0 --port 27777
```

### Windows

```powershell
# 1.进入项目文件夹
cd backend

# 2.临时允许当前会话执行脚本（避免权限报错）
Set-ExecutionPolicy -Scope Process Bypass

# 3.运行 Windows 启动脚本
.\run_windows.ps1
```
不要使用 Linux 命令 `.venv/bin/activate`；Windows 虚拟环境入口是 `.venv\\Scripts\\python.exe`  
如果 Python 3.14 的系统 pip 已损坏，建议使用 Python 3.12 或 3.13 创建虚拟环境

## 服务管理

```bash
# 1. 查看 atmosphere-panel 服务当前运行状态（是否正在运行、是否报错、启动日志等）
sudo systemctl status atmosphere-panel.service

# 2. 重启 atmosphere-panel 服务（通常在修改了后端代码或配置文件后执行，用于应用更新）
sudo systemctl restart atmosphere-panel.service

# 3. 实时跟踪/查看 atmosphere-panel 服务的运行日志（-f 表示 follow 实时滚动输出，方便排查报错）
sudo journalctl -u atmosphere-panel.service -f
```

## 提示

- 本版本消息:此版本还无法正常使用 预计0.2版本可正常使用所有功能 ^ ^
- windows 启动脚本仅供跨平台开发使用
- 初始密码只在首次初始化时输出

## 开发检查

```bash
cd frontend && npm run build
cd ../backend && find app -name "*.py" -print0 | xargs -0 -n1 python3 -m py_compile
```

## 许可证

本项目采用 [MIT License](LICENSE)

## 维护与支持

Maintained by [Miryex](https://www.astrelia7.com)
