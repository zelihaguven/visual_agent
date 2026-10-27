# Aşama 3b dizüstünde (kullanıcı kararı 2026-10-27): kalabalıkta doğruluk, 10k → 1M. Doğruluk donanımdan bağımsız;
# bu koşunun süreleri "dizüstü, üretimi temsil etmez" diye işaretlenir, karar için kullanılmaz.
# Kullanım (Pilot klasöründe, yerel Qdrant sunucusu açık): powershell -ExecutionPolicy Bypass -File bench\run_asama3_yerel.ps1 <adım>
#   korpus     1M korpus (big_patent D/F + Vikipedi en/tr; ~2 GB parquet indirme)
#   qwen10k    Qwen3-8B, ilk 10k kademesi (gerçek hız ve maliyet → devam kararı)
#   qwen       Qwen3-8B, 1M'e kadar (harcama sınırı 3 USD, önceki koşular dahil)
#   kademeler  Qwen3-8B kopyaları: gerçek (≤0), 10k, 30k, 100k
#   yerel10k   local yol bge-m3 + BM25, 10k (gerçek parçaların vektörleri hazır; ~5.800 dikkat dağıtıcı CPU'da)
#   yerel30k   aynı koleksiyonu 30k'ya tamamlar (CPU'da birkaç saat; isteğe bağlı)
#   olcum      3b doğruluk: bütün kademeler, filtreli + filtresiz, rerank'sız
param([Parameter(Mandatory = $true)][string]$Step)
$ErrorActionPreference = "Continue"
$env:PYTHONUTF8 = "1"
$env:PYTHONUNBUFFERED = "1"
$env:PILOT_QDRANT_URL = "http://127.0.0.1:6333"
$env:PILOT_QDRANT_GRPC = "1"
$py = "C:\Users\egitim.YESIM\Desktop\visual_agent_repo\.venv\Scripts\python.exe"
$log = "data\logs\bench_asama3.log"
function Run($title, [string[]]$a) {
    "$(Get-Date -Format HH:mm:ss) == $title" | Out-File $log -Append -Encoding utf8
    & $py @a 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch "HTTP Request" } | Out-File $log -Append -Encoding utf8
}
$qwen = @("-m","bench.scale_index","index","--collection","scale_qwen3_8b","--embed","qwen3-8b","--workers","16")
$bge = @("-m","bench.scale_index","index","--collection","scale_bge_m3","--embed","bge-m3-local","--device","cpu","--workers","1","--batch","32","--reuse-real","data/scale/real_bge_m3.npz")
switch ($Step) {
    "korpus"    { Run "korpus 1M" @("-m","bench.scale_corpus","build") }
    "qwen10k"   { Run "Qwen3-8B ≤10k" ($qwen + @("--max-kademe","10000")) }
    "qwen"      { Run "Qwen3-8B 1M" $qwen }
    "kademeler" {
        foreach ($k in 0, 10000, 30000, 100000) {
            $n = if ($k -eq 0) { "gercek" } else { "$k" }
            Run "kopya ≤$k" @("-m","bench.scale_index","copy","--source","scale_qwen3_8b","--target","scale_qwen3_8b_$n","--max-kademe","$k")
        }
    }
    "yerel10k"  {
        Run "bge-m3 + BM25 ≤10k" ($bge + @("--max-kademe","10000"))
        Run "kopya ≤0" @("-m","bench.scale_index","copy","--source","scale_bge_m3","--target","scale_bge_m3_gercek","--max-kademe","0")
        Run "kopya ≤10000" @("-m","bench.scale_index","copy","--source","scale_bge_m3","--target","scale_bge_m3_10000","--max-kademe","10000")
    }
    "yerel30k"  { Run "bge-m3 + BM25 ≤30k" ($bge + @("--max-kademe","30000")) }
    "olcum"     {
        foreach ($c in "scale_qwen3_8b_gercek","scale_qwen3_8b_10000","scale_qwen3_8b_30000","scale_qwen3_8b_100000","scale_qwen3_8b","scale_bge_m3_gercek","scale_bge_m3_10000","scale_bge_m3") {
            Run "3b doğruluk $c" @("-m","bench.measure","--scale-collection",$c,"--name","asama3b_$c","--no-rerank","--unfiltered","--repeats","1","--warmup","3","--recall-queries","300")
        }
    }
    default { "bilinmeyen adım: $Step"; exit 1 }
}
"$(Get-Date -Format HH:mm:ss) == $Step BİTTİ" | Out-File $log -Append -Encoding utf8
