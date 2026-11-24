#!/bin/bash
# filmsheet.sh FILM.mp4 OUT.jpg : 12 frames evenly spaced, in order, with timestamps
f=$1; out=$2; tmp=$(mktemp -d); d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$f")
for i in $(seq 0 11); do t=$(python3 -c "print(round(0.3+($d-0.6)*$i/11,1))")
  ffmpeg -v error -y -ss $t -i "$f" -frames:v 1 -vf "scale=180:-1,drawtext=text='${t}s':x=4:y=4:fontsize=16:fontcolor=yellow:box=1:boxcolor=black" $tmp/$(printf %02d $i).png; done
ffmpeg -v error -y -pattern_type glob -i "$tmp/*.png" -vf tile=6x2 "$out"; rm -rf $tmp
