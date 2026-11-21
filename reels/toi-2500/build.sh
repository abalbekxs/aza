#!/usr/bin/env bash
# Rebuild the reel: frames (120 fps) -> 60 fps with 2-frame motion blur, + audio.
# Usage: ./build.sh <work_dir> <out_dir>
set -euo pipefail
cd "$(dirname "$0")"
WORK=${1:-./_work}; OUT=${2:-.}
F=$WORK/frames; mkdir -p "$F"
if [ "$(ls "$F"/*.jpg 2>/dev/null | wc -l)" -ne 3168 ]; then
  node render.js "$F" 120 0 1056 & node render.js "$F" 120 1056 2112 & node render.js "$F" 120 2112 3168 & wait
fi
python3 -I sound.py "$WORK/mix.wav"
python3 -I sound.py "$WORK/sfx.wav" --sfx-only
VF="tmix=frames=2:weights='1 1',select='not(mod(n\,2))',setpts=N/60/TB,format=yuv420p"
for kind in mix sfx; do
  name=$([ $kind = mix ] && echo "toi-reel-music" || echo "toi-reel-sfx-only")
  ffmpeg -y -loglevel error -framerate 120 -i "$F/f%05d.jpg" -i "$WORK/$kind.wav" \
    -vf "$VF" -r 60 -c:v libx264 -preset slow -crf 17 -profile:v high -movflags +faststart \
    -af "loudnorm=I=-14:TP=-1.5:LRA=11" -c:a aac -b:a 192k -ar 48000 \
    -t 26.4 "$OUT/$name.mp4"
done
ffmpeg -y -loglevel error -framerate 120 -i "$F/f%05d.jpg" -vf "$VF" -r 60 -c:v libx264 -preset slow -crf 17 \
  -profile:v high -movflags +faststart -an -t 26.4 "$OUT/toi-reel-silent.mp4"
echo done
