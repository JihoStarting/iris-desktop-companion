<#
iris-start.ps1 v1.0 - peluncur Iris. ASCII saja (aman di Windows PowerShell 5.1).
Urutan: WSL + penjaga (sleep infinity) -> VOICEVOX, 9Router, Hermes (systemd user) -> server.py -> overlay.
Idempoten, tanpa token di log, tidak me-restart Hermes.
Pakai: powershell -ExecutionPolicy Bypass -File .\iris-start.ps1
Opsi: -Distro Ubuntu  -TungguDetik 90  -TanpaPenjaga  -TanpaOverlay  -Proyek <jalur>
Log: iris-start.log, iris-server.*.log, iris-overlay.*.log (log server memuat teks chat)
Perbaikan 1.0: cek WSL tidak lagi gagal palsu karena stderr wsl.exe; dicoba ulang 3x. by: KangJiho
#>
param(
  [string]$Proyek = $PSScriptRoot,
  [string]$Distro = 'Ubuntu',
  [int]$TungguDetik = 90,
  [switch]$TanpaPenjaga,
  [switch]$TanpaOverlay
)

if (-not $Proyek) { $Proyek = (Get-Location).Path }
$Proyek = $Proyek.TrimEnd('\')
$LogStart = Join-Path $Proyek 'iris-start.log'
$ErrorActionPreference = 'Stop'

function Log([string]$Pesan, [string]$Tingkat = 'INFO') {
  $baris = '[{0}] {1,-5} {2}' -f (Get-Date -Format 'HH:mm:ss'), $Tingkat, $Pesan
  Write-Host $baris
  try { Add-Content -Path $LogStart -Value $baris -Encoding ASCII } catch { }
}

# Kode HTTP; 0 = tidak menjawab. Kode apa pun (200, 307, 401, 404) berarti layanan hidup.
function Get-HttpCode([string]$Url, [int]$TimeoutMs = 3000) {
  try {
    $req = [System.Net.HttpWebRequest]::Create($Url)
    $req.Method = 'GET'
    $req.Timeout = $TimeoutMs
    $req.AllowAutoRedirect = $false
    $req.Proxy = $null
    $res = $req.GetResponse()
    $kode = [int]$res.StatusCode
    $res.Close()
    return $kode
  } catch [System.Net.WebException] {
    if ($_.Exception.Response) {
      $kode = [int]$_.Exception.Response.StatusCode
      $_.Exception.Response.Close()
      return $kode
    }
    return 0
  } catch {
    return 0
  }
}

function Wait-Http([string]$Url, [int]$BatasDetik) {
  $t0 = Get-Date
  while (((Get-Date) - $t0).TotalSeconds -lt $BatasDetik) {
    if ((Get-HttpCode $Url) -gt 0) { return $true }
    Start-Sleep -Seconds 2
  }
  return $false
}

Log "Mulai. Proyek: $Proyek"

# 1. WSL
# wsl.exe menulis peringatan ke stderr (UTF-16); di PS 5.1 dengan 'Stop' itu dianggap galat. Jalankan dengan 'Continue'.
$wslOk = $false; $wslKet = ''
for ($i = 1; $i -le 3 -and -not $wslOk; $i++) {
  $ErrorActionPreference = 'Continue'
  $wslKet = (& wsl.exe -d $Distro -- true 2>&1 | Out-String) -replace "`0", ''
  $kode = $LASTEXITCODE
  $ErrorActionPreference = 'Stop'
  if ($kode -eq 0) { $wslOk = $true } else { $wslKet = "kode keluar $kode " + $wslKet.Trim(); Start-Sleep -Seconds 3 }
}
if ($wslOk) { Log "WSL $Distro hidup" } else {
  Log "WSL $Distro tidak bisa dijalankan: $wslKet" 'GAGAL'
  exit 1
}

if (-not $TanpaPenjaga) {
  $penjaga = Get-CimInstance Win32_Process -Filter "Name='wsl.exe'" |
    Where-Object { $_.CommandLine -like '*sleep infinity*' }
  if ($penjaga) {
    Log 'Sesi penjaga WSL sudah ada'
  } else {
    Start-Process -FilePath 'wsl.exe' -ArgumentList @('-d', $Distro, '--', 'sleep', 'infinity') -WindowStyle Hidden | Out-Null
    Log 'Sesi penjaga WSL dibuka (tersembunyi)'
  }
}

# 2. Layanan WSL: yang belum menjawab di-start SEKALIGUS (tanpa menunggu satu per satu); tidak pernah restart
$layanan = @(
  @{ Nama = 'VOICEVOX'; Unit = 'voicevox';       Url = 'http://127.0.0.1:50021/version' },
  @{ Nama = '9Router';  Unit = '9router';        Url = 'http://127.0.0.1:20128/' },
  @{ Nama = 'Hermes';   Unit = 'hermes-gateway'; Url = 'http://127.0.0.1:8642/health' }
)
$tLayanan = Get-Date
$tertunda = @()
foreach ($l in $layanan) {
  if ((Get-HttpCode $l.Url) -gt 0) {
    Log "$($l.Nama) sudah menjawab"
  } else {
    $tertunda += $l
  }
}
if ($tertunda.Count -gt 0) {
  $unitArgs = @('-d', $Distro, '--', 'systemctl', '--user', 'start', '--no-block') + @($tertunda | ForEach-Object { $_.Unit })
  Log ('Start sekaligus: ' + (@($tertunda | ForEach-Object { $_.Nama }) -join ', '))
  $ErrorActionPreference = 'Continue'; & wsl.exe @unitArgs 2>&1 | Out-Null; $ErrorActionPreference = 'Stop'
}

# 3. server.py
if ((Get-HttpCode 'http://127.0.0.1:8765/health') -gt 0) {
  Log 'server.py sudah menjawab di :8765 (tidak membuat server kedua)'
} else {
  $py = Join-Path $Proyek '.venv\Scripts\python.exe'
  if (-not (Test-Path $py)) {
    Log "Tidak ada $py (venv Windows belum dibuat?)" 'GAGAL'
    exit 1
  }
  Start-Process -FilePath $py -ArgumentList @('-u', 'server.py') -WorkingDirectory $Proyek -WindowStyle Hidden `
    -RedirectStandardOutput (Join-Path $Proyek 'iris-server.out.log') `
    -RedirectStandardError (Join-Path $Proyek 'iris-server.err.log') | Out-Null
  Log 'server.py dijalankan (tersembunyi); menunggu /health (maks 120 detik)'
  $tSrv = Get-Date
  if (Wait-Http 'http://127.0.0.1:8765/health' 120) {
    Log ('server.py siap setelah {0:N0} detik' -f ((Get-Date) - $tSrv).TotalSeconds)
  } else {
    Log 'server.py belum menjawab dalam 120 detik; overlay tetap dijalankan. Lihat iris-server.err.log' 'WARN'
  }
}

# 4. Overlay
if ($TanpaOverlay) {
  Log 'Overlay dilewati (-TanpaOverlay)'
} else {
  $prefix = $Proyek + '\'
  $jalan = Get-CimInstance Win32_Process -Filter "Name='electron.exe'" |
    Where-Object { $_.ExecutablePath -and $_.ExecutablePath.StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase) }
  if ($jalan) {
    Log 'Overlay sudah jalan'
  } else {
    $electron = Join-Path $Proyek 'node_modules\electron\dist\electron.exe'
    if (-not (Test-Path $electron)) {
      Log "Tidak ada $electron (jalankan npm.cmd install di folder proyek)" 'GAGAL'
      exit 1
    }
    # Tanpa -WindowStyle Hidden: Electron bukan program konsol, dan Hidden bisa ikut menyembunyikan jendela overlay-nya
    Start-Process -FilePath $electron -ArgumentList @('.') -WorkingDirectory $Proyek `
      -RedirectStandardOutput (Join-Path $Proyek 'iris-overlay.out.log') `
      -RedirectStandardError (Join-Path $Proyek 'iris-overlay.err.log') | Out-Null
    Log 'Overlay dijalankan'
  }
}

# 5. Tunggu layanan WSL yang tadi di-start (berjalan paralel dengan server.py dan overlay di atas)
$semuaHidup = $true
foreach ($l in $tertunda) {
  $sisa = [int]($TungguDetik - ((Get-Date) - $tLayanan).TotalSeconds)
  if ($sisa -lt 5) { $sisa = 5 }
  if (Wait-Http $l.Url $sisa) {
    Log "$($l.Nama) naik"
  } else {
    Log "$($l.Nama) belum menjawab setelah $TungguDetik detik" 'WARN'
    $semuaHidup = $false
  }
}
if (-not $semuaHidup) { Log 'Ada layanan yang belum hidup' 'WARN' }

Log 'Selesai.'
