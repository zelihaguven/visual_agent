# Reranker düzeltme denemesi: başlıklı metin (@embed), Qwen talimatı (@inst), RRF füzyonu (her yapılandırmada).
# Kullanım (Pilot klasöründe): powershell -ExecutionPolicy Bypass -File bench\run_rerank_fix.ps1
$ErrorActionPreference = "Continue"
$env:PYTHONUTF8 = "1"
$env:OPENROUTER_API_KEY = [Environment]::GetEnvironmentVariable("OPENROUTER_API_KEY", "User")
$py = "C:\Users\egitim.YESIM\Desktop\visual_agent_repo\.venv\Scripts\python.exe"
$log = "data\logs\bench_rerank_fix.log"
$configs = @("local:BAAI/bge-reranker-v2-m3:onnx-int8:512:4", "local:BAAI/bge-reranker-v2-m3:onnx-int8:512:4@embed",
             "local:jinaai/jina-reranker-v2-base-multilingual:torch:512:4",
             "local:jinaai/jina-reranker-v2-base-multilingual:torch:512:4@embed",
             "openrouter:qwen/qwen3-reranker-8b", "openrouter:qwen/qwen3-reranker-8b@embed",
             "openrouter:qwen/qwen3-reranker-8b@embed@inst")
foreach ($k in "bge-m3-local-bm25_full", "qwen3-8b_full") {
    "$(Get-Date -Format HH:mm:ss) == rerank düzeltme $k" | Out-File $log -Append -Encoding utf8
    & $py -m bench.rerank_bench compare --name "rerank_duzeltme_$k" --candidates "data\bench_cache\candidates_$k.json" `
        --modes filtered unfiltered --configs @configs 2>&1 | ForEach-Object { "$_" } | Out-File $log -Append -Encoding utf8
}
"$(Get-Date -Format HH:mm:ss) == BİTTİ" | Out-File $log -Append -Encoding utf8
