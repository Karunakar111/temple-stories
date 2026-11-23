import React from "react";
import { AbsoluteFill, Audio, Img, OffthreadVideo, Sequence, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { useTeluguFont } from "../experiments/exp01/components/Type";
import { clamp } from "../experiments/exp01/lib/motion";

/**
 * One episode's film, built by `gudi` from that episode's own downloaded assets and narration
 * (gudi/render.py writes the props). Pictures: the shot's still (slow push) or its clip; a
 * `cut` switches to a second picture inside the same spoken span. Captions follow the timing
 * derived from the narration take.
 */
type Pic = { kind: "image" | "video"; src: string };
export type FilmShot = { id: string; start: number; end: number; capEnd: number; text: string | null; pic: Pic; cut: { at: number; pic: Pic } | null };
export type FilmProps = {
  episode: string;
  title: string[];
  total_s: number;
  narration: string;
  music: string | null;
  label: string | null;
  shots: FilmShot[];
};

const F = "Exp01Telugu";
const GOLD = "#f6c454";
const CREAM = "#fff4dc";

const Picture: React.FC<{ pic: Pic; span: number }> = ({ pic, span }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = clamp(frame / fps / Math.max(span, 0.1), 0, 1);
  const style: React.CSSProperties = { width: "100%", height: "100%", objectFit: "cover" };
  if (pic.kind === "video") {
    return <OffthreadVideo src={staticFile(pic.src)} muted style={style} />;
  }
  return <Img src={staticFile(pic.src)} style={{ ...style, transform: `scale(${1.02 + 0.05 * p})` }} />;
};

const Caption: React.FC<{ text: string; dur: number }> = ({ text, dur }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const op = clamp(Math.min(t / 0.12, (dur - t) / 0.12), 0, 1);
  return (
    <div style={{ position: "absolute", left: 0, right: 0, top: 1450, display: "flex", justifyContent: "center", opacity: op }}>
      <div style={{ maxWidth: 940, padding: "14px 30px 20px", borderRadius: 22, background: "rgba(22,12,24,0.62)", fontFamily: F, fontWeight: 700, fontSize: 48, lineHeight: 1.35, textAlign: "center", color: CREAM }}>
        {text}
      </div>
    </div>
  );
};

export const EpisodeFilm: React.FC<FilmProps> = (p) => {
  useTeluguFont();
  const { fps } = useVideoConfig();
  return (
    <AbsoluteFill style={{ background: "#120a0e" }}>
      {p.shots.map((s, i) => {
        const from = Math.round(s.start * fps);
        const len = Math.max(1, Math.round((s.end - s.start) * fps));
        const cutAt = s.cut ? Math.min(len - 1, Math.round(s.cut.at * fps)) : len;
        return (
          <Sequence key={s.id} from={from} durationInFrames={len}>
            <Sequence durationInFrames={cutAt}>
              <Picture pic={s.pic} span={s.end - s.start} />
            </Sequence>
            {s.cut ? (
              <Sequence from={cutAt}>
                <Picture pic={s.cut.pic} span={s.end - s.start - s.cut.at} />
              </Sequence>
            ) : null}
            {s.text && !(i === 0 && p.title.length) ? (
              <Sequence durationInFrames={Math.max(1, Math.round((s.capEnd - s.start) * fps))}>
                <Caption text={s.text} dur={s.capEnd - s.start} />
              </Sequence>
            ) : null}
          </Sequence>
        );
      })}
      {p.title.length ? (
        <Sequence durationInFrames={Math.round((p.shots[0]?.end ?? 2) * fps)}>
          <div style={{ position: "absolute", left: 0, right: 0, top: 640, textAlign: "center", fontFamily: F, textShadow: "0 6px 30px rgba(0,0,0,0.85)" }}>
            <div style={{ fontSize: 96, fontWeight: 900, color: GOLD }}>{p.title[0]}</div>
            {p.title[1] ? <div style={{ fontSize: 110, fontWeight: 900, color: CREAM }}>{p.title[1]}</div> : null}
          </div>
        </Sequence>
      ) : null}
      {p.label ? (
        <div style={{ position: "absolute", left: 40, top: 40, padding: "8px 16px", borderRadius: 8, background: "#c2410c", color: "white", fontFamily: "sans-serif", fontSize: 28, fontWeight: 800 }}>
          {p.label}
        </div>
      ) : null}
      <Audio src={staticFile(p.narration)} volume={1} />
      {p.music ? <Audio src={staticFile(p.music)} volume={0.12} /> : null}
    </AbsoluteFill>
  );
};
