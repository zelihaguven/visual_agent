# Bölüm adı düzeltmesi (2026-11-03): gerçek 4.232 parçalık koleksiyonlarda yalnız embed_text'i değişen noktalar
# yeniden gömülür (sınırlar ve kimlikler aynı), önce/sonra rerank'sız aday listeleri karşılaştırılır.
# Koleksiyonlar: manuals (uygulama, bge-m3 + sparse + BM25), emb_bge-m3-local-bm25 (dense manuals'tan), emb_qwen3-8b
# (bulut, ~606 parça, ~0,001 USD). Sorgu vektörleri önbellekten (--offline). Ölçek koleksiyonlarına ve pakete dokunmaz.
# Kullanım (Pilot klasöründe, yerel Qdrant sunucusu açık): powershell -ExecutionPolicy Bypass -File bench\run_bolum_duzeltme.ps1 <alt küme klasörü>
param([Parameter(Mandatory = $true)][string]$SubsetDir)
$ErrorActionPreference = "Continue"
$env:PYTHONUTF8 = "1"
$env:PYTHONUNBUFFERED = "1"
$env:PILOT_QDRANT_URL = "http://127.0.0.1:6333"
$py = "C:\Users\egitim.YESIM\Desktop\visual_agent_repo\.venv\Scripts\python.exe"
$log = "data\logs\bench_bolum_duzeltme.log"
function Run($title, [string[]]$a) {
    "$(Get-Date -Format HH:mm:ss) == $title" | Out-File $log -Append -Encoding utf8
    & $py @a 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch "HTTP Request" } | Out-File $log -Append -Encoding utf8
    if ($LASTEXITCODE -ne 0) { "$(Get-Date -Format HH:mm:ss) == DURDU: $title (çıkış $LASTEXITCODE)" | Out-File $log -Append -Encoding utf8; exit 1 }
}
"$(Get-Date -Format HH:mm:ss) == BAŞLADI" | Out-File $log -Append -Encoding utf8
$common = @("-m","bench.providers","collect","--sets","questions","questions_ek","sekil_sorular","aday_sorular",
            "--include-unapproved","--offline","--repeats","1")
$qwen = $common + @("--key","qwen3-8b","--dense","short_rescore")
$bge = $common + @("--key","bge-m3-local-bm25","--dense","full")
Run "önce: Qwen3-8B + BM25 (emb_qwen3-8b)" ($qwen + @("--tag","bolum_once_qwen"))
Run "önce: bge-m3 + BM25 (emb_bge-m3-local-bm25)" ($bge + @("--tag","bolum_once_bge"))
Run "kuru: chunks.jsonl ve manuals" @("run_rechunk.py","--changed-only","--dry-run")
Run "chunks.jsonl + manuals (bge-m3, CPU)" @("run_rechunk.py","--changed-only")
Run "emb_bge-m3-local-bm25 (dense manuals'tan)" @("-m","bench.providers","refresh","--key","bge-m3-local-bm25")
Run "emb_qwen3-8b (bulut)" @("-m","bench.providers","refresh","--key","qwen3-8b")
Run "sonra: Qwen3-8B + BM25" ($qwen + @("--tag","bolum_sonra_qwen"))
Run "sonra: bge-m3 + BM25" ($bge + @("--tag","bolum_sonra_bge"))
Run "rapor" @("-m","bench.candidate_report","--name","asama4_bolum_duzeltme_gercek",
              "--title","Bölüm adı düzeltmesi: gerçek 4.232 parça, önce/sonra (rerank'sız)",
              "--runs","Qwen3-8B + BM25=önce:bolum_once_qwen,sonra:bolum_sonra_qwen",
                      "bge-m3 + BM25=önce:bolum_once_bge,sonra:bolum_sonra_bge",
              "--subset","etkilenen 34=$SubsetDir\etkilenen34.json","bölümü değişen 16=$SubsetDir\bolumu_degisen.json")
"$(Get-Date -Format HH:mm:ss) == BİTTİ" | Out-File $log -Append -Encoding utf8
