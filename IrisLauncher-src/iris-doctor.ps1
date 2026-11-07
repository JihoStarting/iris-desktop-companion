<#
iris-doctor.ps1  -  cek kesehatan Iris (Fase 1 dari Bagian Q)

HANYA MEMBACA. Skrip ini tidak menyalakan, mematikan, memasang, atau mengubah apa pun:
  - tidak menyalakan WSL (kalau WSL mati, hanya dilaporkan)
  - tidak mengubah .env, .wslconfig, atau pengaturan Windows
  - tidak pernah mencetak isi token atau kunci (hanya panjangnya)

Cara pakai (dari folder proyek, PowerShell Windows):
  powershell -ExecutionPolicy Bypass -File .\iris-doctor.ps1

Opsi:
  -Proyek     folder proyek (bawaan: folder tempat skrip ini berada)
  -Distro     nama distro WSL (bawaan: Ubuntu)
  -MinFreeGB  di bawah ini disk diberi WARN (bawaan: 15)
  -RamWarnPct di atas ini RAM sistem diberi WARN (bawaan: 85)

Kode keluar: 0 kalau tidak ada GAGAL, 1 kalau ada.
Catatan: WSL yang mati (setelah Iris Stop atau Iris Hermes) dilaporkan INFO, bukan GAGAL; node yang tidak ada hanya WARN.
Berkas ini sengaja hanya berisi karakter ASCII supaya aman dibaca Windows PowerShell 5.1.
#>
[CmdletBinding()]
param(
  [string]$Proyek = $PSScriptRoot,
  [string]$Distro = 'Ubuntu',
  [int]$MinFreeGB = 15,
  [int]$RamWarnPct = 85
)

$ErrorActionPreference = 'Continue'
if ([string]::IsNullOrWhiteSpace($Proyek)) { $Proyek = (Get-Location).Path }

# ---------------------------------------------------------------- pembantu
$script:cnt = @{ OK = 0; INFO = 0; WARN = 0; GAGAL = 0 }

function Say([string]$Level, [string]$Msg, [string]$Hint = '') {
  $script:cnt[$Level] = $script:cnt[$Level] + 1
  $colors = @{ OK = 'Green'; INFO = 'Gray'; WARN = 'Yellow'; GAGAL = 'Red' }
  Write-Host ('[{0,-5}] {1}' -f $Level, $Msg) -ForegroundColor $colors[$Level]
  if ($Hint) { Write-Host ('        -> ' + $Hint) -ForegroundColor DarkGray }
}

function Head([string]$Title) {
  Write-Host ''
  Write-Host ('== ' + $Title) -ForegroundColor Cyan
}

function Test-Http([string]$Url, [int]$TimeoutSec = 4) {
  $r = [pscustomobject]@{ Replied = $false; Code = 0; Body = ''; Error = '' }
  try {
    $resp = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec $TimeoutSec -ErrorAction Stop
    $r.Replied = $true
    $r.Code = [int]$resp.StatusCode
    $c = $resp.Content
    if ($c -is [byte[]]) { $c = [System.Text.Encoding]::UTF8.GetString($c) }
    $r.Body = [string]$c
  } catch {
    $ex = $_.Exception
    $code = 0
    if ($ex.Response) { try { $code = [int]$ex.Response.StatusCode } catch { $code = 0 } }
    if ($code -gt 0) { $r.Replied = $true; $r.Code = $code }
    else { $r.Error = $ex.Message }
  }
  return $r
}

function Read-EnvFile([string]$Path) {
  $h = @{}
  if (-not (Test-Path -LiteralPath $Path)) { return $h }
  foreach ($line in (Get-Content -LiteralPath $Path -Encoding UTF8)) {
    $t = $line.Trim()
    if ($t -eq '' -or $t.StartsWith('#')) { continue }
    if ($t -match '^(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$') {
      $name = $Matches[1]
      $v = $Matches[2].Trim()
      if ($v.Length -ge 2) {
        $first = $v.Substring(0, 1)
        $last = $v.Substring($v.Length - 1, 1)
        if (($first -eq '"' -and $last -eq '"') -or ($first -eq "'" -and $last -eq "'")) {
          $v = $v.Substring(1, $v.Length - 2)
        }
      }
      $h[$name] = $v
    }
  }
  return $h
}

function Get-Authority([string]$Url, [string]$Default) {
  if ([string]::IsNullOrWhiteSpace($Url)) { return $Default }
  try { return ([uri]$Url).GetLeftPart([System.UriPartial]::Authority) } catch { return $Default }
}

function Get-PortOf([string]$Authority, [int]$Default) {
  try { return ([uri]$Authority).Port } catch { return $Default }
}

function Get-Listener([int]$Port) {
  $c = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue | Select-Object -First 1
  if (-not $c) { return $null }
  $name = '?'
  $p = Get-Process -Id $c.OwningProcess -ErrorAction SilentlyContinue
  if ($p) { $name = $p.ProcessName }
  return [pscustomobject]@{ Port = $Port; Pid = $c.OwningProcess; Name = $name; Address = $c.LocalAddress }
}

function Get-WslListeners([string[]]$Lines) {
  $seen = @{}
  $res = @()
  foreach ($l in $Lines) {
    $c = ($l.Trim() -split '\s+')
    if ($c.Count -lt 5 -or $c[0] -ne 'LISTEN') { continue }
    $local = $c[3]
    $i = $local.LastIndexOf(':')
    if ($i -lt 0) { continue }
    $addr = $local.Substring(0, $i)
    $port = 0
    if (-not [int]::TryParse($local.Substring($i + 1), [ref]$port)) { continue }
    $wild = @('0.0.0.0', '*', '[::]', '::') -contains $addr
    if ($seen.ContainsKey($port) -and -not $wild) { continue }
    if ($seen.ContainsKey($port) -and $seen[$port].Wildcard) { continue }
    $o = [pscustomobject]@{ Port = $port; Address = $addr; Wildcard = $wild }
    $seen[$port] = $o
  }
  foreach ($k in ($seen.Keys | Sort-Object)) { $res += $seen[$k] }
  return $res
}

function Get-FreeText([double]$Bytes) { return ('{0:N1} GB' -f ($Bytes / 1GB)) }

# ---------------------------------------------------------------- kepala
Write-Host ''
Write-Host 'Iris doctor (hanya membaca, tidak mengubah apa pun)' -ForegroundColor White
Write-Host ('Waktu    : ' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'))
Write-Host ('PowerShell: ' + $PSVersionTable.PSVersion.ToString())
Write-Host ('Proyek   : ' + $Proyek)

# ---------------------------------------------------------------- 1. proyek
Head '1. Folder proyek'
if (-not (Test-Path -LiteralPath $Proyek)) {
  Say 'GAGAL' ('Folder proyek tidak ditemukan: ' + $Proyek) 'Jalankan skrip dari folder proyek, atau pakai -Proyek <jalur>.'
  Write-Host ''
  exit 1
}
$core = @('server.py', 'main.js', 'preload.js', 'index.html', 'package.json', 'requirements.txt')
$missingCore = @()
foreach ($f in $core) {
  if (-not (Test-Path -LiteralPath (Join-Path $Proyek $f))) { $missingCore += $f }
}
if ($missingCore.Count -eq 0) { Say 'OK' ('Berkas inti lengkap (' + ($core -join ', ') + ')') }
else { Say 'GAGAL' ('Berkas inti hilang: ' + ($missingCore -join ', ')) 'Periksa apakah folder yang dijalankan sudah benar.' }

if (-not (Test-Path -LiteralPath (Join-Path $Proyek 'assets\iris.vrm'))) {
  Say 'WARN' 'assets\iris.vrm tidak ada' 'Model avatar bawaan tidak ditemukan; overlay mungkin tidak menampilkan karakter.'
}

$qual = Split-Path -Path $Proyek -Qualifier -ErrorAction SilentlyContinue
if ($qual) {
  $letter = $qual.Substring(0, 1)
  try {
    $disk = Get-Partition -DriveLetter $letter -ErrorAction Stop | Get-Disk -ErrorAction Stop
    if ($disk.BusType -eq 'USB') {
      Say 'WARN' ("Proyek ada di drive ${letter}: yang terhubung lewat USB (" + $disk.FriendlyName + ')') 'Kalau drive belum tercolok saat masuk Windows, auto-start akan gagal.'
    } else {
      Say 'INFO' ("Drive proyek ${letter}: tipe bus " + $disk.BusType + ' (' + $disk.FriendlyName + ')')
    }
  } catch {
    Say 'INFO' ("Jenis drive ${letter}: tidak terbaca (mungkin butuh hak admin); dilewati.")
  }
}

# ---------------------------------------------------------------- 2. venv
Head '2. Python (.venv)'
$venvPy = Join-Path $Proyek '.venv\Scripts\python.exe'
$cfg = Join-Path $Proyek '.venv\pyvenv.cfg'
if (-not (Test-Path -LiteralPath $venvPy)) {
  Say 'GAGAL' '.venv\Scripts\python.exe tidak ada' 'Buat ulang: python -m venv .venv, lalu pip install -r requirements.txt (jangan pindahkan .venv).'
} else {
  $ver = ''
  try { $ver = (& $venvPy --version 2>&1 | Out-String).Trim() } catch { $ver = '' }
  if ($LASTEXITCODE -eq 0 -and $ver -like 'Python*') {
    Say 'OK' ('venv jalan: ' + $ver)
  } else {
    Say 'GAGAL' 'venv ada tetapi python-nya tidak bisa dijalankan' 'Interpreter dasar kemungkinan hilang (mis. Python dihapus atau dipindah). Buat ulang .venv.'
  }
  if (Test-Path -LiteralPath $cfg) {
    $home0 = (Select-String -LiteralPath $cfg -Pattern '^\s*home\s*=\s*(.+)$' | Select-Object -First 1)
    if ($home0) { Say 'INFO' ('Interpreter dasar venv: ' + $home0.Matches[0].Groups[1].Value.Trim()) }
  }
  $req = Join-Path $Proyek 'requirements.txt'
  if ((Test-Path -LiteralPath $req) -and $ver -like 'Python*') {
    $pyCode = @'
import sys, re
import importlib.metadata as md
missing = []
for raw in open(sys.argv[1], encoding='utf-8'):
    line = raw.split('#')[0].strip()
    if not line or line.startswith('-'):
        continue
    name = re.split(r'[<>=!~;\[ ]', line, maxsplit=1)[0]
    try:
        md.version(name)
    except md.PackageNotFoundError:
        missing.append(name)
print('MISSING:' + ','.join(missing))
'@
    $out = ''
    try { $out = ($pyCode | & $venvPy - $req 2>&1 | Out-String).Trim() } catch { $out = '' }
    if ($out -match 'MISSING:(.*)$') {
      $m = $Matches[1].Trim()
      $optionalPkgs = @('faster-whisper')   # hanya untuk mic/STT (v14); tanpa ini sisanya tetap jalan
      $miss = @($m -split ',' | Where-Object { $_ -ne '' })
      $hard = @($miss | Where-Object { $optionalPkgs -notcontains $_ })
      $soft = @($miss | Where-Object { $optionalPkgs -contains $_ })
      if ($miss.Count -eq 0) { Say 'OK' 'Semua paket di requirements.txt terpasang' }
      if ($hard.Count -gt 0) { Say 'GAGAL' ('Paket belum terpasang: ' + ($hard -join ', ')) '.\.venv\Scripts\python.exe -m pip install -r requirements.txt' }
      if ($soft.Count -gt 0) { Say 'WARN' ('Paket opsional belum terpasang: ' + ($soft -join ', ') + ' (hanya untuk mic/STT)') 'Abaikan kalau belum memakai mic. Untuk memasang: .\.venv\Scripts\python.exe -m pip install -r requirements.txt' }
    } else {
      Say 'WARN' 'Tidak bisa memeriksa paket requirements.txt' ($out.Substring(0, [Math]::Min(120, $out.Length)))
    }
  }
}

# ---------------------------------------------------------------- 3. node
Head '3. Node dan Electron'
$nodeCmd = Get-Command node -ErrorAction SilentlyContinue
if (-not $nodeCmd) {
  Say 'WARN' 'node tidak ada di PATH' 'Tidak wajib: peluncur memakai electron.exe langsung. Hanya npm install yang butuh Node.'
} else {
  $nv = ''
  try { $nv = (& node --version 2>&1 | Out-String).Trim() } catch { $nv = '' }
  Say 'OK' ('node ' + $nv + ' (' + $nodeCmd.Source + ')')
}
$electronExe = Join-Path $Proyek 'node_modules\electron\dist\electron.exe'
if (Test-Path -LiteralPath $electronExe) { Say 'OK' 'Biner Electron ada' }
else { Say 'GAGAL' 'node_modules\electron\dist\electron.exe tidak ada' 'Jalankan npm install di folder proyek (unduhan Electron ratusan MB).' }
$el = Get-Process -Name electron -ErrorAction SilentlyContinue
if ($el) {
  $mb = [math]::Round((($el | Measure-Object -Property WorkingSet64 -Sum).Sum) / 1MB)
  Say 'INFO' ('Overlay Electron sedang jalan: ' + @($el).Count + ' proses, sekitar ' + $mb + ' MB')
} else {
  Say 'INFO' 'Overlay Electron belum jalan'
}

# ---------------------------------------------------------------- 4. .env
Head '4. Konfigurasi (.env)'
$homeEnv = Join-Path $HOME '.env'
$localEnv = Join-Path $Proyek '.env'
$envHome = Read-EnvFile $homeEnv
$envLocal = Read-EnvFile $localEnv
$cfgEnv = @{}
foreach ($k in $envLocal.Keys) { $cfgEnv[$k] = $envLocal[$k] }
foreach ($k in $envHome.Keys) { $cfgEnv[$k] = $envHome[$k] }   # asumsi: ~/.env menang (belum dicek di server.py)

if (Test-Path -LiteralPath $homeEnv) { Say 'OK' ('~/.env ditemukan (' + $envHome.Count + ' variabel)') }
else { Say 'INFO' '~/.env tidak ada' }
if (Test-Path -LiteralPath $localEnv) { Say 'INFO' ('.env di folder proyek ditemukan (' + $envLocal.Count + ' variabel)') }
if (-not (Test-Path -LiteralPath $homeEnv) -and -not (Test-Path -LiteralPath $localEnv)) {
  Say 'WARN' 'Tidak ada berkas .env sama sekali' 'Salin .env.example lalu isi (mis. kunci Hermes dan token).'
}

$expectSecret = @(
  @{ N = 'HERMES_API_KEY';     Lvl = 'WARN'; Why = 'tanpa ini /agen ke Hermes ditolak (401)' },
  @{ N = 'NINEROUTER_API_KEY'; Lvl = 'WARN'; Why = 'dibutuhkan kalau "Require API key" di 9Router aktif' },
  @{ N = 'COMPANION_TOKEN';    Lvl = 'WARN'; Why = 'tanpa ini /ws dan jembatan web tidak terlindungi token' }
)
foreach ($e in $expectSecret) {
  if ($cfgEnv.ContainsKey($e.N) -and $cfgEnv[$e.N].Length -gt 0) {
    Say 'OK' ($e.N + ' terisi (' + $cfgEnv[$e.N].Length + ' karakter)')
  } else {
    Say $e.Lvl ($e.N + ' kosong atau tidak ada') $e.Why
  }
}
$plain = @('HERMES_URL', 'COMPANION_HOST', 'COMPANION_PORT', 'NINEROUTER_URL', 'VOICEVOX_URL', 'VOICEVOX_SPEAKER', 'NINEROUTER_MODEL')
foreach ($n in $plain) {
  if ($cfgEnv.ContainsKey($n)) { Say 'INFO' ($n + ' = ' + $cfgEnv[$n]) }
}
$others = @()
foreach ($k in ($cfgEnv.Keys | Sort-Object)) {
  if (($plain -notcontains $k) -and (@('HERMES_API_KEY', 'NINEROUTER_API_KEY', 'COMPANION_TOKEN') -notcontains $k)) { $others += $k }
}
if ($others.Count -gt 0) { Say 'INFO' ('Variabel lain (hanya nama): ' + ($others -join ', ')) }
if ($cfgEnv.ContainsKey('COMPANION_HOST')) {
  $h = $cfgEnv['COMPANION_HOST'].Trim()
  if (@('127.0.0.1', 'localhost', '::1') -notcontains $h) {
    Say 'GAGAL' ('COMPANION_HOST = ' + $h) 'Jangan buka server ke jaringan tanpa autentikasi. Kembalikan ke 127.0.0.1.'
  }
}

# ---------------------------------------------------------------- 5. server Iris
Head '5. Server Iris'
$srvPort = 8765
if ($cfgEnv.ContainsKey('COMPANION_PORT')) {
  $pp = 0
  if ([int]::TryParse($cfgEnv['COMPANION_PORT'], [ref]$pp) -and $pp -gt 0) { $srvPort = $pp }
}
$srvUp = $false
$ls = Get-Listener $srvPort
if (-not $ls) {
  Say 'WARN' ('Server Iris belum jalan (port ' + $srvPort + ' kosong)') 'Normal kalau memang belum dinyalakan.'
} else {
  $srvUp = $true
  $cl = ''
  $wp = Get-CimInstance Win32_Process -Filter ('ProcessId=' + $ls.Pid) -ErrorAction SilentlyContinue
  if ($wp) { $cl = [string]$wp.CommandLine }
  if ($cl -match 'server\.py') {
    Say 'OK' ('Server Iris jalan di port ' + $srvPort + ' (PID ' + $ls.Pid + ', ' + $ls.Name + ')')
  } elseif ($cl -eq '') {
    Say 'INFO' ('Port ' + $srvPort + ' dipakai ' + $ls.Name + ' (PID ' + $ls.Pid + '); baris perintah tidak terbaca')
  } else {
    Say 'GAGAL' ('Port ' + $srvPort + ' dipakai proses lain: ' + $ls.Name + ' (PID ' + $ls.Pid + ')') 'Bukan server.py. Kemungkinan server versi WSL atau program lain; hentikan salah satunya.'
  }
  if ($ls.Address -notin @('127.0.0.1', '::1')) {
    Say 'WARN' ('Server mendengar di ' + $ls.Address) 'Seharusnya hanya 127.0.0.1.'
  }
}

# ---------------------------------------------------------------- 6. WSL
Head '6. WSL'
$wslCfgPath = Join-Path $HOME '.wslconfig'
$netMode = ''
if (Test-Path -LiteralPath $wslCfgPath) {
  foreach ($line in (Get-Content -LiteralPath $wslCfgPath)) {
    if ($line -match '^\s*(networkingMode|memory|processors|swap|autoMemoryReclaim|vmIdleTimeout|sparseVhd)\s*=\s*(.+?)\s*$') {
      Say 'INFO' ('.wslconfig: ' + $Matches[1] + ' = ' + $Matches[2])
      if ($Matches[1] -eq 'networkingMode') { $netMode = $Matches[2].ToLower() }
    }
  }
} else {
  Say 'INFO' '.wslconfig tidak ada (bawaan: tanpa batas memori, jaringan NAT)'
}

$wslExe = Get-Command wsl.exe -ErrorAction SilentlyContinue
$wslRunning = $false
if (-not $wslExe) {
  Say 'GAGAL' 'wsl.exe tidak ditemukan' 'Aktifkan fitur WSL di Windows.'
} else {
  $raw = ''
  try { $raw = ((& wsl.exe -l -v 2>&1) | Out-String) -replace "`0", '' } catch { $raw = '' }
  $m = [regex]::Match($raw, '(?m)^\s*\*?\s*' + [regex]::Escape($Distro) + '\s+(\S+)\s+(\d)')
  if (-not $m.Success) {
    Say 'GAGAL' ('Distro "' + $Distro + '" tidak ditemukan') 'Cek nama dengan: wsl -l -v, lalu pakai -Distro <nama>.'
  } else {
    $state = $m.Groups[1].Value
    if ($state -eq 'Running') { $wslRunning = $true; Say 'OK' ($Distro + ' berjalan (WSL' + $m.Groups[2].Value + ')') }
    else { Say 'INFO' ($Distro + ' berstatus ' + $state) 'Normal setelah Iris Stop atau Iris Hermes (mati). Doctor tidak menyalakan WSL; nyalakan lewat Iris Start.bat.' }
  }
}

$pjg = @(Get-CimInstance Win32_Process -Filter "Name='wsl.exe'" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like '*sleep infinity*' })
if ($pjg.Count -gt 0) { Say 'INFO' ('Sesi penjaga WSL (sleep infinity) jalan: ' + $pjg.Count + ' proses') }
else { Say 'INFO' 'Sesi penjaga WSL (sleep infinity) tidak ada' }

$wslLines = @()
if ($wslRunning) {
  try { $wslLines = @((& wsl.exe -d $Distro -- ss -ltn 2>&1) | ForEach-Object { [string]$_ }) } catch { $wslLines = @() }
  $lst = Get-WslListeners $wslLines
  if ($lst.Count -eq 0) {
    Say 'WARN' 'Daftar port di dalam WSL tidak terbaca' 'Perintah ss mungkin tidak ada di distro.'
  } else {
    $watch = @{ 20128 = '9Router'; 8642 = 'Hermes API'; 50021 = 'VOICEVOX' }
    foreach ($e in $lst) {
      if ($watch.ContainsKey($e.Port)) {
        if ($e.Wildcard) {
          if ($netMode -eq 'mirrored') {
            Say 'WARN' ($watch[$e.Port] + ' (port ' + $e.Port + ') mendengar di semua antarmuka, dan WSL memakai mode mirrored') 'Dengan mirrored, ini bisa terjangkau dari jaringan lokal. Ikat ke 127.0.0.1 atau pakai firewall.'
          } else {
            Say 'INFO' ($watch[$e.Port] + ' (port ' + $e.Port + ') mendengar di semua antarmuka di dalam WSL') 'Mode NAT umumnya tidak terbuka ke jaringan lain, tetapi mengikatnya ke 127.0.0.1 lebih aman.'
          }
        } else {
          Say 'OK' ($watch[$e.Port] + ' (port ' + $e.Port + ') hanya di ' + $e.Address + ' dalam WSL')
        }
      } elseif ($e.Wildcard) {
        Say 'INFO' ('Port ' + $e.Port + ' di dalam WSL mendengar di semua antarmuka (layanan belum diketahui)') ('Cek: wsl -d ' + $Distro + ' -- sudo ss -ltnp')
      }
    }
  }
}

# ---------------------------------------------------------------- 6b. disk virtual WSL dan unit systemd
Head '6b. Disk virtual WSL dan layanan systemd'
$script:wslVhdxDrive = ''
$script:wslVhdxText = ''
try {
  $lxd = Get-ChildItem 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Lxss' -ErrorAction Stop |
    ForEach-Object { Get-ItemProperty -LiteralPath $_.PSPath } |
    Where-Object { $_.DistributionName -eq $Distro -and $_.BasePath } | Select-Object -First 1
  if ($lxd) {
    $baseDir = ([string]$lxd.BasePath) -replace '^\\\\\?\\', ''
    $vhd = Join-Path $baseDir 'ext4.vhdx'
    if (Test-Path -LiteralPath $vhd) {
      $vgb = [math]::Round((Get-Item -LiteralPath $vhd).Length / 1GB, 1)
      $script:wslVhdxDrive = $vhd.Substring(0, 1).ToUpper()
      $script:wslVhdxText = ('' + $vgb + ' GB')
      Say 'INFO' ('Disk virtual WSL: ' + $vhd + ' (' + $vgb + ' GB, drive ' + $script:wslVhdxDrive + ':)')
    } else {
      Say 'INFO' ('Disk virtual WSL tidak ditemukan di ' + $baseDir)
    }
  } else {
    Say 'INFO' ('Letak disk virtual WSL untuk "' + $Distro + '" tidak terbaca dari registri')
  }
} catch {
  Say 'INFO' 'Letak disk virtual WSL tidak terbaca dari registri'
}

function Get-UserUnit([string]$DistroName, [string]$Unit) {
  $act = ''
  $en = ''
  try { $act = (((& wsl.exe -d $DistroName -- systemctl --user is-active $Unit 2>&1) | Out-String).Trim() -split "`r?`n")[0].Trim() } catch { $act = '' }
  try { $en = (((& wsl.exe -d $DistroName -- systemctl --user is-enabled $Unit 2>&1) | Out-String).Trim() -split "`r?`n")[0].Trim() } catch { $en = '' }
  $exists = ($en -match '^(enabled|disabled|static|indirect|linked|masked|alias|generated)')
  return [pscustomobject]@{ Unit = $Unit; Active = $act; Enabled = $en; Exists = $exists }
}

if ($wslRunning) {
  $linuxUser = ''
  try { $linuxUser = (((& wsl.exe -d $Distro -- whoami 2>&1) | Out-String).Trim() -split "`r?`n")[0].Trim() } catch { $linuxUser = '' }
  foreach ($u in @('hermes-gateway', 'voicevox', '9router')) {
    $st = Get-UserUnit $Distro $u
    if ($st.Exists -and $st.Active -eq 'active' -and $st.Enabled -eq 'enabled') {
      Say 'OK' ('Unit ' + $u + ': aktif dan otomatis naik (enabled)')
    } elseif ($st.Exists -and $st.Active -eq 'active') {
      Say 'WARN' ('Unit ' + $u + ': aktif tetapi tidak otomatis naik (' + $st.Enabled + ')') ('Aktifkan: wsl -d ' + $Distro + ' -- systemctl --user enable ' + $u)
    } elseif ($st.Exists) {
      Say 'WARN' ('Unit ' + $u + ': ' + $st.Active + ' (' + $st.Enabled + ')') ('Cek: wsl -d ' + $Distro + ' -- systemctl --user status ' + $u + ' --no-pager')
    } elseif ($u -eq '9router') {
      Say 'WARN' '9Router tidak dikelola systemd (tidak ada unit 9router)' 'Kalau jalan, berarti dijalankan manual di terminal: hilang saat terminal ditutup atau WSL restart. Lihat Bagian Q10 (9router.service).'
    } else {
      Say 'INFO' ('Unit ' + $u + ' tidak ditemukan sebagai unit systemd user')
    }
  }
  if (Test-Path -LiteralPath (Join-Path $Proyek 'vv-engine\run.exe')) {
    Say 'INFO' 'vv-engine\run.exe ada: VOICEVOX dijalankan di Windows (DirectML/GPU), bukan di WSL'
    $stVv = Get-UserUnit $Distro 'voicevox'
    if ($stVv.Exists -and $stVv.Enabled -eq 'enabled') {
      Say 'WARN' 'Unit voicevox di WSL masih enabled: ikut naik bersama WSL dan bisa merebut port 50021 dari mesin Windows' ('Matikan permanen (mengubah sistem, jalankan sendiri): wsl -d ' + $Distro + ' -- systemctl --user disable --now voicevox')
    }
  }
  if ($linuxUser -ne '') {
    $lg = ''
    try { $lg = (((& wsl.exe -d $Distro -- loginctl show-user $linuxUser -p Linger 2>&1) | Out-String).Trim() -split "`r?`n")[0].Trim() } catch { $lg = '' }
    if ($lg -eq 'Linger=yes') { Say 'OK' ('Linger aktif untuk ' + $linuxUser + ' (unit user naik tanpa sesi login)') }
    elseif ($lg -ne '') { Say 'WARN' ('Linger belum aktif untuk ' + $linuxUser + ' (' + $lg + ')') ('Unit user tidak naik sendiri tanpa sesi login. Perbaikan (mengubah sistem, jalankan sendiri): wsl -d ' + $Distro + ' -- sudo loginctl enable-linger ' + $linuxUser) }
  }
  $kaLines = @()
  try { $kaLines = @((& wsl.exe -d $Distro -- pgrep -af voicevox_keepalive.sh 2>&1) | ForEach-Object { [string]$_ } | Where-Object { $_ -match '^\d+\s' }) } catch { $kaLines = @() }
  if ($kaLines.Count -gt 0) {
    Say 'INFO' 'voicevox_keepalive.sh masih berjalan (skrip lama untuk VOICEVOX Windows)' 'VOICEVOX kini unit systemd; skrip itu bisa menyalakan VOICEVOX Windows kedua bila mesin Linux lambat naik. Jangan dijalankan lagi setelah peluncur siap.'
  }
}

# ---------------------------------------------------------------- 7. layanan
Head '7. Layanan (VOICEVOX, 9Router, Hermes)'
$lvlDown = 'GAGAL'
if (-not $wslRunning) { $lvlDown = 'INFO' }
function Down-Hint([string]$Orig) {
  if ($wslRunning) { return $Orig }
  return 'WSL sedang mati (normal setelah Iris Stop). Nyalakan lewat Iris Start.bat.'
}
$vvBase = Get-Authority $cfgEnv['VOICEVOX_URL'] 'http://127.0.0.1:50021'
$nrBase = Get-Authority $cfgEnv['NINEROUTER_URL'] 'http://127.0.0.1:20128'
$hmBase = Get-Authority $cfgEnv['HERMES_URL'] 'http://127.0.0.1:8642'

function Owner-Note($Base, $DefaultPort) {
  $pt = Get-PortOf $Base $DefaultPort
  $l = Get-Listener $pt
  if (-not $l) { return '' }
  $note = ' [port ' + $pt + ', dilayani ' + $l.Name + ' PID ' + $l.Pid + ']'
  if ($l.Name -match 'wsl|vmmem') { $note = $note + ' (lewat WSL)' }
  return $note
}

$r = Test-Http ($vvBase + '/version')
if ($r.Replied -and $r.Code -eq 200) {
  Say 'OK' ('VOICEVOX menjawab, versi ' + $r.Body.Trim().Trim('"') + (Owner-Note $vvBase 50021))
} elseif ($r.Replied) {
  Say 'WARN' ('VOICEVOX menjawab HTTP ' + $r.Code + ' di /version') 'Tidak biasa; cek apakah port itu benar-benar VOICEVOX.'
} else {
  Say $lvlDown ('VOICEVOX tidak menjawab di ' + $vvBase) (Down-Hint 'Nyalakan VOICEVOX (suara Iris tidak akan keluar).')
}

$r = Test-Http ($nrBase + '/')
if ($r.Replied) {
  Say 'OK' ('9Router menjawab (HTTP ' + $r.Code + ' di /)' + (Owner-Note $nrBase 20128)) 'Kode HTTP apa pun dianggap hidup; /health sendiri memang tidak ada (404).'
} else {
  Say $lvlDown ('9Router tidak menjawab di ' + $nrBase) (Down-Hint 'Tanpa 9Router, chat dan analisis gambar tidak jalan.')
}

$r = Test-Http ($hmBase + '/health')
if ($r.Replied -and $r.Code -eq 200) {
  Say 'OK' ('Hermes API menjawab HTTP 200' + (Owner-Note $hmBase 8642))
} elseif ($r.Replied) {
  Say 'WARN' ('Hermes API menjawab HTTP ' + $r.Code + ' di /health') 'Gateway hidup tetapi tidak sehat; cek: hermes gateway status (di WSL).'
} else {
  Say $lvlDown ('Hermes API tidak menjawab di ' + $hmBase) (Down-Hint '/agen tidak akan jalan. Cek gateway Hermes di WSL. Jangan restart saat ada tugas berjalan.')
}

# ---------------------------------------------------------------- 8. /health server
if ($srvUp) {
  Head '8. /health dari server Iris'
  $r = Test-Http ('http://127.0.0.1:' + $srvPort + '/health')
  if (-not $r.Replied) {
    Say 'WARN' '/health tidak menjawab' $r.Error
  } elseif ($r.Code -ne 200) {
    Say 'WARN' ('/health menjawab HTTP ' + $r.Code) 'Mungkin ditolak oleh pemeriksaan Origin atau token.'
  } else {
    $shown = $false
    try {
      $j = $r.Body | ConvertFrom-Json -ErrorAction Stop
      foreach ($k in @('voicevox', 'ninerouter', 'hermes', 'agent_confirm', 'ws_token')) {
        $prop = $j.PSObject.Properties[$k]
        if ($prop) {
          $val = ($prop.Value | Out-String).Trim() -replace '\s+', ' '
          if ($val.Length -gt 90) { $val = $val.Substring(0, 90) + '...' }
          Say 'INFO' ('/health ' + $k + ': ' + $val)
          $shown = $true
        }
      }
    } catch { }
    if (-not $shown) { Say 'OK' '/health menjawab HTTP 200 (isi tidak dikenali, tidak ditampilkan)' }
  }
}

# ---------------------------------------------------------------- 9. disk dan RAM
Head '9. Disk dan RAM'
foreach ($d in (Get-PSDrive -PSProvider FileSystem | Where-Object { $_.Used -ne $null -and $_.Free -ne $null })) {
  $total = [double]($d.Used + $d.Free)
  if ($total -le 0) { continue }
  $freeGB = [double]$d.Free / 1GB
  $pct = 100.0 * [double]$d.Free / $total
  $txt = ('Drive ' + $d.Name + ': bebas ' + (Get-FreeText $d.Free) + (' ({0:N1}%)' -f $pct))
  if ($freeGB -lt 5) { Say 'GAGAL' $txt 'Hampir penuh.' }
  elseif ($freeGB -lt $MinFreeGB) {
    $hint = 'Bersihkan dulu sebelum memasang atau memperbarui apa pun.'
    if ($script:wslVhdxDrive -ne '' -and $d.Name -eq $script:wslVhdxDrive) { $hint = $hint + ' Disk virtual WSL (' + $script:wslVhdxText + ') ada di drive ini dan bisa membesar.' }
    Say 'WARN' $txt $hint
  }
  else { Say 'OK' $txt }
}
$os = Get-CimInstance Win32_OperatingSystem -ErrorAction SilentlyContinue
if ($os) {
  $usedPct = 100.0 * ([double]$os.TotalVisibleMemorySize - [double]$os.FreePhysicalMemory) / [double]$os.TotalVisibleMemorySize
  $txt = ('RAM sistem terpakai {0:N0}% dari {1:N1} GB' -f $usedPct, ([double]$os.TotalVisibleMemorySize / 1MB))
  if ($usedPct -ge $RamWarnPct) { Say 'WARN' $txt 'Tinggi. Tutup program lain, kurangi IRIS_WEB_KEEP, atau batasi memori WSL (.wslconfig).' }
  else { Say 'OK' $txt }
}
$vm = Get-Process -Name vmmemWSL, vmmem -ErrorAction SilentlyContinue | Select-Object -First 1
if ($vm) { Say 'INFO' ('Memori WSL (' + $vm.ProcessName + '): sekitar ' + [math]::Round($vm.WorkingSet64 / 1MB) + ' MB') }

# ---------------------------------------------------------------- ringkasan
Write-Host ''
Write-Host ('Ringkasan: {0} OK, {1} INFO, {2} WARN, {3} GAGAL' -f $script:cnt.OK, $script:cnt.INFO, $script:cnt.WARN, $script:cnt.GAGAL) -ForegroundColor White
Write-Host 'Doctor tidak mengubah apa pun. Tempel keluaran ini (tanpa token) kalau minta bantuan.' -ForegroundColor DarkGray
Write-Host ''
if ($script:cnt.GAGAL -gt 0) { exit 1 } else { exit 0 }
