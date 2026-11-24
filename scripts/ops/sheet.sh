#!/bin/bash
# sheet.sh EP OUT.jpg BEAT... : contact sheet of an episode's downloaded stills (label = beat)
ep=$1; out=$2; shift 2; tmp=$(mktemp -d); i=0
for b in "$@"; do f=$(ls episodes/$ep/assets/*-$b-still.png 2>/dev/null | head -1); [ -z "$f" ] && continue
  ffmpeg -v error -y -i "$f" -vf "scale=240:-1,drawtext=text='$b':x=6:y=6:fontsize=22:fontcolor=yellow:box=1:boxcolor=black" $tmp/$(printf %02d $i).png; i=$((i+1)); done
ffmpeg -v error -y -pattern_type glob -i "$tmp/*.png" -vf "tile=${COLS:-5}x2:color=black" -frames:v 1 "$out"; rm -rf $tmp
