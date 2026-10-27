# Aşama 3 kuru çalıştırma: 300 parçalık örnek (150 gerçek + 150 dikkat dağıtıcı), bulut embed (Qwen3-8B), yerel Qdrant sunucusu.
# Kaldığı yerden devam denemesi: önce 2 toplu işte durur, sonra sürdürür. Maliyet ~0,0005 USD.
# Kullanım (Pilot klasöründe): powershell -ExecutionPolicy Bypass -File bench\run_asama3_kuru.ps1
$ErrorActionPreference = "Continue"
$env:PYTHONUTF8 = "1"
$env:PILOT_QDRANT_URL = "http://127.0.0.1:6333"
$py = "C:\Users\egitim.YESIM\Desktop\visual_agent_repo\.venv\Scripts\python.exe"
$log = "data\logs\bench_asama3_kuru.log"
function Step($title, [string[]]$a) {
    "$(Get-Date -Format HH:mm:ss) == $title" | Out-File $log -Append -Encoding utf8
    & $py @a 2>&1 | ForEach-Object { "$_" } | Out-File $log -Append -Encoding utf8
}
"$(Get-Date -Format HH:mm:ss) == BAŞLADI" | Out-File $log -Encoding utf8
& $py -c "from bench.server import server_client as s; c=s(); [c.delete_collection(n) for n in ('scale_kuru','scale_kuru_100') if c.collection_exists(n)]"
Remove-Item data\scale\progress\scale_kuru* -ErrorAction SilentlyContinue
Step "korpus" @("-m","bench.scale_corpus","build","--target","300","--tiers","100,300","--real-sample","150","--out","data/scale/corpus_kuru","--force")
Step "indeks: 2 toplu işte dur" @("-m","bench.scale_index","index","--corpus","data/scale/corpus_kuru","--collection","scale_kuru","--workers","4","--batch","32","--stop-after","2")
Step "durum" @("-m","bench.scale_index","status","--collection","scale_kuru")
Step "indeks: kaldığı yerden" @("-m","bench.scale_index","index","--corpus","data/scale/corpus_kuru","--collection","scale_kuru","--workers","4","--batch","32")
Step "indeks: tekrar (iş kalmamalı)" @("-m","bench.scale_index","index","--corpus","data/scale/corpus_kuru","--collection","scale_kuru","--workers","4","--batch","32")
Step "durum" @("-m","bench.scale_index","status","--collection","scale_kuru")
Step "kademe kopyası (≤100)" @("-m","bench.scale_index","copy","--source","scale_kuru","--target","scale_kuru_100","--max-kademe","100")
Step "durum" @("-m","bench.scale_index","status","--collection","scale_kuru_100")
Step "deneme sorgusu" @("-m","bench.scale_index","probe","--collection","scale_kuru","--query","Ceketin dış görünür dikişlerinde inç başına kaç dikiş olmalı?")
Step "deneme sorgusu (Türkçe dikkat dağıtıcı)" @("-m","bench.scale_index","probe","--collection","scale_kuru","--query","Dikiş makinesi nasıl çalışır?")
"$(Get-Date -Format HH:mm:ss) == BİTTİ" | Out-File $log -Append -Encoding utf8
