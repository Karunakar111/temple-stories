#!/bin/sh
# Download ElevenLabs narration without a manual browser step.
#
# Usage:
#   sh scripts/fetch-narration.sh                 # list the 10 most recent items
#   sh scripts/fetch-narration.sh <id> <out.mp3>  # download one and verify it decodes
#
# Auth: the CLI reads ELEVENLABS_API_KEY from .env.local (gitignored). Never print it.
#
# NOTE: the Flows endpoint GET /v1/flows/text-to-speech/{generation_id} is NOT usable on
# this account — it returns 402 paid_plan_required ("requires a Pro plan or above").
# Speech History carries the same audio and works on the current Starter plan.
CLI="npx -y @elevenlabs/cli@latest"

if [ -z "$1" ]; then
  $CLI history list --page-size 10 --format json </dev/null
  exit 0
fi

ID="$1"; OUT="${2:-audio/$1.mp3}"
$CLI history get_audio --history-item-id "$ID" --format raw </dev/null > "$OUT" || exit 1
SZ=$(wc -c < "$OUT")
[ "$SZ" -lt 2000 ] && { echo "FAILED: $OUT is only $SZ bytes"; head -c 300 "$OUT"; exit 1; }
node_modules/ffprobe-static/bin/darwin/x64/ffprobe -v error \
  -show_entries format=duration -show_entries stream=codec_name,sample_rate -of default=nw=1 "$OUT" || exit 1
node_modules/ffmpeg-static/ffmpeg -v error -i "$OUT" -f null - >/dev/null 2>&1 \
  && echo "OK  $OUT  ($SZ bytes, decodes clean)" || { echo "FAILED: $OUT does not decode"; exit 1; }
