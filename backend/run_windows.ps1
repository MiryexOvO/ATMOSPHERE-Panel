# 在 Windows PowerShell 中运行（无需 Linux 的 .venv/bin/activate）
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
if (-not (Test-Path '.venv')) { py -3 -m venv .venv }
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
& .\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 27777
