# Aşama 4: her embedding modeli için aday toplama (bench.providers collect) ve özet. Qdrant sunucusu açık,
# koleksiyonlar kurulmuş olmalı (run_asama4_build.ps1). Kullanım: powershell -ExecutionPolicy Bypass -File bench\run_asama4_collect.ps1
param([string[]]$Keys = @("bge-m3-local", "bge-m3-or", "qwen3-8b", "qwen3-4b", "gemini-001", "te3-large", "me5-large"),
      [string[]]$MrlKeys = @("qwen3-8b", "te3-large"))
$ErrorActionPreference = "Continue"
$env:PYTHONUTF8 = "1"
$env:OPENROUTER_API_KEY = [Environment]::GetEnvironmentVariable("OPENROUTER_API_KEY", "User")
$py = "C:\Users\egitim.YESIM\Desktop\visual_agent_repo\.venv\Scripts\python.exe"
$log = "data\logs\bench_asama4_collect.log"
function Run([string[]]$a) {
    "$(Get-Date -Format HH:mm:ss) == collect $($a -join ' ')" | Out-File $log -Append -Encoding utf8
    & $py -m bench.providers collect @a 2>&1 | ForEach-Object { "$_" } | Out-File $log -Append -Encoding utf8
}
foreach ($k in $Keys) { Run @("--key", $k, "--dense", "full") }
foreach ($k in $MrlKeys) {
    foreach ($d in 256, 512) {
        Run @("--key", $k, "--dense", "short", "--short-dim", "$d")
        Run @("--key", $k, "--dense", "short_rescore", "--short-dim", "$d")
    }
}
$files = Get-ChildItem data\bench_cache\candidates_*_*.json | ForEach-Object { $_.FullName }
& $py -m bench.providers summary --name asama4_embedding @files 2>&1 | ForEach-Object { "$_" } | Out-File $log -Append -Encoding utf8
"$(Get-Date -Format HH:mm:ss) == BİTTİ" | Out-File $log -Append -Encoding utf8
