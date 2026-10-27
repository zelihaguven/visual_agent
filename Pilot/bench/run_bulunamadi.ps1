# "Bulunamadı" uçtan uca: yeni varsayılan (rerank yok) ve eski yol (rerank + bge-m3 sparse). Ollama açık olmalı.
# Kullanım (Pilot klasöründe): powershell -ExecutionPolicy Bypass -File bench\run_bulunamadi.ps1
$ErrorActionPreference = "Continue"
$env:PYTHONUTF8 = "1"
$py = "C:\Users\egitim.YESIM\Desktop\visual_agent_repo\.venv\Scripts\python.exe"
$log = "data\logs\bench_bulunamadi.log"
"$(Get-Date -Format HH:mm:ss) == yeni_varsayilan" | Out-File $log -Append -Encoding utf8
& $py -m bench.notfound_e2e run --label yeni_varsayilan 2>&1 | ForEach-Object { "$_" } | Out-File $log -Append -Encoding utf8
"$(Get-Date -Format HH:mm:ss) == eski_rerank" | Out-File $log -Append -Encoding utf8
$env:PILOT_RERANK_PROVIDER = "local"; $env:PILOT_SPARSE = "bge-m3"; $env:PILOT_RERANK_PASSAGE = "text"; $env:PILOT_RERANK_FUSION = "none"
& $py -m bench.notfound_e2e run --label eski_rerank 2>&1 | ForEach-Object { "$_" } | Out-File $log -Append -Encoding utf8
& $py -m bench.notfound_e2e summary 2>&1 | ForEach-Object { "$_" } | Out-File $log -Append -Encoding utf8
"$(Get-Date -Format HH:mm:ss) == BİTTİ" | Out-File $log -Append -Encoding utf8
