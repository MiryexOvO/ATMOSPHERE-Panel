#

默认面板端口：`27777` 可配置项

## 后端（Linux）

```bash
cd backend
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 27777
```

首次启动时，终端只打印一次 20 位初始密码。

## 前端开发（Nuxt 4）

```bash
cd frontend
npm install
npm run dev
```

访问 `http://127.0.0.1:5173`。当前 Nuxt 使用客户端渲染，API 通过 `/api` 代理到 FastAPI `27777`。
生产构建：`npm run build`，再用 `npm run preview` 验证。

## Windows 开发启动

在 PowerShell 中执行：

```powershell
cd backend
Set-ExecutionPolicy -Scope Process Bypass
.\\run_windows.ps1
```

不要使用 Linux 命令 `.venv/bin/activate`；Windows 虚拟环境入口是 `.venv\\Scripts\\python.exe`。如果 Python 3.14 的系统 pip 已损坏，建议使用 Python 3.12 或 3.13 创建虚拟环境。
