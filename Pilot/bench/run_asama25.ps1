# Aşama 2.5: önce ölçümü (eski indeks) → yeniden parçalama ve indeksleme → sonra ölçümü → kayıp analizi →
# sunucuya kopya → mod farkı. Qdrant sunucusu açık olmalı (qdrant\start_windows.ps1).
# Kullanım (Pilot klasöründe): powershell -ExecutionPolicy Bypass -File bench\run_asama25.ps1 [-SkipBefore]
param([switch]$SkipBefore)
$ErrorActionPreference = "Continue"
$env:PYTHONUTF8 = "1"
$py = "C:\Users\egitim.YESIM\Desktop\visual_agent_repo\.venv\Scripts\python.exe"
$log = "data\logs\bench_asama25.log"
function Step($title, [string[]]$cmd) {
    foreach ($k in "PILOT_QDRANT_URL", "PILOT_COLLECTION") { Remove-Item "Env:$k" -ErrorAction SilentlyContinue }
    "$(Get-Date -Format HH:mm:ss) == $title" | Out-File $log -Append -Encoding utf8
    & $py @cmd 2>&1 | ForEach-Object { "$_" } | Out-File $log -Append -Encoding utf8
}
$m = @("-m", "bench.measure", "--timing-sets", "questions", "--repeats", "3", "--unfiltered", "--recall-queries", "0")
if (-not $SkipBefore) { Step "önce (eski indeks, belirli sıralı RRF)" ($m + @("--name", "asama25_once", "--no-source-strip")) }
Step "yeniden parçalama ve indeksleme" @("run_rechunk.py")
Step "sonra" ($m + @("--name", "asama25_sonra"))
Step "kayıp analizi" @("-m", "bench.loss")
Step "sunucuya kopya" @("-m", "bench.server", "copy", "--name", "manuals")
Step "mod farkı" @("-m", "bench.mode_diff")
"$(Get-Date -Format HH:mm:ss) == BİTTİ" | Out-File $log -Append -Encoding utf8
