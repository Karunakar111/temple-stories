# Zero-spend payload test (24 Nov 2026)

Command: `python3 -m gudi.payload_test` builds the exact Higgsfield `params` for real EP02 calls through `gudi.media.resolve`, the same function the runner uses before it reserves anything.

- `STYLE-PATNAM` resolves to its board media id `85b1b66a-3daa-4ab7-86e0-68bd5da05c9c`. That Higgsfield media matches `assets/pilot/shot3-patnam-v3-final.png` pixel for pixel.
- Upstream stills that do not exist yet are stood in for by existing EP01 media in the account: `CS-RENUKA:still` -> `a729414b-aec4-4dbe-b8f7-c9dcd3e341ed` (EP01 n10-hand start frame); `S02:still` -> `b23194fa-59e6-4cb8-8a2d-e190d7774d5e` (EP01 n01-oggu start frame).
- Both resolved payloads were priced with Higgsfield's free estimate tools, which submit no job. The Higgsfield balance read 356.05 before and after.

| Call | Sent references | Result |
|---|---|---|
| S02:still | `a729414b` image_references, `85b1b66a` image_references | estimate_image_cost: 2 credits (exact), no job submitted |
| S02:clip | `b23194fa` start_image | estimate_video_cost: 6 credits (exact, 4 s pro, sound off), no job submitted |
| S17:still | STYLE-PATNAM only | HELD before reservation: K-EXTERIOR: no Higgsfield media id (needs photo) |

## Exact payloads

### S02:still
```json
{
 "model": "nano_banana_2",
 "prompt": "The same temple doorway of golden light; a Shaiva sage (as in reference image 1) standing in the glow, the worshippers' silhouettes leaning back in wonder, attached style. No deity figure, idol, murti or linga is visible; the sacred presence is carried only by light, lamps and the worshippers' reactions. All figures fully clothed in simple period dress. No text, letters or script anywhere in the image. The last reference image sets the illustration style only.",
 "resolution": "2k",
 "aspect_ratio": "9:16",
 "medias": [
  {
   "value": "a729414b-aec4-4dbe-b8f7-c9dcd3e341ed",
   "role": "image_references"
  },
  {
   "value": "85b1b66a-3daa-4ab7-86e0-68bd5da05c9c",
   "role": "image_references"
  }
 ]
}
```

### S02:clip
```json
{
 "model": "kling3_0",
 "prompt": "The golden light around the sage softens as he becomes solid and still; the worshippers lean back slightly. His face, ash marks and rudraksha stay exactly the same. Camera almost still.",
 "mode": "pro",
 "sound": "off",
 "aspect_ratio": "9:16",
 "duration": 4,
 "medias": [
  {
   "value": "b23194fa-59e6-4cb8-8a2d-e190d7774d5e",
   "role": "start_image"
  }
 ]
}
```

### S17:still (held)
```json
{
 "model": "nano_banana_2",
 "prompt": "Exterior of the Someshwara Shiva temple at Kolanupaka exactly as in reference image 1 (NOT the Jain temple), late afternoon, devotees at the entrance, attached style. All figures fully clothed in simple period dress. No text, letters or script anywhere in the image. The last reference image sets the illustration style only.",
 "resolution": "2k",
 "aspect_ratio": "9:16",
 "medias": [
  {
   "value": "85b1b66a-3daa-4ab7-86e0-68bd5da05c9c",
   "role": "image_references"
  }
 ]
}
```
