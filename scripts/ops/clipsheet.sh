#!/bin/bash
# clipsheet.sh OUT.jpg CLIP... : 4 frames per clip (0%, 33%, 66%, 98%), one row per clip
out=$1; shift; tmp=$(mktemp -d); r=0
for c in "$@"; do d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$c"); i=0
  for f in 0.02 0.33 0.66 0.97; do t=$(python3 -c "print($d*$f)"); ffmpeg -v error -y -ss $t -i "$c" -frames:v 1 -vf "scale=200:-1" $tmp/r${r}_$i.png; i=$((i+1)); done
  ffmpeg -v error -y -i $tmp/r${r}_0.png -i $tmp/r${r}_1.png -i $tmp/r${r}_2.png -i $tmp/r${r}_3.png -filter_complex "hstack=4,drawtext=text='$(basename $c .mp4)':x=4:y=4:fontsize=16:fontcolor=yellow:box=1:boxcolor=black" $tmp/row$(printf %02d $r).png; r=$((r+1)); done
ffmpeg -v error -y -pattern_type glob -i "$tmp/row*.png" -vf "tile=1x$r" -frames:v 1 "$out"; rm -rf $tmp
