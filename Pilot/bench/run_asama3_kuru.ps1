# Aşama 3 kuru çalıştırma (yerel, küçük örnek): korpus + Qwen3-8B indeksi (300 parça, kaldığı yerden devam),
# 3a sentetik (2.000 nokta), sorgu vektörleri, gecikme, 3c yük ve 3b doğruluk. Bulut maliyeti ~0,001 USD.
# Docker'a bağlı adım (bench.scale_bench limits) yerelde denenmez; VM'de ilk iş.
# Kullanım (Pilot klasöründe, yerel Qdrant sunucusu açık): powershell -ExecutionPolicy Bypass -File bench\run_asama3_kuru.ps1
$ErrorActionPreference = "Continue"
$env:PYTHONUTF8 = "1"
$env:PYTHONUNBUFFERED = "1"     # günlük satırları adım bitmeden yazılsın
$env:PILOT_QDRANT_URL = "http://127.0.0.1:6333"
$py = "C:\Users\egitim.YESIM\Desktop\visual_agent_repo\.venv\Scripts\python.exe"
$log = "data\logs\bench_asama3_kuru.log"
function Step($title, [string[]]$a) {
    "$(Get-Date -Format HH:mm:ss) == $title" | Out-File $log -Append -Encoding utf8
    & $py @a 2>&1 | ForEach-Object { "$_" } | Out-File $log -Append -Encoding utf8
}
"$(Get-Date -Format HH:mm:ss) == BAŞLADI" | Out-File $log -Encoding utf8
# Her denemede yeni koleksiyon adı: Windows'taki Qdrant ikilisi silinen koleksiyonun klasörünü hemen bırakmıyor,
# aynı adla yeniden oluşturma "Collection data already exists" veriyor (Linux VM'de yok)
$k = "kuru$(Get-Date -Format HHmm)"
Step "korpus" @("-m","bench.scale_corpus","build","--target","300","--tiers","100,300","--real-sample","150","--out","data/scale/corpus_kuru","--force")
Step "indeks: 2 toplu işte dur" @("-m","bench.scale_index","index","--corpus","data/scale/corpus_kuru","--collection","scale_$k","--workers","4","--batch","32","--stop-after","2")
Step "indeks: kaldığı yerden" @("-m","bench.scale_index","index","--corpus","data/scale/corpus_kuru","--collection","scale_$k","--workers","4","--batch","32")
Step "indeks: tekrar (iş kalmamalı)" @("-m","bench.scale_index","index","--corpus","data/scale/corpus_kuru","--collection","scale_$k","--workers","4","--batch","32")
Step "kademe kopyası (≤100)" @("-m","bench.scale_index","copy","--source","scale_$k","--target","scale_${k}_100","--max-kademe","100")
Step "durum" @("-m","bench.scale_index","status","--collection","scale_$k")
Step "deneme sorgusu" @("-m","bench.scale_index","probe","--collection","scale_$k","--query","Ceketin dış görünür dikişlerinde inç başına kaç dikiş olmalı?")
Step "3a: gerçek vektörleri dışa aktar" @("-m","bench.scale_synth","export")
$env:PILOT_QDRANT_GRPC = "1"
Step "3a: sentetik 2.000 (gRPC)" @("-m","bench.scale_synth","build","--n","2000","--collection","synth_$k","--workers","2")
Step "3a: kaldığı yerden (iş kalmamalı)" @("-m","bench.scale_synth","build","--n","2000","--collection","synth_$k","--workers","2")
Step "3a: kopya ≤10k" @("-m","bench.scale_index","copy","--source","synth_$k","--target","synth_${k}_10k","--max-kademe","10000")
Remove-Item Env:\PILOT_QDRANT_GRPC
Step "sorgular (Qwen3-8B, bulut)" @("-m","bench.scale_bench","queries","--collection","scale_$k")
Step "sorgular (bge-m3, yerel)" @("-m","bench.scale_bench","queries","--collection","synth_$k")
Step "gecikme sentetik" @("-m","bench.scale_bench","latency","--collection","synth_$k","--label","kuru","--repeats","1","--warmup","3","--recall-queries","30")
Step "gecikme qwen" @("-m","bench.scale_bench","latency","--collection","scale_$k","--label","kuru","--repeats","1","--warmup","3","--recall-queries","30")
Step "3c yük qdrant" @("-m","bench.load_test","--collection","scale_$k","--mode","qdrant","--users","1,4","--duration","5","--procs","2","--label","kuru")
Step "3c yük e2e" @("-m","bench.load_test","--collection","scale_$k","--mode","e2e","--users","2","--think","1","--duration","5","--procs","1","--label","kuru")
Step "3b doğruluk (qwen)" @("-m","bench.measure","--scale-collection","scale_$k","--name","kuru_asama3b","--no-rerank","--unfiltered","--repeats","1","--warmup","1","--recall-queries","30")
"$(Get-Date -Format HH:mm:ss) == BİTTİ" | Out-File $log -Append -Encoding utf8
