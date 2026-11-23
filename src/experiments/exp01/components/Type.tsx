import React from "react";
import { continueRender, delayRender, staticFile } from "remotion";
import { clamp, ramp } from "../lib/motion";

/** Load Noto Sans Telugu (OFL) from public/ before the first frame is taken. */
const FAMILY = "Exp01Telugu";
let loaded = false;
export const useTeluguFont = () => {
  const [handle] = React.useState(() => (loaded ? null : delayRender("Telugu font")));
  React.useEffect(() => {
    if (!handle) return;
    const faces = [
      new FontFace(FAMILY, `url(${staticFile("exp01/fonts/NotoSansTelugu_700Bold.ttf")})`, { weight: "700" }),
      new FontFace(FAMILY, `url(${staticFile("exp01/fonts/NotoSansTelugu_900Black.ttf")})`, { weight: "900" }),
    ];
    Promise.all(faces.map((f) => f.load()))
      .then((fs) => {
        fs.forEach((f) => document.fonts.add(f));
        loaded = true;
        continueRender(handle);
      })
      .catch((e) => {
        console.error(e);
        continueRender(handle);
      });
  }, [handle]);
};

const INK = "#24131f";
const GOLD = "#f6c454";
const CREAM = "#fff4dc";
/** Names shown in gold, as in Episode 1's captions. */
const NAMES = ["మల్లన్న", "ఎల్లమ్మ", "కొమురవెల్లి", "బండారి"];

const Words: React.FC<{ text: string }> = ({ text }) => (
  <>
    {text.split(" ").map((w, i) => (
      <span key={i} style={{ color: NAMES.some((n) => w.startsWith(n)) ? GOLD : CREAM }}>
        {w}
        {" "}
      </span>
    ))}
  </>
);

/**
 * Episode-1-style caption: translucent dark band, 0.12 s fades. Times in seconds.
 * `top` is per line, so a caption can move off the action (Episode 1 always used 1290).
 */
export const Caption: React.FC<{ t: number; lines: { a: number; b: number; text: string; top?: number }[] }> = ({ t, lines }) => {
  const cur = lines.find((l) => t >= l.a - 0.12 && t <= l.b + 0.12);
  if (!cur) return null;
  const op = clamp(Math.min((t - (cur.a - 0.12)) / 0.12, (cur.b + 0.12 - t) / 0.12), 0, 1);
  return (
    <div style={{ position: "absolute", left: 0, right: 0, top: cur.top ?? 1290, display: "flex", justifyContent: "center", opacity: op }}>
      <div
        style={{
          maxWidth: 900,
          padding: "14px 30px 20px",
          borderRadius: 22,
          background: "rgba(22,12,24,0.58)",
          fontFamily: FAMILY,
          fontWeight: 700,
          fontSize: 52,
          lineHeight: 1.35,
          textAlign: "center",
        }}
      >
        <Words text={cur.text} />
      </div>
    </div>
  );
};

/** Location title: distance line, district, then the place name; each rises in on its spoken word. */
export const LocationTitle: React.FC<{ t: number; distAt: number; districtAt: number; nameAt: number; outAt: number }> = ({
  t,
  distAt,
  districtAt,
  nameAt,
  outAt,
}) => {
  const out = 1 - ramp(t, outAt, outAt + 0.4);
  const item = (at: number) => {
    const k = ramp(t, at, at + 0.45);
    return { opacity: k * out, transform: `translateY(${(1 - k) * 26}px)` };
  };
  const stroke = `-3px -3px 0 ${INK}, 3px -3px 0 ${INK}, -3px 3px 0 ${INK}, 3px 3px 0 ${INK}, 0 6px 18px rgba(0,0,0,0.55)`;
  return (
    <div style={{ position: "absolute", left: 0, right: 0, top: 300, textAlign: "center", fontFamily: FAMILY }}>
      <div style={{ ...item(distAt), fontWeight: 700, fontSize: 44, color: CREAM, textShadow: stroke }}>
        హైదరాబాద్ నుంచి 85 కి.మీ
      </div>
      <div style={{ ...item(districtAt), marginTop: 14, fontWeight: 700, fontSize: 46, color: CREAM, textShadow: stroke }}>
        సిద్దిపేట జిల్లా
      </div>
      <div
        style={{
          ...item(nameAt),
          marginTop: 6,
          fontWeight: 900,
          fontSize: 118,
          color: GOLD,
          letterSpacing: 1,
          textShadow: `-5px -5px 0 ${INK}, 5px -5px 0 ${INK}, -5px 5px 0 ${INK}, 5px 5px 0 ${INK}, 0 10px 26px rgba(0,0,0,0.6)`,
        }}
      >
        కొమురవెల్లి
      </div>
    </div>
  );
};

/** Closing line, as in Episode 1's end card. */
export const ClosingTitle: React.FC<{ t: number; a1: number; a2: number }> = ({ t, a1, a2 }) => {
  const k1 = ramp(t, a1, a1 + 0.4);
  const k2 = ramp(t, a2, a2 + 0.4);
  const stroke = (w: number) =>
    `-${w}px -${w}px 0 ${INK}, ${w}px -${w}px 0 ${INK}, -${w}px ${w}px 0 ${INK}, ${w}px ${w}px 0 ${INK}, 0 8px 22px rgba(0,0,0,0.6)`;
  return (
    <div style={{ position: "absolute", left: 0, right: 0, top: 1250, textAlign: "center", fontFamily: FAMILY }}>
      {/* soft dark pool so the line reads over the garlands without a hard box */}
      <div
        style={{
          position: "absolute",
          left: -60,
          right: -60,
          top: -90,
          height: 400,
          opacity: k1,
          background: "radial-gradient(ellipse 620px 210px at 50% 50%, rgba(18,9,16,0.78) 0%, rgba(18,9,16,0.5) 55%, rgba(18,9,16,0) 100%)",
        }}
      />
      <div style={{ position: "relative", opacity: k1, transform: `translateY(${(1 - k1) * 24}px)`, fontWeight: 900, fontSize: 70, color: GOLD, textShadow: stroke(4) }}>
        కొమురవెల్లి మల్లన్నకు
      </div>
      <div style={{ position: "relative", opacity: k2, transform: `scale(${0.9 + 0.1 * k2})`, marginTop: 8, fontWeight: 900, fontSize: 92, color: CREAM, textShadow: stroke(5) }}>
        కోటి దండాలు!
      </div>
    </div>
  );
};
