# BM25 sorgu çevirisi, model ve sağlayıcı etkisi (Adım 2 planı §14, onay 2026-11-05): Gemma 3 DeepInfra / Gemma 3 NextBit /
# Gemma 4 NextBit. Tur t1: çeviri + süre, sonra her kolun çevirisiyle BM25 isabeti (yalnız BM25 ve üçlü füzyon, 10k,
# yerel Qdrant, bulutsuz) ve rapor. Sonraki turlar (başka saatte): yalnız çeviri + süre, süre raporu bütün turlarla.
# Kullanım (Pilot klasöründe, Qdrant sunucusu açık):
#   powershell -ExecutionPolicy Bypass -File bench\run_ceviri_karsilastirma.ps1 -Pass t1
#   powershell -ExecutionPolicy Bypass -File bench\run_ceviri_karsilastirma.ps1 -Pass t2 -Report "t1,t2"
param([string]$Pass = "t1", [string]$Report = "")
Set-Location (Split-Path -Parent $PSScriptRoot)
$ErrorActionPreference = "Continue"
$env:PYTHONUTF8 = "1"
$env:PILOT_ANSWER_MODE = "bugun"   # ölçüm araçlarında kip açıkça (bench/__init__.py)
$env:PYTHONUNBUFFERED = "1"
$env:PILOT_QDRANT_URL = "http://127.0.0.1:6333"
$env:OPENROUTER_API_KEY = [Environment]::GetEnvironmentVariable("OPENROUTER_API_KEY", "User")
$py = "C:\Users\egitim.YESIM\Desktop\visual_agent_repo\.venv\Scripts\python.exe"
$log = "data\logs\bench_ceviri_karsilastirma.log"
function Run($title, [string[]]$a) {
    "$(Get-Date -Format HH:mm:ss) == $title" | Out-File $log -Append -Encoding utf8
    & $py @a 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch "HTTP Request" } | Out-File $log -Append -Encoding utf8
    if ($LASTEXITCODE -ne 0) { "$(Get-Date -Format HH:mm:ss) == DURDU: $title (çıkış $LASTEXITCODE)" | Out-File $log -Append -Encoding utf8; exit 1 }
}
"$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') == BAŞLADI ($Pass)" | Out-File $log -Append -Encoding utf8
Run "çeviri, tur $Pass" @("-m", "bench.translate_compare", "--pass", $Pass, "--max-usd", "0.1")
if ($Pass -eq "t1") {
    $sets = @("--sets", "questions", "questions_ek", "sekil_sorular", "aday_sorular", "--include-unapproved")
    $f = @("-m", "bench.triple_fusion", "--qwen-collection", "scale_qwen3_8b_10000", "--bge-collection", "scale_bge_m3_10000") + $sets
    $arms = @{ "g3di" = "g3_deepinfra"; "g3nb" = "g3_nextbit"; "g4nb" = "g4_nextbit" }
    foreach ($k in $arms.Keys) {
        $tr = @("--bm25-translations", "data\bench_cache\ceviri_cmp_$($arms[$k])_t1.json")
        Run "yalnız BM25, $k" ($f + @("--arms", "bm25", "--tag", "cc_bm25_$k") + $tr)
        Run "üçlü füzyon, $k" ($f + @("--tag", "cc_uclu_$k") + $tr)
    }
    Run "isabet raporu" @("-m", "bench.candidate_report", "--name", "asama4_ceviri_karsilastirma_isabet_10k",
        "--title", "BM25 sorgu çevirisi: Gemma 3 DeepInfra / Gemma 3 NextBit / Gemma 4 NextBit, 10k, rerank'sız",
        "--runs", "Yalnız BM25=g3 DeepInfra:cc_bm25_g3di,g3 NextBit:cc_bm25_g3nb,g4 NextBit:cc_bm25_g4nb",
        "Üçlü füzyon=g3 DeepInfra:cc_uclu_g3di,g3 NextBit:cc_uclu_g3nb,g4 NextBit:cc_uclu_g4nb")
}
if ($Report) { Run "süre raporu" (@("-m", "bench.translate_compare", "--report") + ($Report -split ",")) }
"$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') == BİTTİ ($Pass)" | Out-File $log -Append -Encoding utf8
