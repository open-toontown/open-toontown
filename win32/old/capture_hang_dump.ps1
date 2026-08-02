param(
  [int]$WaitSeconds = 60,
  [string]$DumpTag = "hang",
  [string]$ProcName = "ppython"
)

$ErrorActionPreference = "Stop"

function Find-GamePid {
  param([string]$Name)
  $ps = Get-Process -Name $Name -ErrorAction SilentlyContinue
  if (-not $ps) { return $null }

  # Prefer processes whose path is inside this repo (PPYTHON_PATH points at Panda3D\python\ppython.exe)
  $root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path.ToLowerInvariant()
  foreach ($p in $ps) {
    try {
      $path = ($p.Path).ToLowerInvariant()
      if ($path -and $path.StartsWith($root)) { return $p.Id }
    } catch { }
  }

  # Fallback: just take the newest one.
  return ($ps | Sort-Object StartTime -Descending | Select-Object -First 1).Id
}

$rootDir = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$procdump = Join-Path $rootDir "procdump.exe"
if (-not (Test-Path $procdump)) {
  throw "Missing procdump.exe at $procdump"
}

$targetPid = Find-GamePid -Name $ProcName
if (-not $targetPid) {
  Write-Host "No $ProcName process found. Start the game first (win32\capture_freeze.bat or win32\start_game.bat), then run this again."
  exit 2
}

$ts = Get-Date -Format "yyMMdd_HHmmss"
$dumpDir = Join-Path $rootDir "logs"
New-Item -ItemType Directory -Force -Path $dumpDir | Out-Null
$dumpPath = Join-Path $dumpDir ("{0}-{1}-{2}.dmp" -f $DumpTag, $ts, $targetPid)

Write-Host "Target PID: $targetPid"
Write-Host "Waiting $WaitSeconds seconds, then dumping -> $dumpPath"
Start-Sleep -Seconds $WaitSeconds

# -accepteula avoids interactive prompt
# -ma full dump
& $procdump -accepteula -ma $targetPid $dumpPath | Write-Host

Write-Host "Dump complete: $dumpPath"

