"""Film assembly (config/production.json "assembly"), the same on the Mac and in the cloud.

- Picture: every clip and still in ONE FFmpeg filter_complex pass. FFmpeg decodes the clips
  (trim, speed, 30 fps, scale/crop to the frame, clone the last frame if a clip is short);
  stills get a slow push. Nothing is extracted to a full-episode frame sequence, so the
  Remotion video-decoding limit on macOS 12 never comes into play.
- Text: Remotion renders only transparent PNGs, ONE per caption phrase or typeset card
  (Noto Sans Telugu shaped by Chrome), via `remotion render --sequence`. FFmpeg overlays each
  PNG for its own time window with short alpha fades. A 100 s film needs ~60 small PNGs.
- Sound: see gudi/audio_mix.py (stem check -> bed -> mix -> mix check).
- Outputs per film: <slug>.mp4 (H.264 + AAC, faststart, tagged), <slug>.te.srt, <slug>-cover.jpg.
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

from .audio_mix import ff

CODE = Path(__file__).resolve().parent.parent


def frames(t, fps):
    return int(round(t * fps))


def build_picture(segments, out, size, fps=30):
    W, H = size
    W2, H2 = (W * 3 // 2) // 2 * 2, (H * 3 // 2) // 2 * 2
    args, chains = [], []
    for i, s in enumerate(segments):
        n = s["frames"]
        dur = n / fps
        if s["kind"] == "clip":
            args += ["-ss", f"{s.get('ss', 0.0):.3f}", "-i", str(s["src"])]
            sp = s.get("speed", 1.0)
            lead = float(s.get("lead", 0.0))  # hold the first frame this long before the clip moves
            head = f"tpad=start_mode=clone:start_duration={lead:.3f}," if lead > 0 else ""
            fc = ""
            if s.get("focus"):  # a clip keeps the still's reframing: static crop at the "from" framing
                cx, cy, z = s["focus"]["from"]
                fc = (f"crop=iw/{z}:ih/{z}:'max(0,min(iw-iw/{z},iw*{cx}-iw/{z}/2))':"
                      f"'max(0,min(ih-ih/{z},ih*{cy}-ih/{z}/2))',")
            fc = ("hflip," if s.get("hflip") else "") + fc
            chains.append(f"[{i}:v]setpts=(PTS-STARTPTS)/{sp},fps={fps},{fc}scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,"
                          f"{head}tpad=stop_mode=clone:stop_duration={dur + 1:.3f},trim=end_frame={n},setpts=PTS-STARTPTS[v{i}]")
        else:
            args += ["-loop", "1", "-framerate", str(fps), "-t", f"{dur + 0.5:.3f}", "-i", str(s["src"])]
            if s.get("focus"):  # move from one framing to another: [cx, cy, zoom], cx/cy as fractions of the image
                (x0, y0, z0), (x1, y1, z1) = s["focus"]["from"], s["focus"]["to"]
                W3, H3 = W * 2, H * 2  # work at 2x so slow moves stay smooth
                m = max(n - 1, 1)
                zf = f"({z0}+({z1}-{z0})*on/{m})"
                xf = f"min(max(({x0}+({x1}-{x0})*on/{m})*iw-iw/zoom/2,0),iw-iw/zoom)"
                yf = f"min(max(({y0}+({y1}-{y0})*on/{m})*ih-ih/zoom/2,0),ih-ih/zoom)"
                chains.append(f"[{i}:v]scale={W3}:{H3}:force_original_aspect_ratio=increase,crop={W3}:{H3},"
                              f"zoompan=z='{zf}':x='{xf}':y='{yf}':d=1:s={W}x{H}:fps={fps},"
                              f"setsar=1,trim=end_frame={n},setpts=PTS-STARTPTS[v{i}]")
                continue
            z = s.get("push", 0.05)
            chains.append(f"[{i}:v]scale={W2}:{H2}:force_original_aspect_ratio=increase,crop={W2}:{H2},"
                          f"zoompan=z='1.0+{z}*on/{max(n, 1)}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={W}x{H}:fps={fps},"
                          f"setsar=1,trim=end_frame={n},setpts=PTS-STARTPTS[v{i}]")
    graph = ";".join(chains) + ";" + "".join(f"[v{i}]" for i in range(len(segments))) + f"concat=n={len(segments)}:v=1:a=0,format=yuv420p[vout]"
    gf = Path(str(out) + ".graph.txt")
    gf.write_text(graph)
    subprocess.run([ff("ffmpeg"), "-v", "error", "-y", *args, "-filter_complex_script", str(gf), "-map", "[vout]",
                    "-r", str(fps), "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p", str(out)], check=True)
    gf.unlink()
    return out


def _remotion(comp, out_dir, props, scale, frames_n):
    """Render `frames_n` single frames of a text-only composition as transparent PNGs."""
    props_f = Path(out_dir) / f"{comp}.props.json"
    props_f.write_text(json.dumps(props, ensure_ascii=False))
    cmd = ["npx", "remotion", "render", "src/preview/index.ts", comp, str(out_dir), "--sequence", "--image-format=png",
           f"--image-sequence-pattern={comp}-[frame].[ext]", f"--props={props_f}", f"--frames=0-{frames_n - 1}",
           f"--scale={scale}", "--license-key=free-license", "--log=error"]
    chrome = shutil.which("google-chrome")
    if chrome and sys.platform != "darwin":
        cmd.append(f"--browser-executable={chrome}")
    try:
        r = subprocess.run(cmd, cwd=str(CODE), capture_output=True, text=True, timeout=600)
    except subprocess.TimeoutExpired:
        free = shutil.disk_usage(str(out_dir)).free / 1e9
        raise RuntimeError(f"remotion text layers did not finish in 10 minutes ({free:.1f} GB free on disk)")
    if r.returncode != 0:
        raise RuntimeError("remotion: " + (r.stdout + r.stderr).strip()[-400:])
    pngs = sorted(Path(out_dir).glob(f"{comp}-*.png"))
    if len(pngs) != frames_n:
        raise RuntimeError(f"remotion wrote {len(pngs)} of {frames_n} {comp} frames")
    return pngs


def render_overlays(items, out_dir, scale):
    """items: [{kind, lines|text, start, end}] -> one transparent PNG each."""
    if not items:
        return []
    return _remotion("OverlayLayer", out_dir, {"items": [{k: v for k, v in it.items() if k not in ("start", "end")} for it in items]},
                     scale, len(items))


def render_cover(cover, out_jpg, work, scale=1.0):
    png = _remotion("Cover", work, cover, scale, 1)[0]
    subprocess.run([ff("ffmpeg"), "-v", "error", "-y", "-i", str(png), "-q:v", "2", str(out_jpg)], check=True)
    png.unlink()
    return out_jpg


def mux(picture, overlays, mix_wav, out, total_s, fps, tag):
    """Overlay each PNG for its window (alpha fades), add the mix, encode for phones."""
    args = ["-i", str(picture), "-i", str(mix_wav)]
    chains, last = [], "0:v"
    for k, (png, it) in enumerate(overlays):
        a, b = it["start"], it["end"]
        ln = max(0.2, b - a)
        args += ["-loop", "1", "-framerate", str(fps), "-t", f"{ln:.3f}", "-i", str(png)]
        idx = k + 2
        fin = "fade=t=in:st=0:d=0.12:alpha=1," if a > 0.01 else ""  # text on the first frame is fully visible on frame one
        chains.append(f"[{idx}:v]format=rgba,{fin}fade=t=out:st={max(0, ln - 0.12):.3f}:d=0.12:alpha=1,"
                      f"setpts=PTS-STARTPTS+{a:.3f}/TB[o{k}]")
        chains.append(f"[{last}][o{k}]overlay=0:0:eof_action=pass:repeatlast=0[b{k}]")
        last = f"b{k}"
    graph = ";".join(chains) if chains else "[0:v]null[b]"
    vlabel = f"[{last}]" if chains else "[b]"
    gf = Path(str(out) + ".graph.txt")
    gf.write_text(graph)
    subprocess.run([ff("ffmpeg"), "-v", "error", "-y", *args, "-filter_complex_script", str(gf), "-map", vlabel, "-map", "1:a",
                    "-t", f"{total_s:.3f}", "-r", str(fps), "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
                    "-profile:v", "high", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart",
                    "-metadata", f"comment={tag}", str(out)], check=True)
    gf.unlink()
    return out
