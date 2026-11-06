# Aşama 4: embedding × reranker kombinasyonları (aynı aday listesi üzerinde rerank; rerank'sız satır da tabloda).
# Kullanım (Pilot klasöründe): powershell -ExecutionPolicy Bypass -File bench\run_asama4_rerank.ps1 [-Keys ...]
param([string[]]$Keys = @("bge-m3-local_full", "bge-m3-local-bm25_full", "qwen3-8b_full", "te3-large_full"))
$ErrorActionPreference = "Continue"
$env:PYTHONUTF8 = "1"
$env:PILOT_ANSWER_MODE = "bugun"   # ölçüm araçlarında kip açıkça (bench/__init__.py)
$env:OPENROUTER_API_KEY = [Environment]::GetEnvironmentVariable("OPENROUTER_API_KEY", "User")
$py = "C:\Users\egitim.YESIM\Desktop\visual_agent_repo\.venv\Scripts\python.exe"
$log = "data\logs\bench_asama4_rerank.log"
$configs = @("local:BAAI/bge-reranker-v2-m3:onnx-int8:512:4", "local:jinaai/jina-reranker-v2-base-multilingual:torch:512:4",
             "openrouter:qwen/qwen3-reranker-8b")
foreach ($k in $Keys) {
    "$(Get-Date -Format HH:mm:ss) == rerank $k" | Out-File $log -Append -Encoding utf8
    & $py -m bench.rerank_bench compare --name "asama4_rerank_$k" --candidates "data\bench_cache\candidates_$k.json" `
        --modes filtered unfiltered --configs @configs 2>&1 | ForEach-Object { "$_" } | Out-File $log -Append -Encoding utf8
}
"$(Get-Date -Format HH:mm:ss) == BİTTİ" | Out-File $log -Append -Encoding utf8
