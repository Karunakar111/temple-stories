# Setup notes — what was broken and how it was fixed

Machine: macOS 12.7.5 (Monterey), Intel x86_64, Node v24.19.0, npm 11.17.0.
Date of repair: 2026-11-22.

## 1. `npx remotion skills add` — "could not determine executable to run"

**Cause:** the project had never been installed. There was no `node_modules` and no
lockfile, so `npx` could not find a local `remotion` binary.

**Fix:** `npm install`. The command then worked and installed the official Remotion
agent skills into `.claude/skills/` and `.agents/skills/` (tracked by `skills-lock.json`).

## 2. `npm install three @react-three/fiber @remotion/three @types/three` — ERESOLVE

**Cause:** not a real version conflict. `@react-three/fiber@9.8.2` declares `expo`,
`expo-gl`, `expo-asset`, `expo-file-system` and `react-native` as **optional** peer
dependencies. With no lockfile and no installed tree, npm tried to resolve the whole
graph at once, followed the optional `expo` peer to `expo@58`, and that in turn wanted
`react-native@undefined`.

R3F 9.8.2's real requirements are satisfied by this project:

| peer      | required        | installed |
|-----------|-----------------|-----------|
| react     | `>=19 <19.4`    | 19.3.1    |
| react-dom | `>=19 <19.4`    | 19.3.1    |
| three     | `>=0.156`       | 0.187.0   |

**Fix:** install in stages against a resolved tree — `npm install` first, then
`three` + `@types/three`, then `@react-three/fiber` + `@remotion/three`.
No `--legacy-peer-deps` or `--force` was needed. No Expo or React Native package is
installed (`ls node_modules | grep -E '^expo|react-native'` returns nothing).

All `@remotion/*` packages are pinned to the exact same version, **4.0.545**.

## 3. Disk full (the hidden blocker)

The install failed partway with `ENOSPC` — the disk had **20 MB free**. Cleared the npm
cache and the Homebrew cache (both regenerable) to recover ~2.9 GB. See the warning in
README.md: video work needs much more headroom than this.

## 4. macOS 12 vs Remotion 4.0.545 (two separate blockers)

Remotion 4.0.545 officially requires **macOS 15 (Sequoia)**. Two of its bundled native
binaries link against symbols that do not exist on macOS 12:

| binary | missing symbol | effect |
|---|---|---|
| `chrome-headless-shell` | `_kVTCompressionPropertyKey_ReferenceBufferCount` (VideoToolbox) | browser cannot launch at all |
| `@remotion/compositor-darwin-x64` / `libavdevice.dylib` | `_AVCaptureDeviceTypeContinuityCamera` (AVFoundation) | frames render, muxing to MP4 crashes |

Upstream issue: https://github.com/remotion-dev/remotion/issues/7027

**Fix A — browser.** Use the installed Google Chrome (150.0.7871.129), which runs fine on
macOS 12. Configured in `remotion.config.ts` via `Config.setBrowserExecutable`, with a
`REMOTION_BROWSER_EXECUTABLE` env override. This is a deliberate exception to Remotion's
"always use the bundled browser" guidance, forced by the OS.

**Fix B — encoding.** Remotion's own FFmpeg cannot run here, so **`npx remotion render out.mp4`
does not work on this machine**. Instead:

1. Remotion renders an image **sequence** (this path never touches the broken binary),
2. the project's own static FFmpeg 6.1.1 (`ffmpeg-static`, a devDependency) muxes it to MP4.

That is what `scripts/render.mjs` does. Use `npm run render <CompositionId>` — not
`npx remotion render`.

Homebrew was not used for FFmpeg: Homebrew no longer ships bottles for macOS 12, so
`brew install ffmpeg` would build from source for hours. `ffmpeg-static` is pinned in the
lockfile, needs no admin rights, and changes nothing outside this folder.

### If you upgrade to macOS 15 later
Delete the `Config.setBrowserExecutable` block in `remotion.config.ts` and you can use
`npx remotion render` directly. `scripts/render.mjs` will keep working either way.

## Verification performed (2026-11-22)

1. **Studio opens** — `npm run studio` serves http://localhost:3000; the composition list,
   timeline and live 3D preview all load.
2. **Animated 3D composition displays** — `SetupCheck`: a lit, shadow-casting, rotating
   object with a frame-driven camera push-in, plus an HTML text layer over the canvas.
3. **3-second MP4 renders** — `npm run render SetupCheck`.
4. **The file plays** — `ffprobe`: h264, 1080x1920, 30/1 fps, 90 frames, 3.000 s, 0.23 MB,
   `yuv420p`, faststart. A full decode pass (`ffmpeg -f null -`) reported no errors, and
   frames 0 / 45 / 89 were extracted and visually inspected.

## Remotion licence

Remotion is source-available and needs a paid company licence for some organisations.
An individual creator qualifies for the **free licence**, so renders pass
`--license-key=free-license`; preview renders also pass `--is-production=false`.
If this channel is ever run by a company of 4+ people, read
https://www.remotion.dev/docs/license and buy a licence. **Karunakar should confirm
this applies to him.**
