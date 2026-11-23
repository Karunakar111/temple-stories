import React from "react";
import { AbsoluteFill, Audio, Img, Sequence, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { useTeluguFont } from "../experiments/exp01/components/Type";
import { Bloom, LampGlow } from "../experiments/exp01/components/effects";
import { clamp, ramp, sine } from "../experiments/exp01/lib/motion";

/**
 * Technical preview of an episode, built from shots.json (see scripts/plan/preview_props.py).
 * Shows real timing, real typesetting and real local light effects. Every picture is either an
 * EP01 painting standing in (TEMPORARY ART) or a plate drawn in code (PLACEHOLDER), and says so.
 */
export type PreviewShot = {
  id: string;
  start: number;
  dur: number;
  hold: number;
  text: string | null;
  picture: string;
  cls: string;
  clip_s: number | null;
  reuse: string | null;
  art: { kind: "temp" | "plate"; src: string; pos: string | null };
  type: { kind: string; lines: string[]; at?: number } | null;
  fx: string | null;
};
export type PreviewProps = {
  episode: string;
  revision: string;
  timing: string;
  total_s: number;
  music: string;
  shots: PreviewShot[];
};

const F = "Exp01Telugu";
const UI = "-apple-system, 'Segoe UI', Roboto, Helvetica, Arial, Exp01Telugu, sans-serif";
const GOLD = "#f6c454";
const CREAM = "#fff4dc";
const NAMES = ["కొలనుపాక", "సోమేశ్వర", "రేణుక", "అగస్త్య", "లోపాముద్ర", "శివ"];

/* ------------------------------------------------------------- pictures */

const LAMPS = [
  { x: 300, y: 1060, r: 70 },
  { x: 780, y: 1060, r: 70 },
  { x: 410, y: 900, r: 46 },
  { x: 670, y: 900, r: 46 },
];

const LampPlate: React.FC<{ frame: number; strength: number }> = ({ frame, strength }) => (
  <AbsoluteFill style={{ background: "radial-gradient(ellipse at 50% 52%, #4a2414 0%, #24110c 45%, #0d0607 80%)" }}>
    {/* a doorway of the sanctum, drawn flat; no deity or linga is drawn (see decision D1) */}
    <div style={{ position: "absolute", left: 250, top: 420, width: 580, height: 900, borderRadius: "290px 290px 0 0", border: "18px solid rgba(120,70,40,0.55)", boxShadow: "inset 0 0 120px rgba(0,0,0,0.8)" }} />
    <div style={{ position: "absolute", left: 210, top: 1300, width: 660, height: 40, background: "rgba(110,64,36,0.6)", borderRadius: 6 }} />
    {LAMPS.map((l, i) => (
      <div key={i} style={{ position: "absolute", left: l.x - 10, top: l.y - 4, width: 20, height: 26, borderRadius: "50% 50% 40% 40%", background: "#ffd27a", opacity: 0.95 }} />
    ))}
    <LampGlow lamps={LAMPS} frame={frame} strength={strength} />
  </AbsoluteFill>
);

const StonePlate: React.FC<{ t: number }> = ({ t }) => {
  const rows = Array.from({ length: 9 }, (_, i) => i);
  return (
    <AbsoluteFill style={{ background: "linear-gradient(115deg, #6b5a49 0%, #4a3d31 40%, #2c241d 100%)" }}>
      {rows.map((i) => (
        <div
          key={i}
          style={{
            position: "absolute",
            left: 140 + (i % 2) * 18,
            top: 520 + i * 92,
            width: 800 - (i % 3) * 40,
            height: 10,
            borderRadius: 5,
            background: "rgba(20,14,10,0.55)",
            boxShadow: "0 3px 0 rgba(255,225,180,0.18)",
          }}
        />
      ))}
      {/* raking light sweeps across the incised lines */}
      <div style={{ position: "absolute", inset: 0, background: `linear-gradient(100deg, rgba(255,200,120,0) ${-30 + t * 18}%, rgba(255,200,120,0.28) ${t * 18}%, rgba(255,200,120,0) ${30 + t * 18}%)`, mixBlendMode: "screen" }} />
    </AbsoluteFill>
  );
};

const TempArt: React.FC<{ src: string; pos: string | null; p: number }> = ({ src, pos, p }) => (
  <AbsoluteFill style={{ overflow: "hidden" }}>
    <Img
      src={staticFile(src)}
      style={{
        width: "100%",
        height: "100%",
        objectFit: "cover",
        objectPosition: pos ?? "50% 50%",
        transform: `scale(${1.02 + 0.05 * p})`,
        filter: "saturate(0.55) brightness(0.72) sepia(0.15)",
      }}
    />
  </AbsoluteFill>
);

/* ------------------------------------------------------------- labels */

const Label: React.FC<{ s: PreviewShot }> = ({ s }) => {
  const temp = s.art.kind === "temp";
  return (
    <div style={{ position: "absolute", left: 40, right: 40, top: 110, fontFamily: UI }}>
      <div
        style={{
          display: "inline-block",
          padding: "8px 16px",
          borderRadius: 8,
          background: temp ? "#c2410c" : "#6d28d9",
          color: "white",
          fontSize: 26,
          fontWeight: 800,
          letterSpacing: 1.5,
        }}
      >
        {temp ? "TEMPORARY ART · EP01 painting, not Kolanupaka" : "PLACEHOLDER · drawn in code"}
      </div>
      <div style={{ marginTop: 12, padding: "12px 16px", borderRadius: 10, background: "rgba(10,6,8,0.72)", color: "#f5e9d6", fontSize: 25, lineHeight: 1.35 }}>
        <b style={{ color: GOLD }}>{s.id}</b> · final picture: {s.picture}
        {s.reuse ? <div style={{ opacity: 0.8 }}>reuses the {s.reuse} still</div> : null}
        {s.clip_s ? (
          <div style={{ marginTop: 6, color: "#fcd34d", fontWeight: 700 }}>
            PAID CLIP {s.clip_s} s · generated after the narration take (on screen {s.dur.toFixed(2)} s)
          </div>
        ) : null}
      </div>
    </div>
  );
};

const Header: React.FC<{ p: PreviewProps }> = ({ p }) => (
  <div style={{ position: "absolute", left: 40, right: 40, top: 40, display: "flex", justifyContent: "space-between", fontFamily: UI, fontSize: 24, color: "rgba(255,244,220,0.85)", fontWeight: 700 }}>
    <span>{p.episode.toUpperCase()} · TECHNICAL PREVIEW</span>
    <span>timing: {p.timing}</span>
  </div>
);

/** Timeline strip: every shot, the current one lit, and each paid clip's length against its shot. */
const Strip: React.FC<{ p: PreviewProps; t: number }> = ({ p, t }) => {
  const W = 1000;
  const x = (s: number) => 40 + (s / p.total_s) * W;
  return (
    <div style={{ position: "absolute", left: 0, top: 1780, width: 1080, height: 110, fontFamily: UI }}>
      {p.shots.map((s) => {
        const on = t >= s.start && t < s.start + s.dur;
        return (
          <React.Fragment key={s.id}>
            <div style={{ position: "absolute", left: x(s.start), top: 30, width: Math.max(2, x(s.start + s.dur) - x(s.start) - 2), height: 22, background: on ? GOLD : "rgba(255,244,220,0.28)", borderRadius: 3 }} />
            {s.clip_s ? (
              <div title="clip" style={{ position: "absolute", left: x(s.start), top: 58, width: x(s.start + s.clip_s) - x(s.start), height: 8, background: "#f97316", borderRadius: 3 }} />
            ) : null}
          </React.Fragment>
        );
      })}
      <div style={{ position: "absolute", left: x(t) - 1, top: 22, width: 3, height: 50, background: "white" }} />
      <div style={{ position: "absolute", left: 40, top: 76, fontSize: 20, color: "rgba(255,244,220,0.7)" }}>
        shots (gold = now) · orange = paid clip length · {t.toFixed(1)} s / {p.total_s.toFixed(1)} s
      </div>
    </div>
  );
};

/* ------------------------------------------------------------- type */

const Words: React.FC<{ text: string }> = ({ text }) => (
  <>
    {text.split(" ").map((w, i) => (
      <span key={i} style={{ color: NAMES.some((n) => w.includes(n)) ? GOLD : CREAM }}>
        {w}{" "}
      </span>
    ))}
  </>
);

const CaptionLine: React.FC<{ text: string; t: number; dur: number }> = ({ text, t, dur }) => {
  const op = clamp(Math.min(t / 0.12, (dur - t) / 0.12), 0, 1);
  return (
    <div style={{ position: "absolute", left: 0, right: 0, top: 1450, display: "flex", justifyContent: "center", opacity: op }}>
      <div style={{ maxWidth: 940, padding: "14px 30px 20px", borderRadius: 22, background: "rgba(22,12,24,0.62)", fontFamily: F, fontWeight: 700, fontSize: 48, lineHeight: 1.35, textAlign: "center" }}>
        <Words text={text} />
      </div>
    </div>
  );
};

const Typeset: React.FC<{ s: PreviewShot; t: number }> = ({ s, t }) => {
  const ty = s.type!;
  const at = ty.at ?? 0;
  const base: React.CSSProperties = { position: "absolute", left: 0, right: 0, textAlign: "center", fontFamily: F };
  if (ty.kind === "title") {
    // On the first frame: no fade-in, so the thumbnail frame already carries the place name.
    return (
      <div style={{ ...base, top: 640 }}>
        <div style={{ fontSize: 96, fontWeight: 900, color: GOLD, textShadow: "0 6px 30px rgba(0,0,0,0.8)" }}>{ty.lines[0]}</div>
        <div style={{ fontSize: 118, fontWeight: 900, color: CREAM, textShadow: "0 6px 30px rgba(0,0,0,0.8)" }}>{ty.lines[1]}</div>
      </div>
    );
  }
  if (ty.kind === "date") {
    // The year lands on the spoken year; the rest builds 1.4 s later.
    const a = ramp(t, at, at + 0.35);
    const b = ramp(t, at + 1.4, at + 1.8);
    return (
      <div style={{ ...base, top: 760 }}>
        <div style={{ fontSize: 132, fontWeight: 900, color: GOLD, opacity: a, transform: `translateY(${(1 - a) * 30}px)`, textShadow: "0 6px 30px rgba(0,0,0,0.8)" }}>{ty.lines[0]}</div>
        <div style={{ fontSize: 72, fontWeight: 700, color: CREAM, opacity: b, textShadow: "0 6px 30px rgba(0,0,0,0.8)" }}>{ty.lines[1]}</div>
      </div>
    );
  }
  const rows = ty.lines;
  const size = ty.kind === "name" ? 92 : ty.kind === "card" ? 70 : 52;
  const top = ty.kind === "questions" ? 720 : ty.kind === "reminders" ? 760 : 860;
  return (
    <div style={{ ...base, top, display: "flex", flexDirection: "column", alignItems: "center", gap: 22 }}>
      {rows.map((r, i) => {
        const o = ramp(t, at + i * 1.1, at + i * 1.1 + 0.35);
        return (
          <div
            key={i}
            style={{
              fontSize: size,
              fontWeight: ty.kind === "name" ? 900 : 700,
              color: ty.kind === "name" || ty.kind === "card" ? GOLD : CREAM,
              opacity: o,
              transform: `translateY(${(1 - o) * 24}px)`,
              padding: ty.kind === "questions" || ty.kind === "reminders" ? "10px 26px" : 0,
              borderRadius: 16,
              background: ty.kind === "questions" || ty.kind === "reminders" ? "rgba(20,10,14,0.66)" : "transparent",
              textShadow: "0 6px 26px rgba(0,0,0,0.8)",
              maxWidth: 960,
            }}
          >
            {r}
          </div>
        );
      })}
    </div>
  );
};

/* ------------------------------------------------------------- shot */

const Shot: React.FC<{ s: PreviewShot; span: number }> = ({ s, span }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const p = clamp(t / span, 0, 1);

  // Emergence (S02): light gathers over 1.6 s, peaks, then settles under the held question.
  const emerge = s.fx === "emerge" ? ramp(t, 0.1, 1.7) * (1 - 0.45 * ramp(t, 2.2, 3.2)) : 0;
  // Return into light (S15): builds slowly, whites out at the end of the line.
  const ret = s.fx === "return" ? ramp(t, 2.0, s.dur - 0.6) : 0;
  const arati = s.fx === "arati" ? 0.45 + 0.25 * sine(frame, 1.6) : 0;
  const lampStrength = 0.75 + 0.6 * emerge + 0.5 * ret + arati;

  return (
    <AbsoluteFill>
      {s.art.kind === "temp" ? (
        <TempArt src={s.art.src} pos={s.art.pos} p={p} />
      ) : s.art.src === "stone" ? (
        <StonePlate t={t} />
      ) : (
        <LampPlate frame={frame} strength={lampStrength} />
      )}
      {s.id === "S13" ? <AbsoluteFill style={{ background: "rgba(10,5,8,0.5)" }} /> : null}
      {emerge > 0 ? <Bloom x={540} y={900} r={220 + 420 * emerge} opacity={emerge} /> : null}
      {ret > 0 ? <Bloom x={540} y={900} r={260 + 900 * ret} opacity={ret} /> : null}
      {s.fx === "emerge" ? (
        <div style={{ position: "absolute", left: 0, right: 0, top: 1210, textAlign: "center", fontFamily: UI, fontSize: 24, color: "#fde68a", opacity: 0.9 }}>
          question lands at {(s.dur - s.hold).toFixed(1)} s, held {s.hold.toFixed(1)} s on his face (was 0.5 s on screen)
        </div>
      ) : null}
      {s.type ? <Typeset s={s} t={t} /> : null}
      {s.text && s.type?.kind !== "title" ? <CaptionLine text={s.text} t={t} dur={s.dur - s.hold + 0.1} /> : null}
      <Label s={s} />
    </AbsoluteFill>
  );
};

export const EpisodePreview: React.FC<PreviewProps> = (props) => {
  useTeluguFont();
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const shots = props.shots;
  return (
    <AbsoluteFill style={{ background: "#120a0e" }}>
      {shots.map((s, i) => {
        // Each picture stays up until the next shot starts (pauses between sentences included).
        const end = i + 1 < shots.length ? shots[i + 1].start : props.total_s;
        return (
          <Sequence key={s.id} from={Math.round(s.start * fps)} durationInFrames={Math.max(1, Math.round((end - s.start) * fps))}>
            <Shot s={s} span={end - s.start} />
          </Sequence>
        );
      })}
      <Header p={props} />
      <Strip p={props} t={t} />
      {props.music ? <Audio src={staticFile(props.music)} volume={0.55} /> : null}
    </AbsoluteFill>
  );
};
