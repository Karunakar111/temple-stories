# Scheduling a Gudi Kathalu video in Zoho Social without anyone attaching files

Works from a cloud session with Claude in Chrome on Karunakar's Chrome (Zoho Social signed in). Proven on EP03, 25 Nov 2026.

Why: the Chrome upload tool takes at most 3.8 MB per call and connector uploads (Drive) refuse files in the 30 MB+ range, while a full-quality Short is 60 to 110 MB. Higgsfield media links are removed after confirmation, so they cannot host it.

1. Make the publish file: `ffmpeg -i <film>.mp4 -c:v libx264 -preset slow -crf 20 -maxrate 6M -bufsize 12M -pix_fmt yuv420p -c:a aac -b:a 160k -movflags +faststart pub.mp4` (about 60 MB for 88 s; visually the same as the review export). Note its sha256.
2. `split -b 3700000 -d -a 2 pub.mp4 part_`.
3. In the Zoho tab, add a hidden receiver input with JS (id `__chunkin`, multiple) whose change handler stores each file's ArrayBuffer in `window.__chunks[name]`. Find its ref and call file_upload once per part (and once for the cover JPG).
4. Rebuild in the page: `new Blob(sorted parts)`; check size and SHA-256 (crypto.subtle) against step 1. Keep as `window.__video`.
5. Patch `HTMLInputElement.prototype.click` so a file input's click is captured in `window.__fi` instead of opening the OS picker. Open New Post > media icon > Desktop, then set `__fi.files` from a DataTransfer holding `__video` and dispatch `change`. Wait for the upload, press Attach.
6. Thumbnail (Instagram): in "Choose a custom video thumbnail" press +, Desktop, same trick with the cover JPG, Attach.
7. Caption: click the editor, `document.execCommand('insertText', false, caption)`; compare innerText with the file (blank lines render as triple newlines).
8. YouTube icon: tick Post as Shorts, set Title and Description (form_input), Visibility Public; compare SHA-256 of both with youtube-description.txt; Update.
9. Instagram icon: Add to Instagram Feed on.
10. Schedule for a Specific Date: date, 06 : 00 PM, Time Zone IST; Schedule. Verify under Posts > Scheduled Posts, each channel tab.

## Bio link (from 25 Nov 2026)
Instagram bio link: https://gudikathalu.vercel.app/ (temple guides at /<temple>/, e.g. /vemulawada/).
- Instagram caption: one line before the comment question, "🛕 <guide label>: బయోలోని లింక్‌లో 🔗" (captions cannot hold clickable links). Without a guide page for the temple: "🛕 మరిన్ని గుడి కథలు, దర్శనం గైడ్‌లు: బయోలోని లింక్‌లో 🔗".
- YouTube description: the direct page URL under the 📍 location line.
- Zoho appends "#shorts" to Shorts descriptions, so the description file ends with a single "#shorts".
