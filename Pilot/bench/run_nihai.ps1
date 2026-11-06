# Adım 2 nihai tur (plan §20, onay 2026-11-05 gece): bir koşu birimi (paralel başlatılır; her yapılandırma ayrı süreç).
# Bütçe: nihai_* dosyaları toplamı 3,0 USD (aşılacaksa durur). Arama önbellekten (önce --prepare yapıldı); Qdrant gerekmez.
# Birimler:
#   şema C, tam set:                -Tag nihai_c -Schema c -Models gemma4      (8 yapılandırmanın her biri ayrı)
#   bugünkü şema, tam set:          -Tag nihai_bugun -Netlestirme dahil -Models gemma4   (ve gemma4_31b)
#   bugünkü şema, yalnız netleşt.:  -Tag nihai_bugun -Netlestirme yalniz -Models "qwen36,gpt54mini,mistral2603"
#   süre turu (C, 30 soru):         -Tag nihai_sure1 -Schema c -N 30 -Models "..."
# Kullanım (Pilot klasöründe): powershell -ExecutionPolicy Bypass -File bench\run_nihai.ps1 -Tag nihai_c -Schema c -Models gemma4
param([string]$Tag, [string]$Models, [string]$Schema = "bugun", [string]$Netlestirme = "", [int]$N = 0)
Set-Location (Split-Path -Parent $PSScriptRoot)
$ErrorActionPreference = "Continue"
$env:PYTHONUTF8 = "1"
$env:PILOT_ANSWER_MODE = "bugun"   # ölçüm araçlarında kip açıkça (bench/__init__.py)
$env:PYTHONUNBUFFERED = "1"
$env:OPENROUTER_API_KEY = [Environment]::GetEnvironmentVariable("OPENROUTER_API_KEY", "User")
$py = "C:\Users\egitim.YESIM\Desktop\visual_agent_repo\.venv\Scripts\python.exe"
$log = "data\logs\bench_${Tag}_$($Models -replace ',', '-').log"
$a = @("-m", "bench.answer_models", "--tag", $Tag, "--schema", $Schema, "--n", $N, "--max-usd", "3.0", "--models") + ($Models -split ",")
if ($Netlestirme) { $a += @("--netlestirme", $Netlestirme) }
"$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') == BAŞLADI $Tag $Schema $Models $Netlestirme" | Out-File $log -Append -Encoding utf8
& $py @a 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch "HTTP Request" } | Out-File $log -Append -Encoding utf8
"$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') == BİTTİ $Tag $Models (çıkış $LASTEXITCODE)" | Out-File $log -Append -Encoding utf8
