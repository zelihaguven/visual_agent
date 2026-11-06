# Parça bazında dil tespiti (2026-11-03): chunks.jsonl yeniden yazılır; parça sınırı değişen doküman (Mr. Coffee)
# bütün gerçek-parça koleksiyonlarında yenisiyle değiştirilir, öteki dokümanlarda yalnız 'lang' payload'ı eşitlenir.
# Bulut: Qwen3-8B'de yalnız yeni metinler (~0,0002 USD). 1M koleksiyonuna ve sunucu paketine dokunmaz.
# Kullanım (Pilot klasöründe, yerel Qdrant sunucusu açık): powershell -ExecutionPolicy Bypass -File bench\run_dil_tespiti.ps1 <yedek klasörü>
param([Parameter(Mandatory = $true)][string]$BackupDir, [string]$Doc = "mrcoffee-2003")
$ErrorActionPreference = "Continue"
$env:PYTHONUTF8 = "1"
$env:PILOT_ANSWER_MODE = "bugun"   # ölçüm araçlarında kip açıkça (bench/__init__.py)
$env:PYTHONUNBUFFERED = "1"
$env:PILOT_QDRANT_URL = "http://127.0.0.1:6333"
$env:OPENROUTER_API_KEY = [Environment]::GetEnvironmentVariable("OPENROUTER_API_KEY", "User")
$py = "C:\Users\egitim.YESIM\Desktop\visual_agent_repo\.venv\Scripts\python.exe"
$log = "data\logs\bench_dil_tespiti.log"
function Run($title, [string[]]$a) {
    "$(Get-Date -Format HH:mm:ss) == $title" | Out-File $log -Append -Encoding utf8
    & $py @a 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch "HTTP Request" } | Out-File $log -Append -Encoding utf8
    if ($LASTEXITCODE -ne 0) { "$(Get-Date -Format HH:mm:ss) == DURDU: $title (çıkış $LASTEXITCODE)" | Out-File $log -Append -Encoding utf8; exit 1 }
}
"$(Get-Date -Format HH:mm:ss) == BAŞLADI" | Out-File $log -Append -Encoding utf8
Copy-Item data\chunks.jsonl (Join-Path $BackupDir "chunks_dil_oncesi.jsonl") -Force
Run "kuru: run_rechunk" @("run_rechunk.py", "--dry-run")
Run "chunks.jsonl + manuals (sınırı değişen doküman yeniden gömülür, ötekilerde payload)" @("run_rechunk.py")
Run "emb_bge-m3-local-bm25" @("-m","bench.providers","replace-doc","--key","bge-m3-local-bm25","--doc",$Doc)
Run "emb_qwen3-8b" @("-m","bench.providers","replace-doc","--key","qwen3-8b","--doc",$Doc)
Run "scale_bge_m3_10000" @("-m","bench.providers","replace-doc","--key","bge-m3-local-bm25","--doc",$Doc,"--collection","scale_bge_m3_10000","--scale")
Run "scale_qwen3_8b_10000" @("-m","bench.providers","replace-doc","--key","qwen3-8b","--doc",$Doc,"--collection","scale_qwen3_8b_10000","--scale")
"$(Get-Date -Format HH:mm:ss) == BİTTİ" | Out-File $log -Append -Encoding utf8
