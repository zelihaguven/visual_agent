# BM25'e çevrilmiş sorgu (2026-11-03): 10k, filtreli/filtresiz, rerank'sız; A (Qwen3-8B + BM25) ve üçlü füzyon,
# çevirisiz ve çevirili. Çeviri bulut LLM ile (ZDR), harcama sınırı 1 USD; dense sorgu vektörleri önbellekten.
# Kullanım (Pilot klasöründe, yerel Qdrant sunucusu açık): powershell -ExecutionPolicy Bypass -File bench\run_asama4_ceviri.ps1
param([string]$Model = "google/gemma-3-12b-it", [string]$Tag = "ceviri_gemma3_12b")
$ErrorActionPreference = "Continue"
$env:PYTHONUTF8 = "1"
$env:PYTHONUNBUFFERED = "1"
$env:PILOT_QDRANT_URL = "http://127.0.0.1:6333"
$env:OPENROUTER_API_KEY = [Environment]::GetEnvironmentVariable("OPENROUTER_API_KEY", "User")
$py = "C:\Users\egitim.YESIM\Desktop\visual_agent_repo\.venv\Scripts\python.exe"
$log = "data\logs\bench_asama4_ceviri.log"
function Run($title, [string[]]$a) {
    "$(Get-Date -Format HH:mm:ss) == $title" | Out-File $log -Append -Encoding utf8
    & $py @a 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch "HTTP Request" } | Out-File $log -Append -Encoding utf8
    if ($LASTEXITCODE -ne 0) { "$(Get-Date -Format HH:mm:ss) == DURDU: $title (çıkış $LASTEXITCODE)" | Out-File $log -Append -Encoding utf8; exit 1 }
}
"$(Get-Date -Format HH:mm:ss) == BAŞLADI" | Out-File $log -Append -Encoding utf8
$sets = @("--sets","questions","questions_ek","sekil_sorular","aday_sorular","--include-unapproved")
Run "çeviri ($Model)" (@("-m","bench.translate_bm25","--model",$Model,"--tag",$Tag,"--max-usd","1.0") + $sets)
$f = @("-m","bench.triple_fusion","--qwen-collection","scale_qwen3_8b_10000","--bge-collection","scale_bge_m3_10000") + $sets
$tr = @("--bm25-translations","data\bench_cache\$Tag.json")
Run "A, çevirisiz" ($f + @("--arms","qwen,bm25","--tag","cv_a"))
Run "A, BM25 çevirili" ($f + @("--arms","qwen,bm25","--tag","cv_a_tr") + $tr)
Run "üçlü, çevirisiz" ($f + @("--tag","cv_uclu"))
Run "üçlü, BM25 çevirili" ($f + @("--tag","cv_uclu_tr") + $tr)
Run "rapor" @("-m","bench.candidate_report","--name","asama4_ceviri_bm25_10k",
              "--title","BM25'e çevrilmiş sorgu ($Model), 10k, rerank'sız",
              "--runs","A Qwen3-8B + BM25=çevirisiz:cv_a,çevirili:cv_a_tr","Üçlü füzyon=çevirisiz:cv_uclu,çevirili:cv_uclu_tr")
"$(Get-Date -Format HH:mm:ss) == BİTTİ" | Out-File $log -Append -Encoding utf8
