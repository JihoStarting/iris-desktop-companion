<#
iris-update.ps1 (peluncur v1.3.x) - cek dan pasang update komponen Iris. ASCII saja (aman di Windows PowerShell 5.1). by: KangJiho

Pakai:
  powershell -ExecutionPolicy Bypass -File .\iris-update.ps1 -Aksi cek    -Nama semua -Proyek <jalur>
  powershell -ExecutionPolicy Bypass -File .\iris-update.ps1 -Aksi update -Nama router,hermes -Proyek <jalur>
  powershell -ExecutionPolicy Bypass -File .\iris-update.ps1 -Aksi pulihkan -Nama voicevox -Proyek <jalur>
  powershell -ExecutionPolicy Bypass -File .\iris-update.ps1 -Aksi pulihkan -Nama server   -Proyek <jalur>   (paket Python ke snapshot sebelum update terakhir)
Nama : semua | wsl | voicevox | router | hermes | server | overlay | apt | launcher   (boleh beberapa, pisah koma)
Opsi : -Distro Ubuntu  -TungguDetik 90  -TanpaGPU  -Diam (cek tanpa obrolan, hanya baris @@UPD)
       -Seri (cek berurutan; tanpa ini cek banyak komponen berjalan paralel)
       -Launcher <jalur exe> -LauncherVersion 1.3.4 -LauncherRepo pemilik/repo  (untuk update launcher sendiri)

Keluaran mode cek (dibaca Iris Launcher), satu baris per komponen:
  @@UPD|kunci|terpasang|terbaru|status|catatan
  status: terbaru | update | unknown | major | tidakada | skip | galat

Cara tiap komponen di-update:
  wsl      : wsl --update (WSL dimatikan dulu, lalu dinyalakan lagi bersama layanan yang tadi hidup)
  voicevox : unduh voicevox_engine-windows-<varian>-<versi>.7z.* dari GitHub, periksa SHA-256 (bila GitHub menyediakan),
             (WAJIB: tanpa checksum update dibatalkan), ekstrak, tukar folder vv-engine (folder lama disimpan sebagai vv-engine.bak-<waktu>, hanya 1 cadangan
             terakhir; -Aksi pulihkan mengembalikannya)
  router   : npm install -g 9router@latest di dalam WSL (npm yang sama dengan yang memasang 9Router)
  hermes   : hermes update (bawaan Hermes) di dalam WSL
  server   : pip install --upgrade -r requirements.txt di .venv (paket yang di-pin dengan == dilewati)
  overlay  : npm update di folder proyek (hanya naik dalam rentang versi package.json)
  apt      : apt-get update + upgrade di WSL sebagai root (wsl -u root, tanpa password)
  launcher : unduh IrisLauncher*.exe dari rilis terbaru GitHub, periksa SHA-256 (WAJIB) dan ProductName, tukar exe (yang lama jadi .old);
             launcher menawarkan mulai ulang sesudahnya
Setiap update dicatat di %LOCALAPPDATA%\IrisLauncher\update-history.log
Layanan yang sedang hidup dimatikan sebelum update dan dinyalakan lagi sesudahnya.
Kode keluar: 0 = berhasil, 1 = ada yang gagal.
#>
param(
  [Parameter(Mandatory = $true)][ValidateSet('cek', 'update', 'pulihkan')][string]$Aksi,
  [string]$Nama = 'semua',
  [string]$Proyek = '',
  [string]$Distro = 'Ubuntu',
  [int]$TungguDetik = 90,
  [switch]$TanpaGPU,
  [switch]$Diam,
  [switch]$Seri,
  [string]$Launcher = '',
  [string]$LauncherVersion = '',
  [string]$LauncherRepo = ''
)

$ErrorActionPreference = 'Continue'
$ProgressPreference = 'SilentlyContinue'
if ($Proyek) { $Proyek = $Proyek.TrimEnd('\') }
try { [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor 3072 } catch { }

$Semua = @('voicevox', 'router', 'hermes', 'server', 'overlay', 'apt', 'launcher', 'wsl')
$script:NewVer = @{}
$SvcScript = Join-Path $PSScriptRoot 'iris-service.ps1'
$VvUrl = 'http://127.0.0.1:50021/version'
$UrlRouter = 'http://127.0.0.1:20128/'
$UrlHermes = 'http://127.0.0.1:8642/health'
$UrlServer = 'http://127.0.0.1:8765/ping'

# ------------------------------------------------------------ bantu
function Say([string]$Pesan) { if (-not $Diam) { Write-Host $Pesan } }

function Clean([string]$s) {
  if (-not $s) { return '' }
  $t = ($s -replace '[\r\n\|]+', ' ')
  $t = ($t -replace '[^\x20-\x7E]', '').Trim()
  if ($t.Length -gt 140) { $t = $t.Substring(0, 140) }
  return $t
}

function Emit([string]$Key, [string]$Ins, [string]$Lat, [string]$St, [string]$Note) {
  Write-Host ('@@UPD|' + $Key + '|' + (Clean $Ins) + '|' + (Clean $Lat) + '|' + $St + '|' + (Clean $Note))
}

function Strip-Ansi([string]$s) {
  if (-not $s) { return '' }
  $t = [regex]::Replace($s, '\x1b\[[0-9;?]*[A-Za-z]', '')
  return ($t -replace "`0", '')
}

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

function Get-Web([string]$Url, [int]$TimeoutMs = 20000, [string]$Accept = 'application/vnd.github+json') {
  $req = [System.Net.HttpWebRequest]::Create($Url)
  $req.UserAgent = 'IrisLauncher-Updater'
  $req.Accept = $Accept
  $req.Timeout = $TimeoutMs
  $req.ReadWriteTimeout = $TimeoutMs
  $res = $req.GetResponse()
  try {
    $sr = New-Object System.IO.StreamReader($res.GetResponseStream(), [System.Text.Encoding]::UTF8)
    return $sr.ReadToEnd()
  } finally {
    $res.Close()
  }
}

function Get-GhRelease([string]$Repo) {
  $json = Get-Web ('https://api.github.com/repos/' + $Repo + '/releases/latest')
  return ($json | ConvertFrom-Json)
}

function Norm-Ver([string]$s) {
  if (-not $s) { return $null }
  $m = [regex]::Match($s, '\d+(\.\d+){0,3}')
  if (-not $m.Success) { return $null }
  $p = @($m.Value.Split('.'))
  while ($p.Count -lt 3) { $p += '0' }
  try { return [version]($p -join '.') } catch { return $null }
}

function Judge([string]$Ins, [string]$Lat) {
  $a = Norm-Ver $Ins
  $b = Norm-Ver $Lat
  if (-not $b) { return 'galat' }
  if (-not $a) { return 'unknown' }
  if ($a -lt $b) { return 'update' }
  return 'terbaru'
}

function Test-WslJalan {
  $raw = ''
  try { $raw = ((& wsl.exe -l -v 2>&1) | Out-String) -replace "`0", '' } catch { $raw = '' }
  return [regex]::IsMatch($raw, '(?m)^\s*\*?\s*' + [regex]::Escape($Distro) + '\s+Running')
}

# Panggil iris-service.ps1 (nyalakan/matikan satu layanan), keluarannya ikut ke log.
function Svc([string]$Svc, [string]$Cmd) {
  $a = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $SvcScript, '-Nama', $Svc, '-Aksi', $Cmd,
    '-Distro', $Distro, '-TungguDetik', [string]$TungguDetik)
  if ($Proyek) { $a += @('-Proyek', $Proyek) }
  if ($TanpaGPU) { $a += '-TanpaGPU' }
  & powershell.exe @a 2>&1 | ForEach-Object { Write-Host ('   ' + (Strip-Ansi ([string]$_))) }
  return ($LASTEXITCODE -eq 0)
}

# Jalankan skrip bash di WSL lewat berkas sementara (aman dari urusan tanda kutip). stdin dikosongkan.
function Invoke-Wsl([string]$Script, [switch]$Live, [string]$User = '') {
  $txt = $Script -replace "`r", ''
  $b64 = [Convert]::ToBase64String([System.Text.Encoding]::ASCII.GetBytes($txt))
  $tmp = '/tmp/iris-upd-' + [Guid]::NewGuid().ToString('N').Substring(0, 10) + '.sh'
  $cmd = ('echo {0} | base64 -d > {1}; bash {1} < /dev/null; rc=$?; rm -f {1}; exit $rc' -f $b64, $tmp)
  $buf = New-Object System.Collections.ArrayList
  $wa = @('-d', $Distro)
  if ($User) { $wa += @('-u', $User) }
  & wsl.exe @wa -- bash -c $cmd 2>&1 | ForEach-Object {
    $l = Strip-Ansi ([string]$_)
    [void]$buf.Add($l)
    if ($Live -and $l.Trim().Length -gt 0) { Write-Host ('   ' + $l) }
  }
  $code = $LASTEXITCODE
  return @{ Code = $code; Lines = @($buf.ToArray()) }
}

function Get-Tag($Lines, [string]$Tag) {
  foreach ($l in $Lines) {
    if (([string]$l).StartsWith($Tag + '=')) { return ([string]$l).Substring($Tag.Length + 1).Trim() }
  }
  return ''
}

# Periksa SHA-256 terhadap digest dari GitHub ("sha256:<hex>").
# Dengan -Wajib (dipakai untuk berkas yang akan DIJALANKAN: exe launcher dan mesin VOICEVOX) digest yang hilang atau
# tidak dikenal membatalkan update. Tanpa -Wajib: hanya ukuran yang sudah dicek.
function Test-Digest([string]$Path, $Digest, [string]$Label, [switch]$Wajib) {
  if (-not $Digest) {
    if ($Wajib) { throw ('GitHub tidak menyediakan checksum SHA-256 untuk ' + $Label + '; update dibatalkan karena berkas ini akan dijalankan dan keasliannya tidak bisa dipastikan.') }
    Write-Host ('  (GitHub tidak menyediakan checksum untuk ' + $Label + '; hanya ukuran yang dicek)'); return
  }
  $m = [regex]::Match([string]$Digest, '^sha256:([0-9a-fA-F]{64})$')
  if (-not $m.Success) {
    if ($Wajib) { throw ('Format checksum ' + $Label + ' tidak dikenal; update dibatalkan.') }
    Write-Host ('  (format checksum ' + $Label + ' tidak dikenal; dilewati)'); return
  }
  Write-Host ('  memeriksa SHA-256 ' + $Label + ' ...')
  $got = (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLower()
  if ($got -ne $m.Groups[1].Value.ToLower()) { throw ('SHA-256 ' + $Label + ' tidak cocok (didapat ' + $got + ')') }
  Write-Host '  SHA-256 cocok'
}

function Hist([string]$Key, [string]$V0, [string]$V1, [string]$Hasil) {
  try {
    $f = Join-Path (Split-Path $PSScriptRoot -Parent) 'update-history.log'
    $a = '?'; if ($V0) { $a = $V0 }
    $b = '?'; if ($V1) { $b = $V1 }
    $line = ('{0} | {1} | {2} -> {3} | {4}' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $Key, $a, $b, $Hasil)
    Add-Content -LiteralPath $f -Value $line -Encoding UTF8
    if ((Get-Item -LiteralPath $f).Length -gt 204800) {
      $keep = Get-Content -LiteralPath $f -Tail 300
      Set-Content -LiteralPath $f -Value $keep -Encoding UTF8
    }
  } catch { }
}

# ------------------------------------------------------------ skrip bash (di dalam WSL)
$BashPre = @'
export PATH="$HOME/.local/bin:$HOME/.hermes/node/bin:$PATH"
export NVM_DIR="${NVM_DIR:-$HOME/.nvm}"
if [ -s "$NVM_DIR/nvm.sh" ]; then . "$NVM_DIR/nvm.sh" >/dev/null 2>&1; fi
'@

# Cari npm yang SAMA dengan yang memasang 9router (dari unit systemd atau PATH), supaya tidak jadi dua salinan.
$BashFind9 = @'
R=""
PFX=""
for T in $(systemctl --user cat 9router 2>/dev/null | grep -m1 '^ExecStart=' | sed 's/^ExecStart=//'); do
  case "$T" in
    */node_modules/9router/*|*/9router) R="$T"; break;;
  esac
done
if [ -z "$R" ]; then R="$(command -v 9router 2>/dev/null)"; fi
NPM=npm
if [ -n "$R" ]; then
  RP="$(readlink -f "$R" 2>/dev/null)"
  case "$RP" in
    */lib/node_modules/9router/*)
      PFX="${RP%%/lib/node_modules/9router/*}"
      if [ -x "$PFX/bin/npm" ]; then NPM="$PFX/bin/npm"; export PATH="$PFX/bin:$PATH"; fi
      ;;
  esac
fi
'@

$BashRouterVer = @'
INS=""
PJ=""
if [ -n "$PFX" ]; then PJ="$PFX/lib/node_modules/9router/package.json"; fi
if [ -n "$PJ" ] && [ -f "$PJ" ]; then
  INS="$(sed -n 's/.*"version"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' "$PJ" | head -n1)"
else
  INS="$("$NPM" ls -g 9router --depth=0 2>/dev/null | grep -o '9router@[0-9][0-9A-Za-z.+-]*' | head -n1 | cut -d@ -f2)"
fi
echo "INS=$INS"
echo "NPM=$NPM"
exit 0
'@

$BashRouterUpd = @'
echo "NPM=$NPM"
echo "prefix: $("$NPM" config get prefix 2>/dev/null)"
timeout 900 "$NPM" install -g 9router@latest --allow-scripts=9router 2>&1
RC=$?
exit $RC
'@

$BashHermesVer = @'
if ! command -v hermes >/dev/null 2>&1; then exit 0; fi
echo "INS=$(hermes --version 2>&1 | head -n3 | tr '\n' ' ')"
exit 0
'@

$BashAptCheck = @'
export DEBIAN_FRONTEND=noninteractive
timeout 150 apt-get update -qq >/dev/null 2>&1
LST="$(apt-get -s upgrade 2>/dev/null | grep '^Inst ')"
N=0
S=0
if [ -n "$LST" ]; then
  N="$(printf '%s\n' "$LST" | wc -l)"
  S="$(printf '%s\n' "$LST" | grep -ci security)"
fi
echo "N=$N"
echo "SEC=$S"
exit 0
'@

$BashAptUpd = @'
export DEBIAN_FRONTEND=noninteractive
timeout 150 apt-get update 2>&1 | tail -n 3
timeout 2400 apt-get -y -o Dpkg::Options::=--force-confold upgrade 2>&1 | tail -n 25
exit ${PIPESTATUS[0]}
'@

$BashHermesCheck = @'
if ! command -v hermes >/dev/null 2>&1; then echo "NOHERMES=1"; exit 0; fi
echo "INS=$(hermes --version 2>&1 | head -n3 | tr '\n' ' ')"
OUT="$(timeout 120 hermes update --check 2>&1 < /dev/null)"
RC=$?
echo "RC=$RC"
echo "OUT=$(echo "$OUT" | tail -n3 | tr '\n' ' ')"
exit 0
'@

$BashHermesUpd = @'
if ! command -v hermes >/dev/null 2>&1; then echo "GAGAL: perintah hermes tidak ditemukan di WSL"; exit 127; fi
timeout 1800 hermes update 2>&1
exit $?
'@

# Versi terpasang saat ini (untuk riwayat); kosong bila tidak terbaca.
function Get-Ver([string]$Key) {
  try {
    switch ($Key) {
      'wsl' {
        $raw = ((& wsl.exe --version 2>&1) | Out-String) -replace "`0", ''
        $m = [regex]::Match($raw, '\d+\.\d+\.\d+(\.\d+)?')
        if ($m.Success) { return $m.Value }
        return ''
      }
      'voicevox' { return (Get-VvVersion) }
      'router' {
        if (-not (Test-WslJalan)) { return '' }
        $r = Invoke-Wsl ($BashPre + "`n" + $BashFind9 + "`n" + $BashRouterVer)
        return (Get-Tag $r.Lines 'INS')
      }
      'hermes' {
        if (-not (Test-WslJalan)) { return '' }
        $r = Invoke-Wsl ($BashPre + "`n" + $BashHermesVer)
        $m = [regex]::Match((Get-Tag $r.Lines 'INS'), '\d+\.\d+(\.\d+)?')
        if ($m.Success) { return $m.Value }
        return ''
      }
      'launcher' { return $LauncherVersion }
    }
  } catch { }
  return ''
}

# ------------------------------------------------------------ pemeriksaan
function Check-Wsl {
  $raw = ''
  try { $raw = ((& wsl.exe --version 2>&1) | Out-String) -replace "`0", '' } catch { $raw = '' }
  $m = [regex]::Match($raw, '\d+\.\d+\.\d+(\.\d+)?')
  $ins = ''
  if ($m.Success) { $ins = $m.Value }
  $lat = ''
  try { $r = Get-GhRelease 'microsoft/WSL'; $lat = ([string]$r.tag_name).TrimStart('v') } catch {
    Emit 'wsl' $ins '' 'galat' 'Tidak bisa cek versi terbaru (internet?)'
    return
  }
  if (-not $ins) { Emit 'wsl' '' $lat 'unknown' 'Versi WSL terpasang tidak terbaca (WSL lama?)'; return }
  Emit 'wsl' $ins $lat (Judge $ins $lat) ''
}

function Check-Router {
  if (-not (Test-WslJalan)) { Emit 'router' '' '' 'skip' 'WSL mati: nyalakan WSL dulu'; return }
  $lat = ''
  try { $j = (Get-Web 'https://registry.npmjs.org/9router/latest' 20000 '*/*') | ConvertFrom-Json; $lat = [string]$j.version } catch { }
  $r = Invoke-Wsl ($BashPre + "`n" + $BashFind9 + "`n" + $BashRouterVer)
  $ins = Get-Tag $r.Lines 'INS'
  if (-not $lat) { Emit 'router' $ins '' 'galat' 'Tidak bisa cek versi terbaru (internet?)'; return }
  if (-not $ins) { Emit 'router' '' $lat 'tidakada' '9router tidak ditemukan di WSL'; return }
  Emit 'router' $ins $lat (Judge $ins $lat) ''
}

function Check-Hermes {
  if (-not (Test-WslJalan)) { Emit 'hermes' '' '' 'skip' 'WSL mati: nyalakan WSL dulu'; return }
  $r = Invoke-Wsl ($BashPre + "`n" + $BashHermesCheck)
  if ((Get-Tag $r.Lines 'NOHERMES') -eq '1') { Emit 'hermes' '' '' 'tidakada' 'perintah hermes tidak ditemukan di WSL'; return }
  $m = [regex]::Match((Get-Tag $r.Lines 'INS'), '\d+\.\d+(\.\d+)?')
  $ins = ''
  if ($m.Success) { $ins = $m.Value }
  $rc = Get-Tag $r.Lines 'RC'
  $out = Get-Tag $r.Lines 'OUT'
  if ($rc -eq '0') { Emit 'hermes' $ins '' 'terbaru' $out }
  elseif ($rc -eq '1') { Emit 'hermes' $ins '' 'update' $out }
  else { Emit 'hermes' $ins '' 'galat' ('hermes update --check gagal: ' + $out) }
}

function Check-Apt {
  if (-not (Test-WslJalan)) { Emit 'apt' '' '' 'skip' 'WSL mati: nyalakan WSL dulu'; return }
  $r = Invoke-Wsl ($BashAptCheck) -User 'root'
  $n = Get-Tag $r.Lines 'N'
  $sec = Get-Tag $r.Lines 'SEC'
  if (-not $n) { Emit 'apt' '' '' 'galat' 'apt-get tidak memberi hasil (WSL tanpa akses root?)'; return }
  if ([int]$n -gt 0) {
    $cat = [string]$n + ' paket Ubuntu bisa di-upgrade'
    if ($sec -and ([int]$sec -gt 0)) { $cat += ' (' + $sec + ' keamanan)' }
    Emit 'apt' '' '' 'update' $cat
  } else {
    Emit 'apt' '' '' 'terbaru' 'Semua paket Ubuntu di WSL terkini'
  }
}

function Check-Launcher {
  if (-not $LauncherRepo) { Emit 'launcher' $LauncherVersion '' 'skip' 'Repo GitHub launcher belum diisi di Pengaturan'; return }
  $lat = ''
  try { $r = Get-GhRelease $LauncherRepo; $lat = ([string]$r.tag_name).TrimStart('v') } catch {
    Emit 'launcher' $LauncherVersion '' 'galat' ('Rilis launcher tidak terbaca dari ' + $LauncherRepo + ' (belum ada rilis / repo salah / internet?)')
    return
  }
  Emit 'launcher' $LauncherVersion $lat (Judge $LauncherVersion $lat) ''
}

function Get-VvVariant {
  $d = Join-Path $Proyek 'vv-engine'
  $dml = Get-ChildItem -LiteralPath $d -Filter 'DirectML.dll' -Recurse -File -ErrorAction SilentlyContinue | Select-Object -First 1
  if ($dml) { return 'directml' }
  $cuda = Get-ChildItem -LiteralPath $d -Filter 'onnxruntime_providers_cuda.dll' -Recurse -File -ErrorAction SilentlyContinue | Select-Object -First 1
  if ($cuda) { return 'nvidia' }
  return 'cpu'
}

function Get-VvVersion {
  $mf = Join-Path $Proyek 'vv-engine\engine_manifest.json'
  if (Test-Path -LiteralPath $mf) {
    try {
      $j = (Get-Content -LiteralPath $mf -Raw -Encoding UTF8) | ConvertFrom-Json
      if ($j.version) { return [string]$j.version }
    } catch { }
  }
  $mk = Join-Path $Proyek 'vv-engine\iris-version.txt'
  if (Test-Path -LiteralPath $mk) {
    try { $t = (Get-Content -LiteralPath $mk -Raw).Trim(); if ($t) { return $t } } catch { }
  }
  try {
    $t = (Get-Web $VvUrl 3000 '*/*').Trim().Trim('"')
    if ($t) { return $t }
  } catch { }
  return ''
}

function Check-Voice {
  if (-not $Proyek -or -not (Test-Path -LiteralPath (Join-Path $Proyek 'vv-engine\run.exe'))) {
    Emit 'voicevox' '' '' 'skip' 'VOICEVOX berjalan di WSL atau vv-engine tidak ada: update manual'
    return
  }
  $ins = Get-VvVersion
  $lat = ''
  try { $r = Get-GhRelease 'VOICEVOX/voicevox_engine'; $lat = ([string]$r.tag_name).TrimStart('v') } catch {
    Emit 'voicevox' $ins '' 'galat' 'Tidak bisa cek versi terbaru (internet?)'
    return
  }
  Emit 'voicevox' $ins $lat (Judge $ins $lat) ('varian ' + (Get-VvVariant))
}

function Req-Names([string]$Path) {
  $names = @{}
  foreach ($ln in (Get-Content -LiteralPath $Path -ErrorAction SilentlyContinue)) {
    $t = ([string]$ln).Trim()
    if ($t.Length -eq 0 -or $t.StartsWith('#') -or $t.StartsWith('-')) { continue }
    $m = [regex]::Match($t, '^([A-Za-z0-9][A-Za-z0-9_.\-]*)')
    if (-not $m.Success) { continue }
    $n = $m.Groups[1].Value.ToLower().Replace('_', '-').Replace('.', '-')
    $names[$n] = ($t -match '==')
  }
  return $names
}

function Check-Server {
  if (-not $Proyek) { Emit 'server' '' '' 'skip' 'Folder proyek belum diatur'; return }
  $py = Join-Path $Proyek '.venv\Scripts\python.exe'
  $rq = Join-Path $Proyek 'requirements.txt'
  if (-not (Test-Path -LiteralPath $py)) { Emit 'server' '' '' 'tidakada' '.venv belum dibuat'; return }
  if (-not (Test-Path -LiteralPath $rq)) { Emit 'server' '' '' 'skip' 'requirements.txt tidak ada'; return }
  $req = Req-Names $rq
  $raw = ''
  try { $raw = ((& $py -m pip list --outdated --format=json --disable-pip-version-check 2>$null) | Out-String).Trim() } catch { }
  if ($LASTEXITCODE -ne 0 -and -not $raw) { Emit 'server' '' '' 'galat' 'pip list --outdated gagal (internet?)'; return }
  $list = @()
  try { if ($raw) { $list = @($raw | ConvertFrom-Json) } } catch { Emit 'server' '' '' 'galat' 'Keluaran pip tidak terbaca'; return }
  $naik = @()
  $pin = 0
  foreach ($p in $list) {
    $k = ([string]$p.name).ToLower().Replace('_', '-').Replace('.', '-')
    if (-not $req.ContainsKey($k)) { continue }
    if ($req[$k]) { $pin++; continue }
    $naik += ([string]$p.name + ' ' + [string]$p.version + '>' + [string]$p.latest_version)
  }
  $cat = ''
  if ($pin -gt 0) { $cat = ' (' + $pin + ' paket di-pin dilewati)' }
  if ($naik.Count -gt 0) {
    $tampil = ($naik | Select-Object -First 3) -join ', '
    if ($naik.Count -gt 3) { $tampil += ', ...' }
    Emit 'server' '' '' 'update' ([string]$naik.Count + ' paket: ' + $tampil + $cat)
  } else {
    Emit 'server' '' '' 'terbaru' ('Semua paket di requirements.txt terkini' + $cat)
  }
}

function Get-Npm {
  $c = Get-Command npm.cmd -ErrorAction SilentlyContinue
  if ($c) { return $c.Source }
  $p = Join-Path $env:ProgramFiles 'nodejs\npm.cmd'
  if (Test-Path -LiteralPath $p) { return $p }
  return $null
}

function Check-Overlay {
  if (-not $Proyek) { Emit 'overlay' '' '' 'skip' 'Folder proyek belum diatur'; return }
  if (-not (Test-Path -LiteralPath (Join-Path $Proyek 'package.json'))) { Emit 'overlay' '' '' 'tidakada' 'package.json tidak ada'; return }
  if (-not (Test-Path -LiteralPath (Join-Path $Proyek 'node_modules'))) { Emit 'overlay' '' '' 'tidakada' 'node_modules belum ada (jalankan npm install)'; return }
  if ((Test-Path -LiteralPath (Join-Path $Proyek 'node_modules\electron\install.js')) -and -not (Test-Path -LiteralPath (Join-Path $Proyek 'node_modules\electron\dist\electron.exe'))) {
    Emit 'overlay' '' '' 'update' 'Biner Electron hilang (electron.exe): klik Update untuk mengunduh ulang'; return
  }
  $npm = Get-Npm
  if (-not $npm) { Emit 'overlay' '' '' 'skip' 'npm tidak ada di PATH Windows (Node.js belum terpasang)'; return }
  $raw = ''
  $kode = 0
  Push-Location -LiteralPath $Proyek
  try {
    $raw = ((& $npm outdated --json 2>$null) | Out-String).Trim()
    $kode = $LASTEXITCODE
  } catch { } finally { Pop-Location }
  if ($kode -ne 0 -and -not $raw) { Emit 'overlay' '' '' 'galat' 'npm outdated gagal (internet?)'; return }
  $obj = $null
  try { if ($raw) { $obj = $raw | ConvertFrom-Json } } catch { Emit 'overlay' '' '' 'galat' 'Keluaran npm tidak terbaca'; return }
  $naik = @()
  $mayor = @()
  $eIns = ''
  $eLat = ''
  if ($obj) {
    foreach ($p in $obj.PSObject.Properties) {
      $cur = [string]$p.Value.current
      $wan = [string]$p.Value.wanted
      $lat = [string]$p.Value.latest
      if (-not $cur -or $cur -eq 'MISSING') { continue }
      $a = Norm-Ver $cur
      $w = Norm-Ver $wan
      $l = Norm-Ver $lat
      if ($p.Name -eq 'electron') { $eIns = $cur; $eLat = $wan }
      if ($a -and $w -and ($a -lt $w)) { $naik += ($p.Name + ' ' + $cur + '>' + $wan) }
      elseif ($w -and $l -and ($w -lt $l)) { $mayor += ($p.Name + ' ' + $cur + '>' + $lat) }
    }
  }
  if ($naik.Count -gt 0) {
    $tampil = ($naik | Select-Object -First 3) -join ', '
    if ($naik.Count -gt 3) { $tampil += ', ...' }
    Emit 'overlay' $eIns $eLat 'update' ([string]$naik.Count + ' paket npm: ' + $tampil)
  } elseif ($mayor.Count -gt 0) {
    $tampil = ($mayor | Select-Object -First 3) -join ', '
    Emit 'overlay' '' '' 'major' ('Versi mayor (tidak otomatis, ubah package.json sendiri): ' + $tampil)
  } else {
    Emit 'overlay' '' '' 'terbaru' 'Semua paket npm terkini'
  }
}

# ------------------------------------------------------------ pemasangan
function Download-File([string]$Url, [string]$Dest, [long]$Size) {
  $leaf = Split-Path $Dest -Leaf
  if ((Test-Path -LiteralPath $Dest) -and $Size -gt 0 -and ((Get-Item -LiteralPath $Dest).Length -eq $Size)) {
    Write-Host ('  sudah ada: ' + $leaf)
    return
  }
  $tmp = $Dest + '.part'
  $req = [System.Net.HttpWebRequest]::Create($Url)
  $req.UserAgent = 'IrisLauncher-Updater'
  $req.Timeout = 30000
  $req.ReadWriteTimeout = 60000
  $res = $req.GetResponse()
  $len = $res.ContentLength
  if ($len -le 0) { $len = $Size }
  $in = $res.GetResponseStream()
  $out = [System.IO.File]::Create($tmp)
  $got = 0L
  try {
    $buf = New-Object byte[] 1048576
    $t0 = Get-Date
    $tl = $t0
    while (($n = $in.Read($buf, 0, $buf.Length)) -gt 0) {
      $out.Write($buf, 0, $n)
      $got += $n
      if (((Get-Date) - $tl).TotalSeconds -ge 8) {
        $tl = Get-Date
        $dt = ($tl - $t0).TotalSeconds
        if ($dt -lt 1) { $dt = 1 }
        $pct = 0
        if ($len -gt 0) { $pct = [int](100 * $got / $len) }
        Write-Host ('  {0}: {1:N0} MB ({2}%)  {3:N1} MB/dtk' -f $leaf, ($got / 1MB), $pct, (($got / 1MB) / $dt))
      }
    }
  } finally {
    $out.Close()
    $in.Close()
    $res.Close()
  }
  if ($Size -gt 0 -and $got -ne $Size) { throw ('Unduhan ' + $leaf + ' tidak lengkap (' + $got + ' dari ' + $Size + ' byte)') }
  if (Test-Path -LiteralPath $Dest) { Remove-Item -LiteralPath $Dest -Force }
  Move-Item -LiteralPath $tmp -Destination $Dest
  Write-Host ('  selesai: ' + $leaf)
}

function Find-7z {
  $cand = @(
    (Join-Path $env:ProgramFiles '7-Zip\7z.exe'),
    (Join-Path ${env:ProgramFiles(x86)} '7-Zip\7z.exe')
  )
  foreach ($c in $cand) { if ($c -and (Test-Path -LiteralPath $c)) { return $c } }
  $g = Get-Command 7z.exe -ErrorAction SilentlyContinue
  if ($g) { return $g.Source }
  $g = Get-Command 7za.exe -ErrorAction SilentlyContinue
  if ($g) { return $g.Source }
  return $null
}

function Update-Voice {
  if (-not $Proyek) { Write-Host 'GAGAL: folder proyek belum diatur.'; return $false }
  $vvDir = Join-Path $Proyek 'vv-engine'
  if (-not (Test-Path -LiteralPath (Join-Path $vvDir 'run.exe'))) {
    Write-Host 'GAGAL: vv-engine\run.exe tidak ada (VOICEVOX di WSL tidak di-update dari sini).'
    return $false
  }
  $insVer = Get-VvVersion
  $variant = Get-VvVariant
  Write-Host ('Mengambil info rilis VOICEVOX Engine (varian ' + $variant + ', terpasang: ' + $(if ($insVer) { $insVer } else { 'tidak terbaca' }) + ')...')
  $rel = Get-GhRelease 'VOICEVOX/voicevox_engine'
  $tag = ([string]$rel.tag_name).TrimStart('v')
  if ($insVer -and ((Judge $insVer $tag) -eq 'terbaru')) { Write-Host ('VOICEVOX sudah terbaru (' + $insVer + ').'); return $true }
  $assets = @($rel.assets | Where-Object { $_.name -like ('voicevox_engine-windows-' + $variant + '-*') -and $_.name -match '\.7z(\.\d+)?$' } | Sort-Object name)
  if ($assets.Count -eq 0) {
    Write-Host ('GAGAL: aset windows-' + $variant + ' tidak ada di rilis ' + $tag + '. Aset yang ada:')
    foreach ($a in $rel.assets) { Write-Host ('   ' + $a.name) }
    return $false
  }
  $total = [long](($assets | Measure-Object -Property size -Sum).Sum)
  Write-Host ('Rilis ' + $tag + ': ' + $assets.Count + ' berkas, total ' + [int]($total / 1MB) + ' MB')

  try {
    $free = (Get-Item -LiteralPath $Proyek).PSDrive.Free
    if ($free -and ($free -lt ($total * 3.5))) {
      Write-Host ('GAGAL: ruang kosong drive proyek ' + [int]($free / 1MB) + ' MB, butuh sekitar ' + [int]($total * 3.5 / 1MB) + ' MB (unduhan + hasil ekstrak + cadangan).')
      return $false
    }
  } catch { }

  $wd = Join-Path $Proyek '_update\voicevox'
  $xd = Join-Path $wd 'x'
  New-Item -ItemType Directory -Force -Path $wd | Out-Null
  if (Test-Path -LiteralPath $xd) { Remove-Item -LiteralPath $xd -Recurse -Force -ErrorAction SilentlyContinue }
  New-Item -ItemType Directory -Force -Path $xd | Out-Null

  $files = @()
  foreach ($a in $assets) {
    $dest = Join-Path $wd $a.name
    Write-Host ('Mengunduh ' + $a.name + ' (' + [int]($a.size / 1MB) + ' MB)...')
    Download-File $a.browser_download_url $dest ([long]$a.size)
    try { Test-Digest $dest $a.digest $a.name -Wajib } catch { Remove-Item -LiteralPath $dest -Force -ErrorAction SilentlyContinue; throw }
    $files += $dest
  }

  $combined = $files[0]
  if ($files.Count -gt 1) {
    $combined = Join-Path $wd 'engine.7z'
    Write-Host 'Menyatukan bagian-bagian arsip...'
    $o = [System.IO.File]::Create($combined)
    try {
      foreach ($f in $files) {
        $i = [System.IO.File]::OpenRead($f)
        try { $i.CopyTo($o, 4194304) } finally { $i.Close() }
        Remove-Item -LiteralPath $f -Force
      }
    } finally { $o.Close() }
  }

  Write-Host 'Mengekstrak (beberapa menit)...'
  $sz = Find-7z
  $okx = $false
  if ($sz) {
    Write-Host ('  memakai ' + $sz)
    & $sz x -y ('-o' + $xd) $combined 2>&1 | Out-Null
    $okx = ($LASTEXITCODE -le 1)
  } else {
    $tar = Join-Path $env:WINDIR 'System32\tar.exe'
    if (Test-Path -LiteralPath $tar) {
      Write-Host '  7-Zip tidak ditemukan; mencoba tar.exe bawaan Windows'
      & $tar -xf $combined -C $xd 2>&1 | Out-Null
      $okx = ($LASTEXITCODE -eq 0)
    }
  }
  if (-not $okx) {
    Write-Host 'GAGAL mengekstrak. Pasang 7-Zip (7-zip.org) lalu ulangi; arsip yang sudah diunduh tetap disimpan di _update\voicevox.'
    return $false
  }
  $run = Get-ChildItem -LiteralPath $xd -Filter 'run.exe' -Recurse -File -ErrorAction SilentlyContinue |
    Sort-Object { $_.FullName.Length } | Select-Object -First 1
  if (-not $run) { Write-Host 'GAGAL: run.exe tidak ditemukan di hasil ekstrak.'; return $false }
  $newDir = $run.DirectoryName
  Write-Host ('Hasil ekstrak: ' + $newDir)

  $was = ((Get-HttpCode $VvUrl) -gt 0)
  Write-Host 'Mematikan VOICEVOX untuk menukar folder...'
  [void](Svc 'voicevox' 'mati')
  $bakName = 'vv-engine.bak-' + (Get-Date -Format 'yyyyMMdd-HHmmss')
  $bak = Join-Path $Proyek $bakName
  $ok = $false
  try {
    Rename-Item -LiteralPath $vvDir -NewName $bakName -ErrorAction Stop
    try {
      Move-Item -LiteralPath $newDir -Destination $vvDir -ErrorAction Stop
      $ok = $true
    } catch {
      Write-Host ('GAGAL memindahkan folder baru: ' + $_.Exception.Message)
      Rename-Item -LiteralPath $bak -NewName 'vv-engine' -ErrorAction SilentlyContinue
    }
  } catch {
    Write-Host ('GAGAL mengganti nama folder lama (masih dipakai proses lain?): ' + $_.Exception.Message)
  }
  if ($ok) {
    try { Set-Content -LiteralPath (Join-Path $vvDir 'iris-version.txt') -Value $tag -Encoding ASCII } catch { }
    $script:NewVer['voicevox'] = $tag
    Write-Host ('VOICEVOX Engine sekarang ' + $tag + '. Folder lama disimpan: ' + $bakName + ' (bisa dipulihkan dari dialog Update)')
    Get-ChildItem -LiteralPath $Proyek -Directory -Filter 'vv-engine.bak-*' -ErrorAction SilentlyContinue |
      Where-Object { $_.Name -ne $bakName } | ForEach-Object {
        Remove-Item -LiteralPath $_.FullName -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host ('Cadangan lama dihapus: ' + $_.Name)
      }
    Remove-Item -LiteralPath (Join-Path $Proyek '_update') -Recurse -Force -ErrorAction SilentlyContinue
  }
  if ($was -or $ok) {
    if ($was) { [void](Svc 'voicevox' 'nyala') }
  }
  return $ok
}

function Update-Router {
  if (-not (Test-WslJalan)) { Write-Host 'GAGAL: WSL mati. Nyalakan WSL dulu (klik chip WSL).'; return $false }
  $was = ((Get-HttpCode $UrlRouter) -gt 0)
  if ($was) { Write-Host 'Mematikan 9Router sebentar...'; [void](Svc 'router' 'mati') }
  Write-Host 'Menjalankan npm install -g 9router@latest di WSL...'
  $r = Invoke-Wsl ($BashPre + "`n" + $BashFind9 + "`n" + $BashRouterUpd) -Live
  if ($r.Code -ne 0 -and (($r.Lines -join "`n") -match 'EACCES|permission denied')) {
    # Sengaja TIDAK mengulang sebagai root: skrip pasang paket npm akan ikut berjalan sebagai root.
    Write-Host 'GAGAL: izin ditolak saat menulis ke folder npm global di WSL.'
    Write-Host '  Launcher tidak mengulang sebagai root secara otomatis. Sebaiknya folder npm global dijadikan milik user biasa.'
    Write-Host ('  Kalau tetap mau memakai root, jalankan sendiri (sesuaikan jalur npm bila memakai nvm): wsl -d ' + $Distro + ' -u root -- npm install -g 9router@latest')
  }
  $ok = ($r.Code -eq 0)
  if ($was) { Write-Host 'Menyalakan 9Router lagi...'; [void](Svc 'router' 'nyala') }
  if ($ok) { Write-Host '9Router ter-update.' }
  return $ok
}

function Update-Hermes {
  if (-not (Test-WslJalan)) { Write-Host 'GAGAL: WSL mati. Nyalakan WSL dulu (klik chip WSL).'; return $false }
  Write-Host 'Menjalankan hermes update di WSL (gateway Hermes dimulai ulang sendiri bila sedang jalan)...'
  $r = Invoke-Wsl ($BashPre + "`n" + $BashHermesUpd) -Live
  $ok = ($r.Code -eq 0)
  if ((Get-HttpCode $UrlHermes) -eq 0) {
    Write-Host 'Hermes belum menjawab; mencoba menyalakan...'
    [void](Svc 'hermes' 'nyala')
  }
  if ($ok) { Write-Host 'Hermes ter-update.' }
  return $ok
}

# Snapshot "pip freeze" sebelum update server.py (satu generasi), di samping update-history.log.
function Get-PipSnap { return (Join-Path (Split-Path $PSScriptRoot -Parent) 'pip-pre-update.txt') }

function Rollback-Server {
  $py = Join-Path $Proyek '.venv\Scripts\python.exe'
  $snap = Get-PipSnap
  if (-not (Test-Path -LiteralPath $py)) { Write-Host 'GAGAL: .venv\Scripts\python.exe tidak ada.'; return $false }
  if (-not (Test-Path -LiteralPath $snap)) { Write-Host 'GAGAL: belum ada snapshot paket Python (dibuat otomatis tiap kali server.py di-update).'; return $false }
  $was = ((Get-HttpCode $UrlServer) -gt 0)
  if ($was) { Write-Host 'Mematikan server.py sebentar...'; [void](Svc 'server' 'mati') }
  Write-Host 'Mengembalikan paket Python dari snapshot ...'
  & $py -m pip install -r $snap --disable-pip-version-check 2>&1 | ForEach-Object { Write-Host ('   ' + (Strip-Ansi ([string]$_))) }
  $ok = ($LASTEXITCODE -eq 0)
  if ($was) { Write-Host 'Menyalakan server.py lagi...'; [void](Svc 'server' 'nyala') }
  if ($ok) { Write-Host 'Paket Python dipulihkan ke versi sebelum update terakhir.' } else { Write-Host 'GAGAL: pip mengembalikan galat (lihat baris di atas).' }
  return $ok
}

function Update-Server {
  $py = Join-Path $Proyek '.venv\Scripts\python.exe'
  $rq = Join-Path $Proyek 'requirements.txt'
  if (-not (Test-Path -LiteralPath $py)) { Write-Host 'GAGAL: .venv\Scripts\python.exe tidak ada.'; return $false }
  if (-not (Test-Path -LiteralPath $rq)) { Write-Host 'GAGAL: requirements.txt tidak ada.'; return $false }
  # Snapshot versi paket sekarang (pip freeze) supaya update yang gagal atau merusak bisa dikembalikan.
  $snap = Get-PipSnap
  $snapOk = $false
  try {
    $fr = @(& $py -m pip freeze --disable-pip-version-check 2>$null)
    if ($LASTEXITCODE -eq 0 -and $fr.Count -gt 0) {
      Set-Content -LiteralPath $snap -Value $fr -Encoding UTF8
      $snapOk = $true
      Write-Host ('Snapshot paket Python disimpan (' + $fr.Count + ' paket) untuk pemulihan.')
    }
  } catch { }
  if (-not $snapOk) { Write-Host 'PERINGATAN: snapshot paket Python gagal dibuat; pemulihan otomatis tidak tersedia untuk update ini.' }
  $was = ((Get-HttpCode $UrlServer) -gt 0)
  if ($was) { Write-Host 'Mematikan server.py sebentar...'; [void](Svc 'server' 'mati') }
  Write-Host 'Menjalankan pip install --upgrade -r requirements.txt ...'
  & $py -m pip install --upgrade -r $rq --disable-pip-version-check 2>&1 | ForEach-Object { Write-Host ('   ' + (Strip-Ansi ([string]$_))) }
  $ok = ($LASTEXITCODE -eq 0)
  if (-not $ok -and $snapOk) {
    Write-Host 'pip gagal; mengembalikan paket ke versi sebelum update...'
    & $py -m pip install -r $snap --disable-pip-version-check 2>&1 | ForEach-Object { Write-Host ('   ' + (Strip-Ansi ([string]$_))) }
    if ($LASTEXITCODE -eq 0) { Write-Host 'Paket Python dikembalikan ke keadaan sebelum update.' }
    else { Write-Host 'GAGAL mengembalikan paket otomatis. Coba menu Alat > Pulihkan paket Python.' }
  }
  if ($was) { Write-Host 'Menyalakan server.py lagi...'; [void](Svc 'server' 'nyala') }
  if ($ok) { Write-Host 'Paket Python ter-update.' } else { Write-Host 'GAGAL: pip mengembalikan galat (lihat baris di atas).' }
  return $ok
}

function Test-OverlayJalan {
  $prefix = $Proyek + '\'
  $j = @(Get-CimInstance Win32_Process -Filter "Name='electron.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.ExecutablePath -and $_.ExecutablePath.StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase) })
  return ($j.Count -gt 0)
}

# v1.3.1: npm update bisa mengganti paket electron tanpa mengunduh biner node_modules\electron\dist\electron.exe
# (skrip pasca-pasang tidak jalan atau gagal diam-diam; npm tetap mengembalikan kode 0). Cek dan pasang ulang lewat install.js milik electron.
function Repair-Electron {
  $exe = Join-Path $Proyek 'node_modules\electron\dist\electron.exe'
  if (Test-Path -LiteralPath $exe) { return $true }
  $inst = Join-Path $Proyek 'node_modules\electron\install.js'
  if (-not (Test-Path -LiteralPath $inst)) { return $true }   # proyek ini tidak memakai paket electron
  $node = $null
  $c = Get-Command node -ErrorAction SilentlyContinue
  if ($c) { $node = $c.Source }
  if (-not $node) {
    $np = Get-Npm
    if ($np) { $cand = Join-Path (Split-Path $np -Parent) 'node.exe'; if (Test-Path -LiteralPath $cand) { $node = $cand } }
  }
  if (-not $node) { Write-Host 'GAGAL: electron.exe tidak ada dan node.exe tidak ditemukan untuk mengunduhnya.'; return $false }
  Write-Host 'Biner Electron belum ada setelah npm update; mengunduh ulang (ratusan MB, bisa beberapa menit)...'
  $out = ''
  Push-Location -LiteralPath $Proyek
  try { $out = (& $node $inst 2>&1 | Out-String) } catch { $out = [string]$_ } finally { Pop-Location }
  if (Test-Path -LiteralPath $exe) { Write-Host 'Biner Electron terpasang.'; return $true }
  $t = (Strip-Ansi $out)
  if ($t.Length -gt 300) { $t = $t.Substring($t.Length - 300) }
  Write-Host ('GAGAL: electron.exe masih tidak ada. Keluaran install.js (akhir): ' + $t.Trim())
  return $false
}

function Update-Overlay {
  if (-not (Test-Path -LiteralPath (Join-Path $Proyek 'package.json'))) { Write-Host 'GAGAL: package.json tidak ada.'; return $false }
  $npm = Get-Npm
  if (-not $npm) { Write-Host 'GAGAL: npm tidak ada di PATH Windows (Node.js belum terpasang).'; return $false }
  $was = Test-OverlayJalan
  if ($was) { Write-Host 'Menutup overlay sebentar...'; [void](Svc 'overlay' 'mati') }
  Write-Host 'Menjalankan npm update (bila Electron naik versi, unduhannya ratusan MB)...'
  Push-Location -LiteralPath $Proyek
  try {
    & $npm update --no-fund --no-audit 2>&1 | ForEach-Object { Write-Host ('   ' + (Strip-Ansi ([string]$_))) }
    $ok = ($LASTEXITCODE -eq 0)
  } finally { Pop-Location }
  if ($ok) { $ok = (Repair-Electron) }
  if ($was) { Write-Host 'Membuka overlay lagi...'; [void](Svc 'overlay' 'nyala') }
  if ($ok) { Write-Host 'Paket overlay ter-update.' } else { Write-Host 'GAGAL: npm update mengembalikan galat.' }
  return $ok
}

function Update-Apt {
  if (-not (Test-WslJalan)) { Write-Host 'GAGAL: WSL mati. Nyalakan WSL dulu (klik chip WSL).'; return $false }
  Write-Host 'Menjalankan apt-get update dan upgrade di WSL sebagai root (bisa beberapa menit)...'
  $r = Invoke-Wsl $BashAptUpd -Live -User 'root'
  $ok = ($r.Code -eq 0)
  if ($ok) { Write-Host 'Paket Ubuntu ter-update. (Bila kernel/systemd ikut naik, WSL baru memakainya setelah dimatikan lalu dinyalakan lagi.)' }
  else { Write-Host 'GAGAL: apt-get upgrade mengembalikan galat (lihat baris di atas).' }
  return $ok
}

function Update-Launcher {
  if (-not $LauncherRepo) { Write-Host 'GAGAL: repo GitHub launcher belum diisi di Pengaturan.'; return $false }
  if (-not $Launcher -or -not (Test-Path -LiteralPath $Launcher)) { Write-Host 'GAGAL: jalur IrisLauncher.exe tidak diketahui.'; return $false }
  $rel = Get-GhRelease $LauncherRepo
  $tag = ([string]$rel.tag_name).TrimStart('v')
  if ((Judge $LauncherVersion $tag) -eq 'terbaru') { Write-Host ('Launcher sudah terbaru (' + $LauncherVersion + ').'); return $true }
  $asset = $rel.assets | Where-Object { $_.name -match '^IrisLauncher.*\.exe$' } | Select-Object -First 1
  if (-not $asset) {
    Write-Host ('GAGAL: rilis ' + $tag + ' tidak punya berkas IrisLauncher*.exe. Aset yang ada:')
    foreach ($a in $rel.assets) { Write-Host ('   ' + $a.name) }
    return $false
  }
  $new = $Launcher + '.new'
  $old = $Launcher + '.old'
  Write-Host ('Mengunduh ' + $asset.name + ' (' + [int]($asset.size / 1KB) + ' KB) untuk versi ' + $tag + '...')
  if (Test-Path -LiteralPath $new) { Remove-Item -LiteralPath $new -Force }
  Download-File $asset.browser_download_url $new ([long]$asset.size)
  try { Test-Digest $new $asset.digest $asset.name -Wajib } catch { Remove-Item -LiteralPath $new -Force -ErrorAction SilentlyContinue; throw }
  $hdr = New-Object byte[] 2
  $fs = [System.IO.File]::OpenRead($new)
  try { [void]$fs.Read($hdr, 0, 2) } finally { $fs.Close() }
  if ($hdr[0] -ne 0x4D -or $hdr[1] -ne 0x5A -or (Get-Item -LiteralPath $new).Length -lt 102400) {
    Remove-Item -LiteralPath $new -Force -ErrorAction SilentlyContinue
    Write-Host 'GAGAL: berkas unduhan bukan program Windows yang valid.'
    return $false
  }
  # Pastikan ini memang Iris Launcher (ProductName dari AssemblyProduct) dan bandingkan versinya dengan tag rilis.
  $pn = ''
  $fv = ''
  try { $vi = (Get-Item -LiteralPath $new).VersionInfo; $pn = [string]$vi.ProductName; $fv = [string]$vi.FileVersion } catch { }
  if ($pn -ne 'Iris Launcher') {
    Remove-Item -LiteralPath $new -Force -ErrorAction SilentlyContinue
    Write-Host ('GAGAL: berkas unduhan bukan Iris Launcher (ProductName: "' + $pn + '").')
    return $false
  }
  if ((Judge $fv $tag) -eq 'update') {
    Write-Host ('PERINGATAN: versi di dalam exe (' + $fv + ') lebih rendah dari tag rilis (' + $tag + '). Tombol Update akan terus menawarkan update; samakan AssemblyVersion dengan tag saat membuat rilis.')
  }
  if (Test-Path -LiteralPath $old) { Remove-Item -LiteralPath $old -Force -ErrorAction SilentlyContinue }
  try {
    Rename-Item -LiteralPath $Launcher -NewName (Split-Path $old -Leaf) -ErrorAction Stop
  } catch {
    Remove-Item -LiteralPath $new -Force -ErrorAction SilentlyContinue
    Write-Host ('GAGAL mengganti exe (folder tidak bisa ditulis?): ' + $_.Exception.Message)
    return $false
  }
  try {
    Move-Item -LiteralPath $new -Destination $Launcher -ErrorAction Stop
  } catch {
    Rename-Item -LiteralPath $old -NewName (Split-Path $Launcher -Leaf) -ErrorAction SilentlyContinue
    Write-Host ('GAGAL memasang exe baru: ' + $_.Exception.Message)
    return $false
  }
  $script:NewVer['launcher'] = $tag
  Write-Host ('IrisLauncher.exe sekarang versi ' + $tag + '. Mulai ulang launcher untuk memakainya (exe lama: ' + (Split-Path $old -Leaf) + ', dihapus otomatis).')
  return $true
}

function Rollback-Voice {
  if (-not $Proyek) { Write-Host 'GAGAL: folder proyek belum diatur.'; return $false }
  $baks = @(Get-ChildItem -LiteralPath $Proyek -Directory -Filter 'vv-engine.bak-*' -ErrorAction SilentlyContinue | Sort-Object Name -Descending)
  if ($baks.Count -eq 0) { Write-Host 'GAGAL: tidak ada folder cadangan vv-engine.bak-* di folder proyek.'; return $false }
  $bak = $baks[0]
  $cur = Join-Path $Proyek 'vv-engine'
  $was = ((Get-HttpCode $VvUrl) -gt 0)
  Write-Host ('Memulihkan VOICEVOX dari ' + $bak.Name + ' ...')
  [void](Svc 'voicevox' 'mati')
  $tmpName = 'vv-engine.dibuang-' + (Get-Date -Format 'yyyyMMdd-HHmmss')
  $ok = $false
  try {
    if (Test-Path -LiteralPath $cur) { Rename-Item -LiteralPath $cur -NewName $tmpName -ErrorAction Stop }
    try {
      Rename-Item -LiteralPath $bak.FullName -NewName 'vv-engine' -ErrorAction Stop
      $ok = $true
    } catch {
      Write-Host ('GAGAL memulihkan: ' + $_.Exception.Message)
      if (Test-Path -LiteralPath (Join-Path $Proyek $tmpName)) { Rename-Item -LiteralPath (Join-Path $Proyek $tmpName) -NewName 'vv-engine' -ErrorAction SilentlyContinue }
    }
  } catch {
    Write-Host ('GAGAL mengganti nama folder aktif (masih dipakai proses lain?): ' + $_.Exception.Message)
  }
  if ($ok) {
    Remove-Item -LiteralPath (Join-Path $Proyek $tmpName) -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host ('VOICEVOX dipulihkan ke versi ' + $(if (Get-VvVersion) { Get-VvVersion } else { 'sebelumnya' }) + '.')
  }
  if ($was) { [void](Svc 'voicevox' 'nyala') }
  return $ok
}

function Update-Wsl {
  $wasR = ((Get-HttpCode $UrlRouter) -gt 0)
  $wasH = ((Get-HttpCode $UrlHermes) -gt 0)
  $vvWin = ($Proyek -and (Test-Path -LiteralPath (Join-Path $Proyek 'vv-engine\run.exe')))
  $wasV = ((-not $vvWin) -and ((Get-HttpCode $VvUrl) -gt 0))
  $wasW = Test-WslJalan
  if ($wasW) {
    Write-Host 'Mematikan layanan WSL dan WSL-nya (wsl --update butuh WSL berhenti)...'
    [void](Svc 'wsl' 'mati')
  }
  Write-Host 'Menjalankan wsl --update ...'
  $out = ((& wsl.exe --update 2>&1) | Out-String) -replace "`0", ''
  $ok = ($LASTEXITCODE -eq 0)
  foreach ($l in ($out -split "`r?`n")) { if ($l.Trim().Length -gt 0) { Write-Host ('   ' + (Strip-Ansi $l)) } }
  if (-not $ok) {
    Write-Host 'Mencoba wsl --update --web-download ...'
    $out = ((& wsl.exe --update --web-download 2>&1) | Out-String) -replace "`0", ''
    $ok = ($LASTEXITCODE -eq 0)
    foreach ($l in ($out -split "`r?`n")) { if ($l.Trim().Length -gt 0) { Write-Host ('   ' + (Strip-Ansi $l)) } }
  }
  if ($wasW) {
    Write-Host 'Menyalakan WSL lagi...'
    [void](Svc 'wsl' 'nyala')
    if ($wasR) { [void](Svc 'router' 'nyala') }
    if ($wasH) { [void](Svc 'hermes' 'nyala') }
    if ($wasV) { [void](Svc 'voicevox' 'nyala') }
  }
  if ($ok) { Write-Host 'WSL ter-update.' } else { Write-Host 'GAGAL: wsl --update tidak berhasil (kalau minta izin administrator, jalankan sekali dari PowerShell admin: wsl --update).' }
  return $ok
}

# ------------------------------------------------------------ utama
$pilih = @()
if ($Nama -eq 'semua') { $pilih = $Semua }
else {
  foreach ($x in ($Nama -split '[,;]')) {
    $k = $x.Trim().ToLower()
    if ($Semua -contains $k) { $pilih += $k }
  }
}
if ($pilih.Count -eq 0) { Write-Host 'Tidak ada komponen yang dipilih.'; exit 1 }

# Cek banyak komponen sekaligus: tiap komponen dijalankan di proses PowerShell sendiri (paralel), hasil dicetak berurutan.
function Check-Parallel {
  $procs = @{}
  foreach ($k in $pilih) {
    $a = ('-NoProfile -ExecutionPolicy Bypass -File "{0}" -Aksi cek -Nama {1} -Distro {2} -TungguDetik {3} -Diam -Seri' -f $PSCommandPath, $k, $Distro, $TungguDetik)
    if ($Proyek) { $a += (' -Proyek "' + $Proyek + '"') }
    if ($TanpaGPU) { $a += ' -TanpaGPU' }
    if ($Launcher) { $a += (' -Launcher "' + $Launcher + '" -LauncherVersion "' + $LauncherVersion + '"') }
    if ($LauncherRepo) { $a += (' -LauncherRepo "' + $LauncherRepo + '"') }
    try {
      $psi = New-Object System.Diagnostics.ProcessStartInfo
      $psi.FileName = 'powershell.exe'
      $psi.Arguments = $a
      $psi.UseShellExecute = $false
      $psi.CreateNoWindow = $true
      $psi.RedirectStandardOutput = $true
      $psi.StandardOutputEncoding = [System.Text.Encoding]::UTF8
      $p = [System.Diagnostics.Process]::Start($psi)
      $procs[$k] = @{ P = $p; T = $p.StandardOutput.ReadToEndAsync() }
    } catch {
      $procs[$k] = $null
    }
  }
  $batas = (Get-Date).AddSeconds(300)
  foreach ($k in $pilih) {
    $e = $procs[$k]
    $dapat = $false
    if ($e) {
      $sisa = [int](($batas - (Get-Date)).TotalMilliseconds)
      if ($sisa -lt 1000) { $sisa = 1000 }
      if ($e.T.Wait($sisa)) {
        foreach ($ln in ($e.T.Result -split "`r?`n")) {
          if ($ln.StartsWith('@@UPD|')) { Write-Host $ln; $dapat = $true }
        }
      } else {
        try { $e.P.Kill() } catch { }
      }
    }
    if (-not $dapat) { Emit $k '' '' 'galat' 'Pemeriksaan tidak selesai atau tidak memberi hasil' }
  }
}

if ($Aksi -eq 'pulihkan') {
  if ($pilih.Count -eq 1 -and $pilih[0] -eq 'server') {
    $oks = $false
    try { $oks = Rollback-Server } catch { Write-Host ('GAGAL: ' + $_.Exception.Message) }
    $hs2 = 'GAGAL'
    if ($oks -eq $true) { $hs2 = 'OK (pemulihan)' }
    Hist 'server' '' '' $hs2
    if ($oks -eq $true) { exit 0 }
    exit 1
  }
  $v0 = Get-VvVersion
  $okp = $false
  try { $okp = Rollback-Voice } catch { Write-Host ('GAGAL: ' + $_.Exception.Message) }
  $hs = 'GAGAL'
  if ($okp -eq $true) { $hs = 'OK (pemulihan)' }
  Hist 'voicevox' $v0 (Get-VvVersion) $hs
  if ($okp -eq $true) { exit 0 }
  exit 1
}

if ($Aksi -eq 'cek') {
  if ($pilih.Count -gt 1 -and -not $Seri) {
    Say 'Memeriksa semua komponen secara paralel ...'
    Check-Parallel
    exit 0
  }
  foreach ($k in $pilih) {
    Say ('Memeriksa ' + $k + ' ...')
    try {
      switch ($k) {
        'wsl'      { Check-Wsl }
        'voicevox' { Check-Voice }
        'router'   { Check-Router }
        'hermes'   { Check-Hermes }
        'server'   { Check-Server }
        'overlay'  { Check-Overlay }
        'apt'      { Check-Apt }
        'launcher' { Check-Launcher }
      }
    } catch {
      Emit $k '' '' 'galat' $_.Exception.Message
    }
  }
  exit 0
}

# update: urutan tetap, WSL paling akhir (karena mematikan semua layanan di dalamnya)
$urut = @($Semua | Where-Object { $pilih -contains $_ })
$berhasil = @()
$gagal = @()
foreach ($k in $urut) {
  Write-Host ''
  Write-Host ('--- Update ' + $k + ' ---')
  $ok = $false
  $v0 = Get-Ver $k
  try {
    switch ($k) {
      'voicevox' { $ok = Update-Voice }
      'router'   { $ok = Update-Router }
      'hermes'   { $ok = Update-Hermes }
      'server'   { $ok = Update-Server }
      'overlay'  { $ok = Update-Overlay }
      'apt'      { $ok = Update-Apt }
      'launcher' { $ok = Update-Launcher }
      'wsl'      { $ok = Update-Wsl }
    }
  } catch {
    Write-Host ('GAGAL: ' + $_.Exception.Message)
    $ok = $false
  }
  $v1 = ''
  if ($script:NewVer.ContainsKey($k)) { $v1 = [string]$script:NewVer[$k] } else { $v1 = Get-Ver $k }
  if ($ok -eq $true) { $berhasil += $k; Hist $k $v0 $v1 'OK' } else { $gagal += $k; Hist $k $v0 $v1 'GAGAL' }
}
Write-Host ''
if ($berhasil.Count -gt 0) { Write-Host ('Berhasil: ' + ($berhasil -join ', ')) }
if ($gagal.Count -gt 0) { Write-Host ('GAGAL: ' + ($gagal -join ', ')); exit 1 }
Write-Host 'Selesai: semua update terpasang.'
exit 0
