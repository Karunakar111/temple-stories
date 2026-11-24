"""Narration check, sound bed, final mix and mix check. Standard library + FFmpeg only
(macOS 12's Python 3.8 has no numpy guarantee).

1. verify_stem: the take is checked BEFORE anything is mixed: decodes, sample rate, no clipping,
   loudness in a sane range, no long dropouts, head/tail silence, length plausible for the script.
2. bed: a soft tanpura-style drone in D with distant bells, synthesised by FFmpeg (aevalsrc).
   Zero credits, no samples, no licences.
3. mix: narration on top; the bed ducks under the voice (sidechain); loudness normalised for phones.
4. verify_mix: checked separately: integrated loudness, true peak, length against the picture,
   no clipping, and the narration still carries the mix (envelope correlation with the stem).
"""
import array
import json
import math
import re
import shutil
import subprocess
from pathlib import Path

TARGET_I, TARGET_TP = -14.0, -1.5
CPS = 14.68  # EP01's measured speaking rate, characters per second


def ff(name):
    exe = shutil.which(name)
    if exe:
        return exe
    root = Path(__file__).resolve().parent.parent / "node_modules"
    cands = [root / "ffmpeg-static" / "ffmpeg"] if name == "ffmpeg" else \
        [root / "ffprobe-static" / "bin" / "darwin" / "x64" / "ffprobe", root / "ffprobe-static" / "bin" / "linux" / "x64" / "ffprobe"]
    for c in cands:
        if c.exists():
            return str(c)
    return name


def probe(path):
    r = subprocess.run([ff("ffprobe"), "-v", "error", "-show_entries", "stream=codec_type,codec_name,sample_rate,channels,width,height:format=duration:format_tags=comment",
                        "-of", "json", str(path)], capture_output=True, text=True)
    return json.loads(r.stdout or "{}")


def duration(path):
    return float(probe(path).get("format", {}).get("duration") or 0)


def loudness(path):
    """Integrated loudness (LUFS) and true peak (dBTP) via ebur128."""
    r = subprocess.run([ff("ffmpeg"), "-hide_banner", "-nostats", "-i", str(path), "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True)
    tail = r.stderr[r.stderr.rfind("Summary:"):]
    i = re.search(r"I:\s+(-?[\d.]+|-inf) LUFS", tail)
    tp = re.search(r"Peak:\s+(-?[\d.]+|-inf) dBFS", tail)
    f = lambda m: float(m.group(1)) if m and m.group(1) != "-inf" else -99.0
    return f(i), f(tp)


def silences(path, noise="-40dB", d=0.6):
    r = subprocess.run([ff("ffmpeg"), "-hide_banner", "-nostats", "-i", str(path), "-af", f"silencedetect=noise={noise}:d={d}", "-f", "null", "-"],
                       capture_output=True, text=True)
    starts = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", r.stderr)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", r.stderr)]
    total = duration(path)
    if len(ends) < len(starts):
        ends.append(total)
    return list(zip(starts, ends)), total


def clipped_samples(path):
    """Samples at or above full scale, counted on the decoded 16-bit signal."""
    x = _pcm(path, 48000, 1)
    return sum(1 for v in x if v >= 32767 or v <= -32768), len(x)


def _pcm(path, rate, seconds=None):
    cmd = [ff("ffmpeg"), "-v", "error", "-i", str(path)]
    if seconds:
        cmd += ["-t", f"{seconds:.3f}"]
    cmd += ["-ac", "1", "-ar", str(rate), "-f", "s16le", "-"]
    a = array.array("h")
    a.frombytes(subprocess.run(cmd, capture_output=True).stdout)
    return a


def envelope(path, seconds, rate=2000, hop=0.02):
    x = _pcm(path, rate, seconds)
    n = int(rate * hop)
    return [math.sqrt(sum(v * v for v in x[k:k + n]) / n) for k in range(0, len(x) - n + 1, n)]


def correlation(a, b, max_lag=10):
    """Pearson correlation of two envelopes and the best lag (in hops) within +-max_lag."""
    m = min(len(a), len(b))
    a, b = a[:m], b[:m]
    if m < 20:
        return 0.0, 0

    def corr(x, y):
        n = len(x)
        mx, my = sum(x) / n, sum(y) / n
        sxy = sum((p - mx) * (q - my) for p, q in zip(x, y))
        sx = math.sqrt(sum((p - mx) ** 2 for p in x))
        sy = math.sqrt(sum((q - my) ** 2 for q in y))
        return sxy / (sx * sy) if sx and sy else 0.0

    best, lag = -2.0, 0
    for L in range(-max_lag, max_lag + 1):
        x, y = (a[L:], b[:m - L]) if L >= 0 else (a[:m + L], b[-L:])
        c = corr(x, y)
        if c > best:
            best, lag = c, L
    return best, lag


# ---------------------------------------------------------------------------------- 1. stem
def verify_stem(path, script_text=None):
    checks, problems = {}, []
    info = probe(path)
    a = [s for s in info.get("streams", []) if s.get("codec_type") == "audio"]
    if not a:
        return {"audio": False}, ["narration has no audio stream"]
    sr = int(a[0].get("sample_rate") or 0)
    dur = float(info.get("format", {}).get("duration") or 0)
    dec = subprocess.run([ff("ffmpeg"), "-v", "error", "-xerror", "-i", str(path), "-f", "null", "-"], capture_output=True, text=True)
    i, tp = loudness(path)
    sil, _ = silences(path, "-45dB", 0.6)
    head = sil[0][1] if sil and sil[0][0] <= 0.05 else 0.0
    tail = dur - sil[-1][0] if sil and sil[-1][1] >= dur - 0.05 else 0.0
    inner = max([e - s for s, e in sil if s > 0.05 and e < dur - 0.05] or [0.0])
    clip, n = clipped_samples(path)
    checks.update(duration_s=round(dur, 2), sample_rate=sr, loudness_lufs=i, true_peak_dbtp=tp, head_silence_s=round(head, 2),
                  tail_silence_s=round(tail, 2), longest_pause_s=round(inner, 2), clipped_samples=clip, decode_clean=dec.returncode == 0 and not dec.stderr.strip())
    if not checks["decode_clean"]:
        problems.append("narration does not decode cleanly")
    if sr < 22050:
        problems.append(f"sample rate {sr} Hz is too low")
    if clip > n * 0.0001:
        problems.append(f"{clip} clipped samples")
    if not (-30.0 <= i <= -8.0):
        problems.append(f"loudness {i} LUFS outside -30..-8")
    if head > 1.5 or tail > 2.5:
        problems.append(f"head {head:.2f} s / tail {tail:.2f} s silence too long")
    if inner > 2.5:
        problems.append(f"a {inner:.2f} s dropout inside the take")
    if script_text:
        expect = len(script_text.replace("\n\n", "")) / CPS
        checks["expected_s"] = round(expect, 1)
        if not (0.7 * expect <= dur <= 1.4 * expect):
            problems.append(f"length {dur:.1f} s implausible for the script (~{expect:.0f} s)")
    return checks, problems


# ---------------------------------------------------------------------------------- 2. bed
def make_bed(path, seconds, seed=0):
    """Tanpura-style drone (Pa Sa' Sa' Sa, 0.62 s plucks in D), a low sustained Sa, soft air, a distant bell."""
    D = 146.83
    cyc = f"if(lt(mod(t,2.48),0.62),{D * 1.5:.2f},if(lt(mod(t,2.48),1.86),{D * 2:.2f},{D:.2f}))"
    pl = "exp(-3.2*mod(t,0.62))*min(1,mod(t,0.62)/0.01)"
    tanpura = f"0.10*{pl}*(sin(2*PI*({cyc})*t)+0.55*sin(4*PI*({cyc})*t)+0.35*sin(6*PI*({cyc})*t)+0.2*sin(8*PI*({cyc})*t))"
    low = f"0.045*sin(2*PI*{D / 2:.2f}*t)*(0.8+0.2*sin(2*PI*0.11*t))"
    period = 9.3 + (seed % 7) * 0.4
    bell = f"0.035*exp(-1.4*mod(t+{seed % 5},{period:.2f}))*(sin(2*PI*880*t)+0.5*sin(2*PI*1760*t)+0.3*sin(2*PI*2429*t))"
    expr = f"{tanpura}+{low}+{bell}"
    fade_out = max(0.0, seconds - 2.5)
    subprocess.run([ff("ffmpeg"), "-v", "error", "-y",
                    "-f", "lavfi", "-i", f"aevalsrc='{expr}':s=48000:d={seconds:.3f}",
                    "-f", "lavfi", "-i", f"anoisesrc=color=pink:amplitude=0.012:d={seconds:.3f}:r=48000:seed={seed}",
                    "-filter_complex", f"[1:a]lowpass=f=900[air];[0:a][air]amix=inputs=2:normalize=0,afade=t=in:d=1.2,afade=t=out:st={fade_out:.2f}:d=2.5,"
                                       "aformat=channel_layouts=stereo",
                    "-ar", "48000", str(path)], check=True)
    return path


# ---------------------------------------------------------------------------------- 3. mix
def mix(narration, bed, out, seconds, narration_start=0.0):
    """Two-pass: build the ducked pre-mix, measure it, then normalise linearly to -14 LUFS / -1.5 dBTP."""
    out = Path(out)
    pre = out.with_suffix(".premix.wav")
    fc = (f"[0:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(narration_start * 1000)}|{int(narration_start * 1000)},"
          f"apad=whole_dur={seconds:.3f},asplit=2[nar][key];"
          "[1:a]volume=0.42[bed];"
          "[bed][key]sidechaincompress=threshold=0.02:ratio=9:attack=8:release=300[duck];"
          f"[nar][duck]amix=inputs=2:normalize=0:duration=first,atrim=duration={seconds:.3f}[out]")
    subprocess.run([ff("ffmpeg"), "-v", "error", "-y", "-i", str(narration), "-i", str(bed), "-filter_complex", fc,
                    "-map", "[out]", "-ar", "48000", "-ac", "2", "-c:a", "pcm_s24le", str(pre)], check=True)
    r = subprocess.run([ff("ffmpeg"), "-hide_banner", "-nostats", "-i", str(pre), "-af",
                        f"loudnorm=I={TARGET_I}:TP={TARGET_TP}:LRA=11:print_format=json", "-f", "null", "-"], capture_output=True, text=True)
    m = json.loads(r.stderr[r.stderr.rfind("{"):r.stderr.rfind("}") + 1])
    ln = (f"loudnorm=I={TARGET_I}:TP={TARGET_TP}:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    subprocess.run([ff("ffmpeg"), "-v", "error", "-y", "-i", str(pre), "-af", ln + ",aresample=48000", "-ar", "48000", "-ac", "2", str(out)], check=True)
    pre.unlink()
    return out


# ---------------------------------------------------------------------------------- 4. mix check
def verify_mix(mix_path, narration, picture_s, narration_start=0.0):
    checks, problems = {}, []
    dur = duration(mix_path)
    i, tp = loudness(mix_path)
    clip, n = clipped_samples(mix_path)
    take = duration(narration)
    span = min(take, dur - narration_start)
    e_mix = envelope(mix_path, narration_start + span)[int(narration_start / 0.02):]
    e_nar = envelope(narration, span)
    c, lag = correlation(e_nar, e_mix)
    checks.update(duration_s=round(dur, 2), picture_s=round(picture_s, 2), loudness_lufs=i, true_peak_dbtp=tp,
                  clipped_samples=clip, narration_corr=round(c, 3), narration_lag_ms=lag * 20)
    if abs(dur - picture_s) > 0.1:
        problems.append(f"mix {dur:.2f} s vs picture {picture_s:.2f} s")
    if abs(i - TARGET_I) > 1.0:
        problems.append(f"loudness {i} LUFS (target {TARGET_I} +-1)")
    if tp > -1.0:
        problems.append(f"true peak {tp} dBTP above -1.0")
    if clip > n * 0.0001:
        problems.append(f"{clip} clipped samples")
    if c < 0.6:
        problems.append(f"narration does not carry the mix (correlation {c:.2f} < 0.60)")
    if abs(lag) > 3:
        problems.append(f"narration shifted by {lag * 20} ms in the mix")
    return checks, problems
