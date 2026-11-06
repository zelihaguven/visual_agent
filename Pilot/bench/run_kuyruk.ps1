# Bulut gecikme kuyruğu ölçümü (bench.tail_probe), Görev Zamanlayıcı'dan çağrılır: gün içinde farklı saatlerde 30'ar çağrı.
# Kullanım: powershell -ExecutionPolicy Bypass -File bench\run_kuyruk.ps1 -Label t1
# Özet: python -m bench.tail_probe --summary
param([string]$Label = "t")
Set-Location (Split-Path -Parent $PSScriptRoot)
$env:PYTHONUTF8 = "1"
$env:PILOT_ANSWER_MODE = "bugun"   # ölçüm araçlarında kip açıkça (bench/__init__.py)
$env:PYTHONUNBUFFERED = "1"
$env:OPENROUTER_API_KEY = [Environment]::GetEnvironmentVariable("OPENROUTER_API_KEY", "User")
$py = "C:\Users\egitim.YESIM\Desktop\visual_agent_repo\.venv\Scripts\python.exe"
$log = "data\logs\bench_kuyruk.log"
"$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') == $Label BAŞLADI" | Out-File $log -Append -Encoding utf8
& $py -m bench.tail_probe --label $Label --max-usd 0.3 2>&1 | ForEach-Object { "$_" } | Out-File $log -Append -Encoding utf8
"$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') == $Label BİTTİ (çıkış $LASTEXITCODE)" | Out-File $log -Append -Encoding utf8
