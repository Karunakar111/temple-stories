# EP02 Kolanupaka: live run plan (prepared 24 Nov 2026, not started)

Quote: **69 Higgsfield credits, 1,430 ElevenLabs credits** (22 paid calls: 15 stills, 6 clips, 1 narration take).
Nothing runs until Karunakar confirms the ElevenLabs balance and approves.

## Approval covers
- Script `episodes/ep02-kolanupaka/voice.te.txt` (sha pinned at approval), shot list revision 3, reference board.
- Caps: Higgsfield 69, ElevenLabs 1,430 (episode, daily and monthly caps all set to these for this run).
- The Kolanupaka exterior reference (K-EXTERIOR) for S17 and S16a: the photo Karunakar picks, imported to Higgsfield at no cost.
  Without it, those two shots wait and the film cannot finish.

## Steps
1. Mac online in the Claude desktop app. `npx -y @elevenlabs/cli@latest onboard check` confirms the key without printing it.
2. `python3 -m gudi balance record elevenlabs <credits> --source "subscription page"`.
3. `python3 -m gudi approve ep02-kolanupaka --by Karunakar --cap higgsfield=69 --cap elevenlabs=1430 --i-have-reviewed`.
4. Runner, attended: `GUDI_PROVIDER=operator python3 -m gudi run --episode ep02-kolanupaka --live`.
   - Reserves each call first, then writes the exact payload to `state/operator/outbox/`.
   - Narration: `python3 -m gudi.paid.tts_once episodes/ep02-kolanupaka/voice.te.txt <take.mp3>` on the Mac
     (one take, with character timestamps), staged back and recorded.
   - Stills and clips: submitted from the Claude session with the Higgsfield connector, exactly as written
     (media ids already resolved), then recorded with `gudi operator submitted|done`.
   - No automatic retries. A miss is reported and stops that shot.
5. `python3 -m gudi film ep02-kolanupaka` builds the phone-ready cut on the assembly path: narration check,
   picture, phrase captions, typeset cards, sound bed, mix check, MP4 + SRT + cover, final check.
6. Watch-through of S09 to S12 (water hand-over, the feet washing, the teaching) before the cut is handed over.

## Proven at zero spend
- `python3 -m gudi.operator_rehearsal`: the same runner, ledger and operator path with stand-in media; 22 requests,
  every reference sent as an id (CS-RENUKA and CS-AGASTYA feed S09-S11; S09's still starts its clip), film READY.
- `python3 scripts/plan/ep01_pipeline_test.py`: EP01 footage through the same film builder.
