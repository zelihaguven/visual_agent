# Üçlü füzyon + reranker (2026-11-03): 10k, filtreli/filtresiz, qwen3-reranker-8b (başlıklı metin + RRF birleşimi);
# aday listeleri: üçlü füzyon (cv_uclu) ve BM25'i çevirili üçlü füzyon (cv_uclu_tr). Harcama 1 USD'yi geçerse durur.
# Kullanım (Pilot klasöründe, yerel Qdrant sunucusu açık): powershell -ExecutionPolicy Bypass -File bench\run_asama4_rerank_uclu.ps1
$ErrorActionPreference = "Continue"
$env:PYTHONUTF8 = "1"
$env:PYTHONUNBUFFERED = "1"
$env:PILOT_QDRANT_URL = "http://127.0.0.1:6333"
$env:OPENROUTER_API_KEY = [Environment]::GetEnvironmentVariable("OPENROUTER_API_KEY", "User")
$py = "C:\Users\egitim.YESIM\Desktop\visual_agent_repo\.venv\Scripts\python.exe"
$log = "data\logs\bench_asama4_rerank_uclu.log"
$limit = 1.0
function Run($title, [string[]]$a) {
    "$(Get-Date -Format HH:mm:ss) == $title" | Out-File $log -Append -Encoding utf8
    & $py @a 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch "HTTP Request" } | Out-File $log -Append -Encoding utf8
    if ($LASTEXITCODE -ne 0) { "$(Get-Date -Format HH:mm:ss) == DURDU: $title (çıkış $LASTEXITCODE)" | Out-File $log -Append -Encoding utf8; exit 1 }
}
function Spent() {
    $code = "import glob,json; print(round(sum((x.get('cost_usd') or 0) for f in glob.glob('eval/bench/b4/asama4_rerank10k_uclu*_*.json') for c in json.load(open(f,encoding='utf-8'))['configs'].values() for m in c.values() for x in m['rows']),4))"
    return [double](& $py -c $code)
}
"$(Get-Date -Format HH:mm:ss) == BAŞLADI" | Out-File $log -Append -Encoding utf8
foreach ($p in "uclu", "uclu_tr") {
    $s = Spent
    "$(Get-Date -Format HH:mm:ss) harcama şimdiye kadar: $s USD" | Out-File $log -Append -Encoding utf8
    if ($s -gt $limit) { "$(Get-Date -Format HH:mm:ss) == DURDU: harcama $s USD > $limit USD" | Out-File $log -Append -Encoding utf8; exit 1 }
    Run "reranker: $p" @("-m","bench.rerank_bench","compare","--name","asama4_rerank10k_$p",
                         "--candidates","data\bench_cache\candidates_cv_$p.json","--modes","filtered","unfiltered",
                         "--configs","openrouter:qwen/qwen3-reranker-8b@embed")
}
"$(Get-Date -Format HH:mm:ss) harcama toplam: $(Spent) USD" | Out-File $log -Append -Encoding utf8
$j = { param($p) (Get-ChildItem "eval\bench\b4\asama4_rerank10k_${p}_2*.json" | Sort-Object LastWriteTime | Select-Object -Last 1).FullName }
Run "özet" @("-m","bench.rerank_report","--name","asama4_rerank10k_uclu_ozet",
             "--title","Üçlü füzyon + reranker, 10k (A + reranker ile karşılaştırma)",
             "--runs","A: Qwen3-8B + BM25=$(& $j 'a')","Üçlü füzyon=$(& $j 'uclu')","Üçlü, BM25 çevirili=$(& $j 'uclu_tr')")
"$(Get-Date -Format HH:mm:ss) == BİTTİ" | Out-File $log -Append -Encoding utf8
