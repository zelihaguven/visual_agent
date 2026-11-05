# Adım 2 cevap modeli ölçümü (bench.answer_models), Görev Zamanlayıcı'dan çağrılır: yerel taban (gece) ve ikinci süre turu.
# Arama önbellekten (önce --prepare); Qdrant gerekmez. Bütçe sınırı bütün turların toplamı (1,5 USD).
# Kullanım: powershell -ExecutionPolicy Bypass -File bench\run_adim2.ps1 -Models qwen25_7b
#           powershell -ExecutionPolicy Bypass -File bench\run_adim2.ps1 -Models "gemma4,qwen36,mistral2603,gpt54mini" -Tag sure2 -N 30
param([string]$Models = "qwen25_7b", [string]$Tag = "ana", [int]$N = 0)
Set-Location (Split-Path -Parent $PSScriptRoot)
$env:PYTHONUTF8 = "1"
$env:PYTHONUNBUFFERED = "1"
$env:OPENROUTER_API_KEY = [Environment]::GetEnvironmentVariable("OPENROUTER_API_KEY", "User")
$py = "C:\Users\egitim.YESIM\Desktop\visual_agent_repo\.venv\Scripts\python.exe"
$log = "data\logs\bench_adim2_$Tag.log"
"$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') == $Models ($Tag) BAŞLADI" | Out-File $log -Append -Encoding utf8
& $py -m bench.answer_models --models ($Models -split ",") --tag $Tag --n $N --max-usd 1.5 2>&1 |
    ForEach-Object { "$_" } | Where-Object { $_ -notmatch "HTTP Request" } | Out-File $log -Append -Encoding utf8
"$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') == $Models ($Tag) BİTTİ (çıkış $LASTEXITCODE)" | Out-File $log -Append -Encoding utf8
