<#
iris-stop.ps1 - kebalikan iris-start.ps1. Hanya karakter ASCII.

Urutan mati (terbalik dari start):
  1. Overlay Electron (dari folder proyek ini)
  2. server.py (yang mendengar di :8765)
  3. Hermes, 9Router, VOICEVOX (unit systemd user di WSL, dihentikan sekaligus)
  4. Sesi penjaga WSL (sleep infinity)
  5. WSL itu sendiri (wsl --shutdown) -> RAM VmmemWSL lepas

PERINGATAN: jangan jalankan saat Hermes sedang mengerjakan tugas /agen.

Pakai (dari folder proyek):
  powershell -ExecutionPolicy Bypass -File .\iris-stop.ps1
Opsi:
  -TanpaWSL   hanya overlay + server.py yang dimatikan; WSL, Hermes, 9Router, VOICEVOX dibiarkan (perilaku lama)
  -HentikanPenjaga   (bersama -TanpaWSL) sesi penjaga WSL ikut dihentikan, WSL tetap hidup; untuk tes penjaga Q10.6
  -Distro Ubuntu   -Proyek <jalur>
#>
param(
  [string]$Proyek = $PSScriptRoot,
  [string]$Distro = 'Ubuntu',
  [switch]$TanpaWSL,
  [switch]$HentikanPenjaga
)

if (-not $Proyek) { $Proyek = (Get-Location).Path }
$Proyek = $Proyek.TrimEnd('\')
$prefix = $Proyek + '\'

# 1. Overlay: electron.exe yang berasal dari folder proyek ini
$el = Get-CimInstance Win32_Process -Filter "Name='electron.exe'" |
  Where-Object { $_.ExecutablePath -and $_.ExecutablePath.StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase) }
if ($el) {
  foreach ($p in $el) { Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue }
  Write-Host 'Overlay dihentikan'
} else {
  Write-Host 'Overlay tidak jalan'
}

# 2. server.py: proses yang mendengar di :8765, dipastikan berasal dari server.py
$ada = $false
$dengar = Get-NetTCPConnection -LocalPort 8765 -State Listen -ErrorAction SilentlyContinue
foreach ($c in $dengar) {
  $proc = Get-CimInstance Win32_Process -Filter ("ProcessId=" + $c.OwningProcess)
  if ($proc -and $proc.CommandLine -like '*server.py*') {
    & taskkill.exe /PID $c.OwningProcess /T /F | Out-Null
    $ada = $true
  }
}
if ($ada) { Write-Host 'server.py dihentikan' } else { Write-Host 'server.py tidak jalan di :8765' }

if ($TanpaWSL) {
  if ($HentikanPenjaga) {
    $pj0 = Get-CimInstance Win32_Process -Filter "Name='wsl.exe'" | Where-Object { $_.CommandLine -like '*sleep infinity*' }
    foreach ($p in $pj0) { Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue }
    Write-Host 'Sesi penjaga WSL dihentikan'
  }
  Write-Host 'WSL, Hermes, 9Router, VOICEVOX dibiarkan hidup (-TanpaWSL)'
  exit 0
}

# 3. Layanan WSL: hanya kalau WSL memang sedang jalan (jangan membangunkan WSL hanya untuk mematikannya)
$raw = ''
try { $raw = ((& wsl.exe -l -v 2>&1) | Out-String) -replace "`0", '' } catch { $raw = '' }
$wslJalan = [regex]::IsMatch($raw, '(?m)^\s*\*?\s*' + [regex]::Escape($Distro) + '\s+Running')

if ($wslJalan) {
  Write-Host 'Menghentikan Hermes, 9Router, VOICEVOX (maks 12 detik)...'
  & wsl.exe -d $Distro -- timeout 12 systemctl --user stop hermes-gateway 9router voicevox 2>$null
  Write-Host 'Layanan WSL dihentikan'
} else {
  Write-Host 'WSL memang sudah mati'
}

# 4. Sesi penjaga WSL
$pj = Get-CimInstance Win32_Process -Filter "Name='wsl.exe'" | Where-Object { $_.CommandLine -like '*sleep infinity*' }
if ($pj) {
  foreach ($p in $pj) { Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue }
  Write-Host 'Sesi penjaga WSL dihentikan'
}

# 5. WSL
if ($wslJalan) {
  Write-Host 'Mematikan WSL...'
  & wsl.exe --shutdown
  Start-Sleep -Seconds 3
  if (Get-Process -Name vmmemWSL, vmmem -ErrorAction SilentlyContinue) {
    Write-Host 'WSL dimatikan. VmmemWSL mungkin butuh beberapa detik lagi untuk hilang.'
  } else {
    Write-Host 'WSL dimatikan. RAM sudah lepas.'
  }
}
Write-Host 'Selesai.'
