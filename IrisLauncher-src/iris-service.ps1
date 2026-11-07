<#
iris-service.ps1 - nyalakan atau matikan SATU layanan saja. Hanya karakter ASCII.
Dipakai oleh chip status di Iris Launcher (klik chip = toggle layanan itu).

Pakai:
  powershell -ExecutionPolicy Bypass -File .\iris-service.ps1 -Nama hermes -Aksi nyala
Nama : wsl | voicevox | router | hermes | server | overlay
Aksi : nyala | mati
Opsi : -Proyek <jalur>  -Distro Ubuntu  -TungguDetik 90  -TanpaPenjaga  -TanpaGPU (VOICEVOX Windows pakai CPU)

Aturan: hanya layanan yang dipilih yang hidup.
  - voicevox/router/hermes butuh WSL berjalan. Kalau WSL sedang mati, WSL dibangunkan seperlunya,
    lalu layanan lain di dalam WSL yang ikut naik otomatis (unit systemd enabled) dihentikan lagi.
  - Mematikan WSL ikut mematikan semua layanan di dalamnya.
  - server.py dan overlay berdiri sendiri; tidak saling menyalakan.
Kode keluar: 0 = berhasil, 1 = gagal.
#>
param(
  [Parameter(Mandatory = $true)][ValidateSet('wsl', 'voicevox', 'router', 'hermes', 'server', 'overlay')][string]$Nama,
  [Parameter(Mandatory = $true)][ValidateSet('nyala', 'mati')][string]$Aksi,
  [string]$Proyek = '',
  [string]$Distro = 'Ubuntu',
  [int]$TungguDetik = 90,
  [switch]$TanpaPenjaga,
  [switch]$TanpaGPU
)

if ($Proyek) { $Proyek = $Proyek.TrimEnd('\') }

$UnitWsl = @{
  voicevox = @{ Unit = 'voicevox';       Label = 'VOICEVOX'; Url = 'http://127.0.0.1:50021/version' }
  router   = @{ Unit = '9router';        Label = '9Router';  Url = 'http://127.0.0.1:20128/' }
  hermes   = @{ Unit = 'hermes-gateway'; Label = 'Hermes';   Url = 'http://127.0.0.1:8642/health' }
}
$SemuaUnit = @('voicevox', '9router', 'hermes-gateway')
$UrlServer = 'http://127.0.0.1:8765/ping'   # bukan /health: /health ikut memeriksa Hermes dll. dan lambat saat Hermes mati

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

function Wait-Mati([string]$Url, [int]$BatasDetik) {
  $t0 = Get-Date
  while (((Get-Date) - $t0).TotalSeconds -lt $BatasDetik) {
    if ((Get-HttpCode $Url 1500) -eq 0) { return $true }
    Start-Sleep -Seconds 1
  }
  return $false
}

function Get-Penjaga {
  return @(Get-CimInstance Win32_Process -Filter "Name='wsl.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -like '*sleep infinity*' })
}

function Test-WslJalan {
  $raw = ''
  try { $raw = ((& wsl.exe -l -v 2>&1) | Out-String) -replace "`0", '' } catch { $raw = '' }
  return [regex]::IsMatch($raw, '(?m)^\s*\*?\s*' + [regex]::Escape($Distro) + '\s+Running')
}

function Stop-Penjaga {
  $pj = Get-Penjaga
  foreach ($p in $pj) { Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue }
  if ($pj.Count -gt 0) { Write-Host 'Sesi penjaga WSL dihentikan' }
}

# Membangunkan WSL + sesi penjaga. Bila WSL tadinya mati, unit systemd yang ikut naik otomatis
# dihentikan lagi, kecuali yang diminta ($Pertahankan), supaya hanya layanan yang diklik yang hidup.
function Start-Wsl([string[]]$Pertahankan) {
  $tadiMati = -not (Test-WslJalan)

  $ok = $false
  for ($i = 1; $i -le 3 -and -not $ok; $i++) {
    & wsl.exe -d $Distro -- true 2>$null
    if ($LASTEXITCODE -eq 0) { $ok = $true } else { Start-Sleep -Seconds 3 }
  }
  if (-not $ok) {
    Write-Host "WSL $Distro tidak bisa dijalankan." 
    return $false
  }
  Write-Host "WSL $Distro hidup"

  if (-not $TanpaPenjaga) {
    if ((Get-Penjaga).Count -eq 0) {
      Start-Process -FilePath 'wsl.exe' -ArgumentList @('-d', $Distro, '--', 'sleep', 'infinity') -WindowStyle Hidden | Out-Null
      Write-Host 'Sesi penjaga WSL dibuka (tersembunyi)'
    }
  }

  if ($tadiMati) {
    Write-Host 'WSL baru bangun; menunggu systemd selesai naik...'
    & wsl.exe -d $Distro -- timeout 40 systemctl --user is-system-running --wait 2>$null | Out-Null
    $stop = @($SemuaUnit | Where-Object { $Pertahankan -notcontains $_ })
    if ($stop.Count -gt 0) {
      Write-Host ('Menghentikan layanan yang ikut naik otomatis: ' + ($stop -join ', '))
      & wsl.exe -d $Distro -- timeout 15 systemctl --user stop @stop 2>$null | Out-Null
    }
  }
  return $true
}

Write-Host "Layanan: $Nama  Aksi: $Aksi"

# ============================================================ WSL
if ($Nama -eq 'wsl') {
  if ($Aksi -eq 'nyala') {
    if (Test-WslJalan) { Write-Host 'WSL sudah hidup.'; exit 0 }
    if (Start-Wsl @()) {
      Write-Host 'WSL hidup. Layanan di dalamnya (VOICEVOX, 9Router, Hermes) tidak dinyalakan.'
      exit 0
    }
    exit 1
  }
  # mati
  if (-not (Test-WslJalan)) { Write-Host 'WSL memang sudah mati.'; Stop-Penjaga; exit 0 }
  Write-Host 'Menghentikan Hermes, 9Router, VOICEVOX (maks 75 detik)...'
  & wsl.exe -d $Distro -- timeout 75 systemctl --user stop hermes-gateway 9router voicevox 2>$null
  Stop-Penjaga
  Write-Host 'Mematikan WSL...'
  & wsl.exe --shutdown
  Start-Sleep -Seconds 3
  if (Get-Process -Name vmmemWSL, vmmem -ErrorAction SilentlyContinue) {
    Write-Host 'WSL dimatikan. VmmemWSL mungkin butuh beberapa detik lagi untuk hilang.'
  } else {
    Write-Host 'WSL dimatikan. RAM sudah lepas.'
  }
  exit 0
}

# ============================================================ VOICEVOX di Windows (vv-engine\run.exe)
# Dipakai bila <Proyek>\vv-engine\run.exe ada; tidak membangunkan WSL. Bila tidak ada, jatuh ke unit WSL di bawah.
if ($Nama -eq 'voicevox' -and $Proyek -and (Test-Path -LiteralPath (Join-Path $Proyek 'vv-engine\run.exe'))) {
  $VvDir = Join-Path $Proyek 'vv-engine'
  $VvExe = Join-Path $VvDir 'run.exe'
  $VvUrl = 'http://127.0.0.1:50021/version'
  $vvProses = @(Get-CimInstance Win32_Process -Filter "Name='run.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.ExecutablePath -and $_.ExecutablePath.StartsWith($VvDir + '\', [System.StringComparison]::OrdinalIgnoreCase) })

  if ($Aksi -eq 'nyala') {
    if ((Get-HttpCode $VvUrl) -gt 0) { Write-Host 'VOICEVOX sudah menjawab.'; exit 0 }
    $gpu = -not $TanpaGPU
    $t0 = Get-Date
    $tVv = Get-Date
    function Start-VvWin([bool]$Gpu) {
      $vvArgs = @('--host', '127.0.0.1', '--port', '50021')
      if ($Gpu) { $vvArgs += '--use_gpu' }
      $vvArgs += @('--cpu_num_threads', '4')
      Start-Process -FilePath $VvExe -ArgumentList $vvArgs -WorkingDirectory $VvDir -WindowStyle Hidden `
        -RedirectStandardOutput (Join-Path $Proyek 'iris-voicevox.out.log') `
        -RedirectStandardError (Join-Path $Proyek 'iris-voicevox.err.log') | Out-Null
    }
    Start-VvWin $gpu
    Write-Host ('Menyalakan VOICEVOX (Windows, GPU=' + $gpu + ')...')
    while (((Get-Date) - $t0).TotalSeconds -lt $TungguDetik) {
      if ((Get-HttpCode $VvUrl) -gt 0) { Write-Host 'VOICEVOX naik.'; exit 0 }
      if ((((Get-Date) - $tVv).TotalSeconds -gt 5) -and (@(Get-CimInstance Win32_Process -Filter "Name='run.exe'" -ErrorAction SilentlyContinue |
          Where-Object { $_.ExecutablePath -and $_.ExecutablePath.StartsWith($VvDir + '\', [System.StringComparison]::OrdinalIgnoreCase) }).Count -eq 0)) {
        if ($gpu) {
          Write-Host 'GPU gagal naik; mencoba tanpa GPU...'
          $gpu = $false
          Start-VvWin $false
          $tVv = Get-Date
        } else {
          break
        }
      }
      Start-Sleep -Seconds 2
    }
    Write-Host 'VOICEVOX belum menjawab. Lihat iris-voicevox.err.log (port 50021 bentrok dengan unit voicevox di WSL?)'
    exit 1
  }

  # mati
  if ($vvProses.Count -gt 0) {
    foreach ($p in $vvProses) { Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue }
    Write-Host 'VOICEVOX (Windows) dihentikan'
  }
  if (((Get-HttpCode $VvUrl 1500) -gt 0) -and (Test-WslJalan)) {
    Write-Host 'Port 50021 masih menjawab; menghentikan unit voicevox di WSL juga...'
    & wsl.exe -d $Distro -- timeout 12 systemctl --user stop voicevox 2>$null | Out-Null
  }
  if (Wait-Mati $VvUrl 8) { Write-Host 'VOICEVOX dihentikan.'; exit 0 }
  Write-Host 'VOICEVOX masih menjawab setelah dihentikan.'
  exit 1
}

# ============================================================ VOICEVOX / 9Router / Hermes
if ($UnitWsl.ContainsKey($Nama)) {
  $u = $UnitWsl[$Nama]
  if ($Aksi -eq 'nyala') {
    if ((Get-HttpCode $u.Url) -gt 0) { Write-Host "$($u.Label) sudah menjawab."; exit 0 }
    if (-not (Start-Wsl @($u.Unit))) { exit 1 }
    Write-Host "Menyalakan $($u.Label)..."
    & wsl.exe -d $Distro -- systemctl --user start --no-block $u.Unit 2>$null | Out-Null
    if (Wait-Http $u.Url $TungguDetik) { Write-Host "$($u.Label) naik."; exit 0 }
    Write-Host "$($u.Label) belum menjawab setelah $TungguDetik detik."
    exit 1
  }
  # mati: jangan membangunkan WSL hanya untuk mematikan layanan
  if (-not (Test-WslJalan)) { Write-Host "WSL mati, jadi $($u.Label) memang sudah mati."; exit 0 }
  $batasStop = if ($Nama -eq 'hermes') { 75 } else { 12 }   # systemd memberi Hermes sampai 70 detik (TimeoutStopSec)
  Write-Host "Mematikan $($u.Label) (maks $batasStop detik)..."
  & wsl.exe -d $Distro -- timeout $batasStop systemctl --user stop $u.Unit 2>$null | Out-Null
  if (Wait-Mati $u.Url 8) { Write-Host "$($u.Label) dihentikan."; exit 0 }
  Write-Host "$($u.Label) masih menjawab setelah dihentikan."
  exit 1
}

# ============================================================ server.py
if ($Nama -eq 'server') {
  if ($Aksi -eq 'nyala') {
    if ((Get-HttpCode $UrlServer) -gt 0) { Write-Host 'server.py sudah menjawab di :8765.'; exit 0 }
    if (-not $Proyek) { Write-Host 'Folder proyek belum diatur.'; exit 1 }
    $py = Join-Path $Proyek '.venv\Scripts\python.exe'
    if (-not (Test-Path $py)) { Write-Host "Tidak ada $py (venv Windows belum dibuat?)"; exit 1 }
    Start-Process -FilePath $py -ArgumentList @('-u', 'server.py') -WorkingDirectory $Proyek -WindowStyle Hidden `
      -RedirectStandardOutput (Join-Path $Proyek 'iris-server.out.log') `
      -RedirectStandardError (Join-Path $Proyek 'iris-server.err.log') | Out-Null
    Write-Host 'server.py dijalankan (tersembunyi); menunggu /health (maks 120 detik)'
    $t0 = Get-Date
    if (Wait-Http $UrlServer 120) {
      Write-Host ('server.py siap setelah {0:N0} detik' -f ((Get-Date) - $t0).TotalSeconds)
      exit 0
    }
    Write-Host 'server.py belum menjawab dalam 120 detik. Lihat iris-server.err.log'
    exit 1
  }
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
  exit 0
}

# ============================================================ Overlay
if ($Nama -eq 'overlay') {
  if (-not $Proyek) { Write-Host 'Folder proyek belum diatur.'; exit 1 }
  $prefix = $Proyek + '\'
  $jalan = @(Get-CimInstance Win32_Process -Filter "Name='electron.exe'" |
    Where-Object { $_.ExecutablePath -and $_.ExecutablePath.StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase) })
  if ($Aksi -eq 'nyala') {
    if ($jalan.Count -gt 0) { Write-Host 'Overlay sudah jalan.'; exit 0 }
    $electron = Join-Path $Proyek 'node_modules\electron\dist\electron.exe'
    if (-not (Test-Path $electron)) { Write-Host "Tidak ada $electron (jalankan npm.cmd install di folder proyek)"; exit 1 }
    # Tanpa -WindowStyle Hidden: Electron bukan program konsol, dan Hidden bisa ikut menyembunyikan jendela overlay-nya
    Start-Process -FilePath $electron -ArgumentList @('.') -WorkingDirectory $Proyek `
      -RedirectStandardOutput (Join-Path $Proyek 'iris-overlay.out.log') `
      -RedirectStandardError (Join-Path $Proyek 'iris-overlay.err.log') | Out-Null
    Write-Host 'Overlay dijalankan'
    exit 0
  }
  if ($jalan.Count -gt 0) {
    foreach ($p in $jalan) { Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue }
    Write-Host 'Overlay dihentikan'
  } else {
    Write-Host 'Overlay tidak jalan'
  }
  exit 0
}
