# Episode 1 (full): first cut report

**File:** `exports/komuravelli-ep01-full-firstcut.mp4`, 1080x1920, 30 fps, 1:48, AAC 192k, about -14 LUFS.
**Status:** first cut for review. Not published.

## Credits spent

| Item | Qty | Credits |
|---|---|---|
| Stills, `nano_banana_2` 2k | 15 | 30.0 |
| Clips, `kling3_0` pro, sound off | 15 clips, 59 s | 88.5 |
| **Total** | | **118.5** (cap 118.5) |

Balance 474.55 before, 356.05 after, checked against the account after each stage.
No retries, no model tests, no failed jobs.

## What was built

- 37 segments over the 42 planned beats (where one clip covers two beats, the action changes on the cut point).
- 15 new stills and clips in `assets/ep01-full/` and `exports/ep01-full/`; 12 existing clips reused.
- Code-drawn: map (Hyderabad to Komuravelli, 85 km counter), hill title, overhead patnam that fills colour by colour as each powder is named, festival date card, comment prompt, end card.
- Telugu captions in the script's spelling, names in turmeric gold, placed clear of the Reels/Shorts bottom UI. Lines already shown by a card are not duplicated as captions.
- Music and effects are synthesised in `scripts/ep01_full/audio.py`: a tanpura-style drone in D, a dolu-style drum and cymbals that change with each section (Oggu rhythm, sparse story pulse, fast chase, silence under the blow, festival rhythm), and effects at story moments. Music is sidechain-ducked under the narration, sitting 11 to 19 dB below the voice.
- Narration: the approved paced master, untouched. The picture is cut to its measured pauses, so sync is by construction.

## Fixes made without new generations

| Problem | Fix |
|---|---|
| Gangamma stills drew her **left** arm across and lost; narration says **right** | Mirrored both stills before animating |
| Kling made her swap to her left arm after 2.3 s | Used only the first 2.3 s, slowed to fill the beat with frame blending |
| Kling added a red, wound-like stump in the hand shot | Recoloured to water-white light in the render (`decolor`), no blood |
| Field still invented two glowing patnam squares floating in the powder | Softened into a plain powder cloud |
| Wedding still added a red-and-orange floor rangoli that reads like a patnam | Cropped out of the start frame |
| Dog still had a printed panel border | Cropped |
| Medalamma intro must not invent a first meeting | Mallanna alone holding a wedding garland, looking toward the village |
| Sleeping-snake clip (`a11-theft`) | Excluded; `a12-hishand` carries the theft |

## Remaining defects (material ones first)

1. **Captions and speech differ on some endings.** Captions keep the script's Telangana spelling (మార్చుకున్నడు, వేస్తరు); the voice says about 20 of these in standard form (మార్చుకున్నాడు, వేస్తారు). Choose: captions match the voice, or keep as is.
2. **Mallanna's dhoti colour changes:** red in the garland and Yellamma shots, blue in the wedding shot.
3. **The Oggu lead holds a cylindrical hand drum**, not the hourglass oggu.
4. **Gangamma's block is in slow motion** (0.47x). It reads as deliberate, but water and hair are a little soft.
5. **The hand shot's recoloured arm end** reads as light; a close viewer may see a glove-like white shape.
6. **Music is a synthesised placeholder**, functional and balanced but not a composed score.
7. ఎల్లమ్మ at 0:31 is quick in the narration (accepted earlier).

## Rebuild

```
python3 scripts/ep01_full/render.py   # picture, frame-exact from scripts/ep01_full/edl.py
python3 scripts/ep01_full/audio.py    # music, effects, mix
ffmpeg -i build/ep01-full/picture.mp4 -i build/ep01-full/mix.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest exports/komuravelli-ep01-full-firstcut.mp4
```
