#!/usr/bin/env bash
# Rebuild the voice-synced reel.
# Usage: ./build.sh <voice.mp3> [work_dir] [out_dir]
# Timeline is warped to the voiceover via warp.json (used by reel.html and sound.py).
set -euo pipefail
cd "$(dirname "$0")"
VOICE=$1; WORK=${2:-./_work}; OUT=${3:-./out}
F=$WORK/frames; mkdir -p "$F" "$OUT"
DUR=$(python3 -c "import json;print(json.load(open('warp.json'))['dur'])")
TOTAL=$(python3 -c "print(round($DUR*120))")
if [ "$(ls "$F"/*.jpg 2>/dev/null | wc -l)" -ne "$TOTAL" ]; then
  A=$((TOTAL/3)); B=$((2*TOTAL/3))
  node render.js "$F" 120 0 $A & node render.js "$F" 120 $A $B & node render.js "$F" 120 $B $TOTAL & wait
fi
python3 -I sound.py "$WORK/bed.wav"
python3 -I sound.py "$WORK/bedsfx.wav" --sfx-only
for k in bed bedsfx; do
  ffmpeg -y -loglevel error -i "$VOICE" -i "$WORK/$k.wav" -filter_complex \
    "[0:a]aresample=48000,pan=stereo|c0=c0|c1=c0,highpass=f=80,acompressor=threshold=-20dB:ratio=3:attack=5:release=120,loudnorm=I=-16:TP=-2,apad=whole_dur=$DUR,asplit=2[v][key];[1:a]volume=0.4[b];[b][key]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=300[bd];[v][bd]amix=inputs=2:duration=longest:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11,atrim=0:$DUR" \
    -ar 48000 "$WORK/final_$k.wav"
done
VF="tmix=frames=2:weights='1 1',select='not(mod(n\,2))',setpts=N/60/TB,format=yuv420p"
ffmpeg -y -loglevel error -framerate 120 -i "$F/f%05d.jpg" -i "$WORK/final_bed.wav" -vf "$VF" -r 60 -c:v libx264 -preset slow -crf 18 \
  -profile:v high -movflags +faststart -c:a aac -b:a 192k -t "$DUR" "$OUT/toi-reel-voice-music.mp4"
ffmpeg -y -loglevel error -framerate 120 -i "$F/f%05d.jpg" -i "$WORK/final_bedsfx.wav" -vf "$VF" -r 60 -c:v libx264 -preset slow -crf 18 \
  -profile:v high -movflags +faststart -c:a aac -b:a 192k -t "$DUR" "$OUT/toi-reel-voice-sfx.mp4"
echo done
