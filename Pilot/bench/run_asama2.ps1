# Aşama 2 ölçüm serisi: gömülü ve sunucu modu, HTTP ve gRPC, access filtresi. Qdrant sunucusu açık olmalı
# (qdrant\start_windows.ps1) ve koleksiyonlar kopyalanmış olmalı (python -m bench.server copy ...).
# Kullanım (Pilot klasöründe): powershell -ExecutionPolicy Bypass -File bench\run_asama2.ps1
$ErrorActionPreference = "Continue"
$env:PYTHONUTF8 = "1"
$py = "C:\Users\egitim.YESIM\Desktop\visual_agent_repo\.venv\Scripts\python.exe"
$log = "data\logs\bench_asama2.log"
function Run($name, [string[]]$extra, [hashtable]$envs) {
    foreach ($k in "PILOT_QDRANT_URL", "PILOT_QDRANT_GRPC", "PILOT_COLLECTION") { Remove-Item "Env:$k" -ErrorAction SilentlyContinue }
    foreach ($k in $envs.Keys) { Set-Item "Env:$k" $envs[$k] }
    "$(Get-Date -Format HH:mm:ss) == $name" | Add-Content $log -Encoding UTF8
    # Out-File -Encoding utf8: PowerShell 5'in *>> yönlendirmesi UTF-16 yazar; log tek kodlamada kalsın
    & $py -m bench.measure --name $name @extra 2>&1 | ForEach-Object { "$_" } | Out-File $log -Append -Encoding utf8
}
$srv = @{ PILOT_QDRANT_URL = "http://127.0.0.1:6333" }
$q = @("--no-rerank", "--repeats", "5", "--unfiltered", "--recall-queries", "500")
Run "asama2_gomulu" $q @{}
Run "asama2_sunucu_http" $q $srv
Run "asama2_sunucu_grpc" $q @{ PILOT_QDRANT_URL = "http://127.0.0.1:6333"; PILOT_QDRANT_GRPC = "1" }
Run "asama2_access_hepsi_all" ($q + @("--access", "g1")) $srv
Run "asama2_access_yapay_filtresiz" $q @{ PILOT_QDRANT_URL = "http://127.0.0.1:6333"; PILOT_COLLECTION = "manuals_access" }
Run "asama2_access_yapay_g1" ($q + @("--access", "g1")) @{ PILOT_QDRANT_URL = "http://127.0.0.1:6333"; PILOT_COLLECTION = "manuals_access" }
Run "asama2_sunucu_rerank" @("--timing-sets", "questions", "--repeats", "3", "--recall-queries", "0") $srv
"$(Get-Date -Format HH:mm:ss) == BİTTİ" | Add-Content $log -Encoding UTF8
