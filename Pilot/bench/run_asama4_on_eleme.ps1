# B4 embedding karşılaştırması, adım 1 (2026-11-03): 10k kademesinde aday listeleri, bulut çağrısı yok (--offline).
# A: Qwen3-8B + BM25, 256'lık ön eleme (SHORT_OVERSAMPLE 4 = bugünkü değer, 8, 16, 32); B: Qwen3-8B + BM25 tam vektör;
# C: bge-m3 + BM25 tam vektör. Bilinen setler + onaysız aday taslak (yalnız bilgi amaçlı). Rerank yok.
# Kullanım (Pilot klasöründe, yerel Qdrant sunucusu açık): powershell -ExecutionPolicy Bypass -File bench\run_asama4_on_eleme.ps1
$ErrorActionPreference = "Continue"
$env:PYTHONUTF8 = "1"
$env:PYTHONUNBUFFERED = "1"
$env:PILOT_QDRANT_URL = "http://127.0.0.1:6333"
$py = "C:\Users\egitim.YESIM\Desktop\visual_agent_repo\.venv\Scripts\python.exe"
$log = "data\logs\bench_asama4_on_eleme.log"
function Run($title, [string[]]$a) {
    "$(Get-Date -Format HH:mm:ss) == $title" | Out-File $log -Append -Encoding utf8
    & $py @a 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch "HTTP Request" } | Out-File $log -Append -Encoding utf8
}
"$(Get-Date -Format HH:mm:ss) == BAŞLADI" | Out-File $log -Append -Encoding utf8
$common = @("-m","bench.providers","collect","--sets","questions","questions_ek","sekil_sorular","aday_sorular",
            "--include-unapproved","--offline","--repeats","1")
$qwen = $common + @("--key","qwen3-8b","--collection","scale_qwen3_8b_10000")
foreach ($o in 4, 8, 16, 32) {
    $env:PILOT_SHORT_OVERSAMPLE = "$o"
    Run "A: Qwen3-8B + BM25, ön eleme 256, oversample $o" ($qwen + @("--dense","short_rescore","--tag","on_eleme10k_qwen_s$o"))
}
Remove-Item Env:\PILOT_SHORT_OVERSAMPLE
Run "B: Qwen3-8B + BM25, tam vektör" ($qwen + @("--dense","full","--tag","on_eleme10k_qwen_full"))
Run "C: bge-m3 + BM25, tam vektör" ($common + @("--key","bge-m3-local-bm25","--collection","scale_bge_m3_10000","--dense","full","--tag","on_eleme10k_bge_full"))
Run "karşılaştırma" @("-m","bench.prefilter_diff","--ref","on_eleme10k_qwen_full",
                      "--vs","on_eleme10k_qwen_s4","on_eleme10k_qwen_s8","on_eleme10k_qwen_s16","on_eleme10k_qwen_s32",
                      "--extra","on_eleme10k_bge_full")
"$(Get-Date -Format HH:mm:ss) == BİTTİ" | Out-File $log -Append -Encoding utf8
