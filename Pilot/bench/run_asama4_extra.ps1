# Aşama 4 ek koşular: te3-large 512 MRL (koleksiyon önbellekten yeniden kurulur, maliyet yok), Nomic v2 MoE (local CPU).
# Kullanım (Pilot klasöründe): powershell -ExecutionPolicy Bypass -File bench\run_asama4_extra.ps1
$ErrorActionPreference = "Continue"
$env:PYTHONUTF8 = "1"
$env:PILOT_ANSWER_MODE = "bugun"   # ölçüm araçlarında kip açıkça (bench/__init__.py)
$env:OPENROUTER_API_KEY = [Environment]::GetEnvironmentVariable("OPENROUTER_API_KEY", "User")
$py = "C:\Users\egitim.YESIM\Desktop\visual_agent_repo\.venv\Scripts\python.exe"
$log = "data\logs\bench_asama4_extra.log"
function Run([string]$title, [string[]]$a) {
    "$(Get-Date -Format HH:mm:ss) == $title" | Out-File $log -Append -Encoding utf8
    & $py -m bench.providers @a 2>&1 | ForEach-Object { "$_" } | Out-File $log -Append -Encoding utf8
}
Run "build bge-m3-local-bm25 (vektörler mevcut indeksten)" @("build", "--key", "bge-m3-local-bm25")
Run "collect bge-m3-local-bm25" @("collect", "--key", "bge-m3-local-bm25", "--dense", "full")
Run "build te3-large (önbellek)" @("build", "--key", "te3-large")
Run "collect te3-large short 512" @("collect", "--key", "te3-large", "--dense", "short", "--short-dim", "512")
Run "collect te3-large short_rescore 512" @("collect", "--key", "te3-large", "--dense", "short_rescore", "--short-dim", "512")
Run "build nomic-v2-moe (CPU)" @("build", "--key", "nomic-v2-moe")
Run "collect nomic full" @("collect", "--key", "nomic-v2-moe", "--dense", "full")
Run "collect nomic short 256" @("collect", "--key", "nomic-v2-moe", "--dense", "short", "--short-dim", "256")
Run "collect nomic short_rescore 256" @("collect", "--key", "nomic-v2-moe", "--dense", "short_rescore", "--short-dim", "256")
$files = Get-ChildItem data\bench_cache\candidates_*_*.json | ForEach-Object { $_.FullName }
Run "özet" (@("summary", "--name", "asama4_embedding") + $files)
"$(Get-Date -Format HH:mm:ss) == BİTTİ" | Out-File $log -Append -Encoding utf8
