#!/usr/bin/env node
/**
 * Render pipeline for temple-stories.
 *
 * Why this exists: this machine runs macOS 12. Remotion 4.0.545's bundled
 * FFmpeg compositor requires macOS 15, so `remotion render out.mp4` cannot mux
 * a video here. Rendering an image *sequence* works fine (frames come straight
 * out of Chrome), so we do that and mux with the project's static FFmpeg.
 *
 * Usage:
 *   node scripts/render.mjs <CompositionId> [options]
 *
 * Options:
 *   --out <path>        Output file (default exports/<CompositionId>.mp4)
 *   --audio <path>      Audio file to mux in (e.g. audio/narration.wav)
 *   --preview           Half resolution, JPEG frames, faster + smaller
 *   --frames <a-b>      Only render this frame range (e.g. 0-29)
 *   --png               Lossless PNG frames (default is JPEG q100 — far smaller,
 *                       and visually identical once muxed to h264)
 *   --keep-frames       Do not delete the frame folder afterwards
 *   --crf <n>           x264 quality, lower = better (default 18, preview 24)
 *   --entry <file>      Remotion entry point (default: the project's src/index.ts)
 *   --props <file>      JSON input props passed to the composition
 *   --browser-executable <path>  Chrome/Chromium to render with
 *
 * Deterministic: every frame is a pure function of the frame number, so the
 * same composition always produces the same frames.
 */

import { spawnSync } from "node:child_process";
import { existsSync, mkdirSync, rmSync, readdirSync, statSync } from "node:fs";
import { resolve, dirname } from "node:path";
import ffmpegPath from "ffmpeg-static";
import ffprobeStatic from "ffprobe-static";

const argv = process.argv.slice(2);
const compositionId = argv.find((a) => !a.startsWith("--"));

if (!compositionId) {
  console.error("Usage: node scripts/render.mjs <CompositionId> [--out path] [--audio path] [--preview]");
  process.exit(1);
}

const flag = (name) => {
  const i = argv.indexOf(`--${name}`);
  if (i === -1) return undefined;
  const next = argv[i + 1];
  return next && !next.startsWith("--") ? next : true;
};

const isPreview = Boolean(flag("preview"));
// Frames are intermediate: the final mux is h264, which is lossy, so PNG's extra
// precision is largely discarded at the encode step anyway. Measured on this project
// at 1080x1920, projected to a 110s part (3300 frames):
//   PNG 281 MB | JPEG q100 254 MB | q95 156 MB | q90 124 MB | q85 107 MB
// q95 is the chosen default: ~45% of PNG's footprint with no visible penalty after
// h264. Pass --png for lossless intermediates (exporting stills, compositing
// elsewhere).
const usePng = Boolean(flag("png"));
const outPath = resolve(String(flag("out") ?? `exports/${compositionId}${isPreview ? "-preview" : ""}.mp4`));
const audioPath = flag("audio") ? resolve(String(flag("audio"))) : undefined;
const frameRange = flag("frames");
const keepFrames = Boolean(flag("keep-frames"));
const crf = String(flag("crf") ?? (isPreview ? 24 : 18));

const framesDir = resolve(`exports/_frames-${compositionId}${isPreview ? "-preview" : ""}`);
const imageFormat = usePng && !isPreview ? "png" : "jpeg";
const ext = imageFormat;

const run = (cmd, args, label) => {
  console.log(`\n▶ ${label}`);
  const res = spawnSync(cmd, args, { stdio: "inherit" });
  if (res.status !== 0) {
    console.error(`\n✗ ${label} failed (exit ${res.status})`);
    process.exit(res.status ?? 1);
  }
};

// 1. Frames
rmSync(framesDir, { recursive: true, force: true });
mkdirSync(framesDir, { recursive: true });

const entryPoint = typeof flag("entry") === "string" ? flag("entry") : undefined;
const propsFile = typeof flag("props") === "string" ? resolve(flag("props")) : undefined;
const browserExe = typeof flag("browser-executable") === "string" ? flag("browser-executable") : undefined;
const extraArgs = [
  ...(propsFile ? [`--props=${propsFile}`] : []),
  ...(browserExe ? [`--browser-executable=${browserExe}`] : []),
];

const renderArgs = [
  "remotion",
  "render",
  ...(entryPoint ? [entryPoint] : []),
  compositionId,
  framesDir,
  "--sequence",
  `--image-format=${imageFormat}`,
  `--image-sequence-pattern=frame-[frame].${ext}`,
  "--license-key=free-license",
  ...extraArgs,
];
if (isPreview) {
  renderArgs.push("--scale=0.5", "--jpeg-quality=90", "--is-production=false");
} else if (imageFormat === "jpeg") {
  renderArgs.push("--jpeg-quality=95");
}
if (typeof frameRange === "string") renderArgs.push(`--frames=${frameRange}`);

run("npx", renderArgs, `Rendering frames for "${compositionId}" (${imageFormat})`);

const frameFiles = readdirSync(framesDir).filter((f) => f.endsWith(`.${ext}`)).sort();
if (frameFiles.length === 0) {
  console.error("✗ No frames were produced.");
  process.exit(1);
}
// Remotion zero-pads [frame] to the digit width of the highest frame number
// (4 frames -> frame-0.png, 90 frames -> frame-00.png), so read the real width
// off disk rather than assuming it.
const padWidth = (frameFiles[0].match(/frame-(\d+)\./)?.[1] ?? "0").length;
const inputPattern = `${framesDir}/frame-%0${padWidth}d.${ext}`;
console.log(`  ${frameFiles.length} frames in ${framesDir} (pattern frame-%0${padWidth}d.${ext})`);

// 2. Read fps from the composition so the mux matches the timeline exactly.
const fpsOverride = flag("fps");
let fps;
if (typeof fpsOverride === "string") {
  fps = Number(fpsOverride);
} else {
  const compsRes = spawnSync("npx", ["remotion", "compositions", ...(entryPoint ? [entryPoint] : []), ...extraArgs], { encoding: "utf8" });
  const stripAnsi = (s) => s.replace(/\u001b\[[0-9;]*m/g, "");
  const compLine = stripAnsi(compsRes.stdout ?? "")
    .split("\n")
    .map((l) => l.trim())
    .find((l) => l.split(/\s+/)[0] === compositionId);
  fps = compLine ? Number(compLine.split(/\s+/)[1]) : NaN;
}
if (!Number.isFinite(fps) || fps <= 0) {
  // Guessing the fps would silently desync the narration, so stop instead.
  console.error(`\u2717 Could not determine fps for "${compositionId}". Pass --fps <n>.`);
  process.exit(1);
}
console.log(`  fps = ${fps}`);

// 3. Mux
mkdirSync(dirname(outPath), { recursive: true });

const ffArgs = [
  "-y",
  "-framerate", String(fps),
  "-start_number", "0",
  "-i", inputPattern,
];
if (audioPath) {
  if (!existsSync(audioPath)) {
    console.error(`✗ Audio file not found: ${audioPath}`);
    process.exit(1);
  }
  ffArgs.push("-i", audioPath);
}
ffArgs.push(
  "-c:v", "libx264",
  "-preset", isPreview ? "veryfast" : "slow",
  "-crf", crf,
  "-pix_fmt", "yuv420p",
  // yuv420p + even dimensions keep the file playable everywhere (QuickTime, phones).
  "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",
  "-movflags", "+faststart",
);
if (audioPath) {
  ffArgs.push("-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest");
}
ffArgs.push(outPath);

run(ffmpegPath, ffArgs, `Muxing to ${outPath}`);

// 4. Verify
const probe = spawnSync(
  ffprobeStatic.path,
  ["-v", "error", "-show_entries",
   "stream=codec_type,codec_name,width,height,r_frame_rate,nb_frames,sample_rate:format=duration,size,format_name",
   "-of", "default=noprint_wrappers=1", outPath],
  { encoding: "utf8" },
);
console.log("\n✓ Export complete");
console.log(`  ${outPath}  (${(statSync(outPath).size / 1e6).toFixed(2)} MB)`);
console.log(probe.stdout.trim().split("\n").map((l) => `  ${l}`).join("\n"));

if (!keepFrames) {
  rmSync(framesDir, { recursive: true, force: true });
  console.log(`  frame folder cleaned up (use --keep-frames to keep it)`);
}
