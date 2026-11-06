# Gün içi süre profili döngüsü (plan §33; onay 2026-11-06). ZAMANLANMIŞ GÖREV DEĞİL: kullanıcı oturum başında elle başlatır.
# 09:30, 11:30, 14:00, 16:30'da birer ölçüm (10 soru, ~0,003 USD); geçmiş saatler atlanır; 18:00'de kendini kapatır.
# Arayüz ölçüm sırasında kapalı olmalı (Qdrant gömülü modda tek süreç).
# Kullanım (Pilot klasöründe): powershell -ExecutionPolicy Bypass -File bench\sure_profili.ps1
Set-Location (Split-Path -Parent $PSScriptRoot)
$ErrorActionPreference = "Continue"
$env:PYTHONUTF8 = "1"
$env:PYTHONUNBUFFERED = "1"
$env:PILOT_ANSWER_MODE = "c"
$env:OPENROUTER_API_KEY = [Environment]::GetEnvironmentVariable("OPENROUTER_API_KEY", "User")
$py = "C:\Users\egitim.YESIM\Desktop\visual_agent_repo\.venv\Scripts\python.exe"
New-Item -ItemType Directory -Force "data\logs" | Out-Null
$log = "data\logs\sure_profili.log"
$slots = @("09:30", "11:30", "14:00", "16:30")
$end = (Get-Date).Date.AddHours(18)
"$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') == DÖNGÜ BAŞLADI" | Out-File $log -Append -Encoding utf8
foreach ($s in $slots) {
    $at = [datetime]::ParseExact("$((Get-Date).ToString('yyyy-MM-dd')) $s", "yyyy-MM-dd HH:mm", $null)
    if ((Get-Date) -gt $at.AddMinutes(20)) { continue }          # geçmiş saat: atla
    while ((Get-Date) -lt $at) { Start-Sleep -Seconds 30 }
    if ((Get-Date) -ge $end) { break }
    "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') == ÖLÇÜM $s" | Out-File $log -Append -Encoding utf8
    & $py -m bench.sure_profili 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch "HTTP Request" } | Out-File $log -Append -Encoding utf8
    "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') == ÖLÇÜM BİTTİ $s (çıkış $LASTEXITCODE)" | Out-File $log -Append -Encoding utf8
}
"$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') == DÖNGÜ BİTTİ" | Out-File $log -Append -Encoding utf8
