# B4 embedding karşılaştırması, adım 2 (2026-11-03): 10k kademesinde 3 yol × filtreli/filtresiz, qwen3-reranker-8b
# (başlıklı metin + RRF birleşimi). Bölüm adı düzeltmesinden sonra; aday set onaysız, sonuçlar geçici.
# A: Qwen3-8B + BM25, 256 ön eleme (bugünkü); B: Qwen3-8B + BM25 tam vektör; C: bge-m3 + BM25.
# Bulut: 36 sorgu vektörü (önbellekte yok) + reranker (~1,1 USD tahmin). Harcama 2,5 USD'yi geçerse durur (sınır 3 USD).
# 1M koleksiyonuna ve sunucu paketine dokunmaz.
# Kullanım (Pilot klasöründe, yerel Qdrant sunucusu açık): powershell -ExecutionPolicy Bypass -File bench\run_asama4_rerank10k.ps1
$ErrorActionPreference = "Continue"
$env:PYTHONUTF8 = "1"
$env:PYTHONUNBUFFERED = "1"
$env:PILOT_QDRANT_URL = "http://127.0.0.1:6333"
$env:OPENROUTER_API_KEY = [Environment]::GetEnvironmentVariable("OPENROUTER_API_KEY", "User")
$py = "C:\Users\egitim.YESIM\Desktop\visual_agent_repo\.venv\Scripts\python.exe"
$log = "data\logs\bench_asama4_rerank10k.log"
$limit = 2.5
function Run($title, [string[]]$a) {
    "$(Get-Date -Format HH:mm:ss) == $title" | Out-File $log -Append -Encoding utf8
    & $py @a 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch "HTTP Request" } | Out-File $log -Append -Encoding utf8
    if ($LASTEXITCODE -ne 0) { "$(Get-Date -Format HH:mm:ss) == DURDU: $title (çıkış $LASTEXITCODE)" | Out-File $log -Append -Encoding utf8; exit 1 }
}
function Spent() {
    $code = "import glob,json; print(round(sum((x.get('cost_usd') or 0) for f in glob.glob('eval/bench/b4/asama4_rerank10k_[abc]_*.json') for c in json.load(open(f,encoding='utf-8'))['configs'].values() for m in c.values() for x in m['rows']),4))"
    return [double](& $py -c $code)
}
"$(Get-Date -Format HH:mm:ss) == BAŞLADI" | Out-File $log -Append -Encoding utf8
Run "10k: bge-m3 gerçek parçalar (dense manuals'tan)" @("-m","bench.providers","refresh","--key","bge-m3-local-bm25","--collection","scale_bge_m3_10000","--partial")
Run "10k: Qwen3-8B gerçek parçalar (önbellekten)" @("-m","bench.providers","refresh","--key","qwen3-8b","--collection","scale_qwen3_8b_10000","--partial")
$common = @("-m","bench.providers","collect","--sets","questions","questions_ek","sekil_sorular","aday_sorular",
            "--include-unapproved","--repeats","1","--timing-sets","yok")
$qwen = $common + @("--key","qwen3-8b","--collection","scale_qwen3_8b_10000")
Run "aday A (36 sorgu vektörü bulutta)" ($qwen + @("--dense","short_rescore","--tag","rr10k_a"))
Run "aday B" ($qwen + @("--dense","full","--tag","rr10k_b"))
Run "aday C" ($common + @("--key","bge-m3-local-bm25","--collection","scale_bge_m3_10000","--dense","full","--tag","rr10k_c"))
foreach ($p in "a", "b", "c") {
    $s = Spent
    "$(Get-Date -Format HH:mm:ss) harcama şimdiye kadar: $s USD" | Out-File $log -Append -Encoding utf8
    if ($s -gt $limit) { "$(Get-Date -Format HH:mm:ss) == DURDU: harcama $s USD > $limit USD" | Out-File $log -Append -Encoding utf8; exit 1 }
    Run "reranker: yol $p" @("-m","bench.rerank_bench","compare","--name","asama4_rerank10k_$p",
                             "--candidates","data\bench_cache\candidates_rr10k_$p.json","--modes","filtered","unfiltered",
                             "--configs","openrouter:qwen/qwen3-reranker-8b@embed")
}
"$(Get-Date -Format HH:mm:ss) harcama toplam: $(Spent) USD" | Out-File $log -Append -Encoding utf8
$j = { param($p) (Get-ChildItem "eval\bench\b4\asama4_rerank10k_${p}_*.json" | Sort-Object LastWriteTime | Select-Object -Last 1).FullName }
Run "özet" @("-m","bench.rerank_report","--name","asama4_rerank10k_ozet",
             "--title","B4 adım 2: 10k, 3 yol, qwen3-reranker-8b (bölüm düzeltmesi sonrası)",
             "--runs","A: Qwen3-8B + BM25, 256 ön eleme=$(& $j 'a')","B: Qwen3-8B + BM25, tam vektör=$(& $j 'b')",
                     "C: bge-m3 + BM25=$(& $j 'c')")
"$(Get-Date -Format HH:mm:ss) == BİTTİ" | Out-File $log -Append -Encoding utf8
