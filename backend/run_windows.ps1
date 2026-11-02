# 在 Windows PowerShell 中运行（无需 Linux 的 .venv/bin/activate）
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$backendListener = Get-NetTCPConnection -State Listen -LocalPort 27777 -ErrorAction SilentlyContinue
if ($backendListener) {
    throw "后端端口 27777 已被占用（PID: $($backendListener.OwningProcess -join ', ')）。请使用已运行的后端，或停止该进程后再启动。"
}
if (-not (Test-Path '.venv')) { py -3 -m venv .venv }
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
& .\.venv\Scripts\python.exe -m app.launcher --host 0.0.0.0 --port 27777
