param([string]$Python = 'python')
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
& $Python -m venv .venv
if ($LASTEXITCODE -ne 0) { throw 'Python 3.11 or 3.12 is required. Pass -Python with its absolute path.' }
& .\.venv\Scripts\python.exe -m pip install -r python-backend/requirements-lock.txt
if ($LASTEXITCODE -ne 0) { throw 'Backend dependency installation failed.' }
npm install
if ($LASTEXITCODE -ne 0) { throw 'Frontend dependency installation failed.' }
Write-Host 'Ready. Run npm run tauri dev, or npm run tauri build for installers.'
