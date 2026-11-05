<#
iris-hermes.ps1 - saklar Hermes + WSL (nyala <-> mati). Hanya karakter ASCII.

Kalau Hermes (:8642) menjawab  -> MATI: stop hermes-gateway, hentikan sesi penjaga WSL, lalu wsl --shutdown
                                  (RAM VmmemWSL lepas; 9Router dan VOICEVOX ikut mati karena WSL-nya mati)
Kalau Hermes tidak menjawab    -> NYALA: WSL dibangunkan, sesi penjaga dibuka, hermes-gateway di-start
                                  (9Router dan VOICEVOX naik sendiri bersama WSL karena unit systemd-nya enabled)

Tidak menyentuh server.py dan overlay Electron.
PERINGATAN: jangan matikan saat Hermes sedang mengerjakan tugas /agen.

Opsi: -Nyalakan (paksa nyala)  -Matikan (paksa mati)  -TanpaPenjaga  -Distro Ubuntu  -TungguDetik 90
#>
param(
  [string]$Distro = 'Ubuntu',
  [int]$TungguDetik = 90,
  [switch]$Nyalakan,
  [switch]$Matikan,
  [switch]$TanpaPenjaga
)

$Unit = 'hermes-gateway'
$Url  = 'http://127.0.0.1:8642/health'

function Get-HttpCode([string]$U, [int]$TimeoutMs = 3000) {
  try {
    $req = [System.Net.HttpWebRequest]::Create($U)
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

function Get-Penjaga {
  return @(Get-CimInstance Win32_Process -Filter "Name='wsl.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -like '*sleep infinity*' })
}

Write-Host 'Memeriksa Hermes...'
$hidup = ((Get-HttpCode $Url) -gt 0)
if ($hidup) { Write-Host 'Status sekarang: NYALA' } else { Write-Host 'Status sekarang: MATI' }

if ($Nyalakan) { $mau = 'nyala' }
elseif ($Matikan) { $mau = 'mati' }
elseif ($hidup) { $mau = 'mati' }
else { $mau = 'nyala' }

# ------------------------------------------------------------ MATI
if ($mau -eq 'mati') {
  if ($hidup) {
    Write-Host 'Mematikan Hermes (maks 12 detik)...'
    & wsl.exe -d $Distro -- timeout 12 systemctl --user stop $Unit 2>$null
    Write-Host 'Hermes dihentikan.' -ForegroundColor Cyan
  } else {
    Write-Host 'Hermes memang sudah mati.'
  }

  $pj = Get-Penjaga
  if ($pj.Count -gt 0) {
    foreach ($p in $pj) { Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue }
    Write-Host 'Sesi penjaga WSL dihentikan.'
  }

  Write-Host 'Mematikan WSL...'
  & wsl.exe --shutdown
  Start-Sleep -Seconds 3
  $vm = Get-Process -Name vmmemWSL, vmmem -ErrorAction SilentlyContinue
  if ($vm) {
    Write-Host 'WSL dimatikan. VmmemWSL mungkin butuh beberapa detik lagi untuk hilang.' -ForegroundColor Cyan
  } else {
    Write-Host 'WSL dimatikan. RAM sudah lepas.' -ForegroundColor Green
  }
  exit 0
}

# ------------------------------------------------------------ NYALA
if ($hidup) {
  Write-Host 'Hermes sudah nyala.'
  exit 0
}

Write-Host 'Membangunkan WSL...'
& wsl.exe -d $Distro -- true 2>$null
if ($LASTEXITCODE -ne 0) {
  Write-Host "WSL $Distro tidak bisa dijalankan." -ForegroundColor Red
  exit 1
}

if (-not $TanpaPenjaga) {
  if ((Get-Penjaga).Count -eq 0) {
    Start-Process -FilePath 'wsl.exe' -ArgumentList @('-d', $Distro, '--', 'sleep', 'infinity') -WindowStyle Hidden | Out-Null
    Write-Host 'Sesi penjaga WSL dibuka (tersembunyi).'
  }
}

Write-Host 'Menyalakan unit hermes-gateway...'
& wsl.exe -d $Distro -- systemctl --user start $Unit 2>$null
Write-Host 'Menunggu Hermes naik...'
$t0 = Get-Date
while (((Get-Date) - $t0).TotalSeconds -lt $TungguDetik) {
  if ((Get-HttpCode $Url) -gt 0) {
    Write-Host 'Hermes nyala.' -ForegroundColor Green
    exit 0
  }
  Start-Sleep -Seconds 2
}
Write-Host "Hermes belum menjawab setelah $TungguDetik detik." -ForegroundColor Yellow
exit 1
