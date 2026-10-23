# Qdrant sunucusunu Windows'ta (geliştirme makinesi) başlatır. Ayarlar docker-compose.yml ile aynı.
# Kullanım (Pilot klasöründe):  powershell -ExecutionPolicy Bypass -File qdrant\start_windows.ps1
# İkili yoksa önce README.md'deki indirme adımı. Depo: data\qdrant_server\ (git dışı). Durdurmak: Ctrl+C.
param([string]$Version = "v1.19.2")
$pilot = Split-Path -Parent $PSScriptRoot
$exe = Join-Path $pilot "tools\qdrant\$Version\qdrant.exe"
if (-not (Test-Path $exe)) { Write-Error "Qdrant ikilisi yok: $exe (README.md: indirme)"; exit 1 }
$data = Join-Path $pilot "data\qdrant_server"
New-Item -ItemType Directory -Force (Join-Path $data "storage"), (Join-Path $data "snapshots") | Out-Null
$env:QDRANT__STORAGE__STORAGE_PATH = Join-Path $data "storage"
$env:QDRANT__STORAGE__SNAPSHOTS_PATH = Join-Path $data "snapshots"
$env:QDRANT__SERVICE__HOST = "127.0.0.1"
$env:QDRANT__SERVICE__HTTP_PORT = "6333"
$env:QDRANT__SERVICE__GRPC_PORT = "6334"
$env:QDRANT__TELEMETRY_DISABLED = "true"
$env:QDRANT__LOG_LEVEL = "INFO"
Set-Location $data
& $exe
