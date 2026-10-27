# Aşama 4: bulut embedding koleksiyonlarını kur (bench.providers build). Qdrant sunucusu açık olmalı.
# Kullanım (Pilot klasöründe): powershell -ExecutionPolicy Bypass -File bench\run_asama4_build.ps1
$ErrorActionPreference = "Continue"
$env:PYTHONUTF8 = "1"
$env:OPENROUTER_API_KEY = [Environment]::GetEnvironmentVariable("OPENROUTER_API_KEY", "User")
$py = "C:\Users\egitim.YESIM\Desktop\visual_agent_repo\.venv\Scripts\python.exe"
$log = "data\logs\bench_asama4_build.log"
foreach ($k in "bge-m3-or", "qwen3-8b", "qwen3-4b", "gemini-001", "te3-large", "me5-large") {
    "$(Get-Date -Format HH:mm:ss) == build $k" | Out-File $log -Append -Encoding utf8
    & $py -m bench.providers build --key $k 2>&1 | ForEach-Object { "$_" } | Out-File $log -Append -Encoding utf8
}
"$(Get-Date -Format HH:mm:ss) == BİTTİ" | Out-File $log -Append -Encoding utf8
