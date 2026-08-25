$root = Split-Path -Parent $PSScriptRoot
$env:PIP_CACHE_DIR = Join-Path $root '.cache\pip'
$env:npm_config_cache = Join-Path $root '.cache\npm'
$env:TEMP = Join-Path $root '.cache\tmp'
$env:TMP = $env:TEMP
New-Item -ItemType Directory -Force -Path $env:PIP_CACHE_DIR, $env:npm_config_cache, $env:TEMP, (Join-Path $root '.runtime\postgres'), (Join-Path $root '.runtime\redis') | Out-Null
& E:\python\python.exe -m venv (Join-Path $root 'backend\.venv')
& (Join-Path $root 'backend\.venv\Scripts\python.exe') -m pip install -r (Join-Path $root 'backend\requirements-dev.txt')
Push-Location (Join-Path $root 'frontend'); npm install; Pop-Location
