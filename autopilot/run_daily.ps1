# Daily autopilot (Windows PowerShell): open the prebuilt villa, let todays_scene.py pick today's look, render, encode.
# Edit the paths below once, then test it by hand:  powershell -ExecutionPolicy Bypass -File autopilot\run_daily.ps1
# CONNECT AI LAB
$ErrorActionPreference = "Stop"
$Pkg      = Split-Path -Parent $PSScriptRoot
$Blender  = if ($env:BLENDER) { $env:BLENDER } else { "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" }
$Scene    = Join-Path $Pkg "scenes\blend\golden-hour-villa.blend"
$Out      = Join-Path $Pkg "out"
$Mark     = Join-Path $Pkg "docs\media\cal_watermark.png"
$Lock     = Join-Path $env:TEMP "blender_mcp_vibecoding.lock"
$Day      = Get-Date -Format "yyyy-MM-dd"

if (Test-Path $Lock) { Write-Host "GPU busy ($Lock). Try again later."; exit 0 }
"autopilot $PID $(Get-Date)" | Out-File $Lock
try {
  New-Item -ItemType Directory -Force -Path (Join-Path $Out $Day) | Out-Null
  $sw = [Diagnostics.Stopwatch]::StartNew()
  & $Blender -b --disable-autoexec $Scene -P (Join-Path $Pkg "autopilot\todays_scene.py") -- --out $Out --date $Day @args `
    *> (Join-Path $Out "$Day\blender.log")
  Write-Host ("render: {0:N0} s" -f $sw.Elapsed.TotalSeconds)
  if (Get-Command ffmpeg -ErrorAction SilentlyContinue) {
    $frames = Join-Path $Out "$Day\frames\f_%04d.png"
    $mp4 = Join-Path $Out "$Day\todays_scene_$Day.mp4"
    $first = (Get-Content (Join-Path $Out "$Day\params.json") | ConvertFrom-Json).frames[0]
    ffmpeg -v error -y -framerate 24 -start_number $first -i $frames -i $Mark `
      -filter_complex "[1]scale=-1:100,format=rgba,colorchannelmixer=aa=0.65[w];[0][w]overlay=W-w-40:H-h-40" `
      -c:v libx264 -crf 18 -pix_fmt yuv420p $mp4
    Write-Host "video: $mp4"
  } else { Write-Host "ffmpeg not found: frames are in $Out\$Day\frames" }
} finally { Remove-Item $Lock -ErrorAction SilentlyContinue }
