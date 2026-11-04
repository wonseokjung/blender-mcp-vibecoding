#!/bin/bash
# Daily autopilot (macOS / Linux): open the prebuilt villa, let todays_scene.py pick today's look, render, encode.
# Edit the three paths below once, then test it by hand:  bash autopilot/run_daily.sh
# CONNECT AI LAB
set -euo pipefail

PKG="$(cd "$(dirname "$0")/.." && pwd)"
BLENDER="${BLENDER:-/Applications/Blender.app/Contents/MacOS/Blender}"
SCENE="${SCENE:-$PKG/scenes/blend/golden-hour-villa.blend}"
OUT="${OUT:-$PKG/out}"
WATERMARK="${WATERMARK:-$PKG/docs/media/cal_watermark.png}"   # set WATERMARK= to skip
LOCK="${TMPDIR:-/tmp}/blender_mcp_vibecoding.lock"
DAY="$(date +%F)"

if [ -e "$LOCK" ]; then echo "GPU busy ($LOCK). Try again later."; exit 0; fi
echo "autopilot $$ $(date '+%F %T')" > "$LOCK"
trap 'rm -f "$LOCK"' EXIT

mkdir -p "$OUT/$DAY"
start=$(date +%s)
"$BLENDER" -b --disable-autoexec "$SCENE" -P "$PKG/autopilot/todays_scene.py" -- --out "$OUT" --date "$DAY" "$@" \
  > "$OUT/$DAY/blender.log" 2>&1
echo "render: $(( $(date +%s) - start )) s" | tee -a "$OUT/$DAY/blender.log"

if command -v ffmpeg >/dev/null 2>&1; then
  if [ -n "$WATERMARK" ] && [ -f "$WATERMARK" ]; then
    # brand corner mark: bottom-right, about 65 % opacity, 100 px tall
    ffmpeg -v error -y -framerate 24 -pattern_type glob -i "$OUT/$DAY/frames/f_*.png" -i "$WATERMARK" \
      -filter_complex "[1]scale=-1:100,format=rgba,colorchannelmixer=aa=0.65[w];[0][w]overlay=W-w-40:H-h-40" \
      -c:v libx264 -crf 18 -pix_fmt yuv420p "$OUT/$DAY/todays_scene_$DAY.mp4"
  else
    ffmpeg -v error -y -framerate 24 -pattern_type glob -i "$OUT/$DAY/frames/f_*.png" \
      -c:v libx264 -crf 18 -pix_fmt yuv420p "$OUT/$DAY/todays_scene_$DAY.mp4"
  fi
  echo "video: $OUT/$DAY/todays_scene_$DAY.mp4"
else
  echo "ffmpeg not found: frames are in $OUT/$DAY/frames"
fi
