import React from "react";
import { AbsoluteFill, Img, staticFile, useCurrentFrame } from "remotion";
import { useTeluguFont } from "../experiments/exp01/components/Type";

/**
 * Text-only layers for gudi/assemble.py. OverlayLayer: frame i is item i, alone, on a transparent
 * background (FFmpeg places each PNG over the picture for its own time window). Cover: one frame.
 * No video is decoded here, so this renders on macOS 12 as well.
 */
const F = "Exp01Telugu";
const GOLD = "#f6c454";
const CREAM = "#fff4dc";
const SHADOW = "0 4px 0 #140a04, 0 0 18px rgba(0,0,0,0.85), 0 6px 30px rgba(0,0,0,0.8)";

export type Item = { kind: string; text?: string; lines?: string[]; names?: string[]; top?: number };  // top: optional override, px from the top of 1920

const Words: React.FC<{ text: string; names: string[] }> = ({ text, names }) => (
  <>
    {text.split(" ").map((w, i) => (
      <span key={i} style={{ color: names.some((n) => w.startsWith(n)) ? GOLD : CREAM }}>
        {w}{" "}
      </span>
    ))}
  </>
);

const Caption: React.FC<{ it: Item }> = ({ it }) => (
  <div style={{ position: "absolute", left: 0, right: 0, top: 1290, transform: "translateY(-50%)", display: "flex", justifyContent: "center" }}>
    <div style={{ maxWidth: 960, padding: "14px 34px 18px", borderRadius: 28, background: "rgba(10,5,2,0.47)", fontFamily: F, fontWeight: 700,
      fontSize: 60, lineHeight: 1.45, textAlign: "center", textShadow: SHADOW }}>
      <Words text={it.text || ""} names={it.names || []} />
    </div>
  </div>
);

const Block: React.FC<{ it: Item }> = ({ it }) => {
  const lines = it.lines || [it.text || ""];
  const base: React.CSSProperties = { position: "absolute", left: 40, right: 40, textAlign: "center", fontFamily: F, textShadow: SHADOW };
  if (it.kind === "title") {
    return (
      <div style={{ ...base, top: it.top ?? 600 }}>
        <div style={{ fontSize: 100, fontWeight: 900, color: GOLD, lineHeight: 1.2 }}>{lines[0]}</div>
        {lines[1] ? <div style={{ fontSize: 118, fontWeight: 900, color: CREAM, lineHeight: 1.2 }}>{lines[1]}</div> : null}
      </div>
    );
  }
  if (it.kind === "date") {
    return (
      <div style={{ ...base, top: it.top ?? 720 }}>
        <div style={{ fontSize: 132, fontWeight: 900, color: GOLD }}>{lines[0]}</div>
        {lines[1] ? <div style={{ fontSize: 72, fontWeight: 700, color: CREAM }}>{lines[1]}</div> : null}
      </div>
    );
  }
  if (it.kind === "blessing") {
    // closing frame: the deity's chant large in gold, the temple name small beneath
    return (
      <div style={{ ...base, top: 760, display: "flex", flexDirection: "column", alignItems: "center", gap: 26 }}>
        <div style={{ fontSize: 40, color: GOLD, letterSpacing: 18, opacity: 0.9 }}>✦ ✦ ✦</div>
        <div style={{ fontSize: 128, fontWeight: 900, color: GOLD, lineHeight: 1.25 }}>{lines[0]}</div>
        {lines[1] ? <div style={{ fontSize: 62, fontWeight: 700, color: CREAM, lineHeight: 1.3 }}>{lines[1]}</div> : null}
      </div>
    );
  }
  if (it.kind === "mark") {
    // small disclosure on an illustrated stand-in for a real object, e.g. ప్రతీకాత్మక చిత్రం
    return (
      <div style={{ position: "absolute", right: 36, top: 150, padding: "8px 18px", borderRadius: 10, background: "rgba(20,10,14,0.62)",
        color: CREAM, fontFamily: F, fontSize: 36, fontWeight: 700 }}>
        {lines[0]}
      </div>
    );
  }
  const boxed = it.kind === "questions" || it.kind === "reminders" || it.kind === "comment";
  const size = it.kind === "name" ? 92 : it.kind === "card" ? 72 : 54;
  const top = it.top ?? (boxed ? 700 : 820);
  return (
    <div style={{ ...base, top, display: "flex", flexDirection: "column", alignItems: "center", gap: 22 }}>
      {lines.map((l, i) => (
        <div key={i} style={{ fontSize: size, fontWeight: it.kind === "name" ? 900 : 700, color: it.kind === "name" || it.kind === "card" ? GOLD : CREAM,
          padding: boxed ? "12px 28px" : 0, borderRadius: 18, background: boxed ? "rgba(20,10,14,0.66)" : "transparent", maxWidth: 980 }}>
          {l}
        </div>
      ))}
    </div>
  );
};

const Label: React.FC<{ it: Item }> = ({ it }) => (
  <div style={{ position: "absolute", left: 36, top: 36, padding: "8px 16px", borderRadius: 8, background: "#c2410c", color: "white",
    fontFamily: "Helvetica, Arial, sans-serif", fontSize: 28, fontWeight: 800 }}>
    {it.text}
  </div>
);

export const OverlayLayer: React.FC<{ items: Item[] }> = ({ items }) => {
  useTeluguFont();
  const frame = useCurrentFrame();
  const it = items[frame];
  if (!it) return null;
  return (
    <AbsoluteFill style={{ background: "transparent" }}>
      {it.kind === "caption" ? <Caption it={it} /> : it.kind === "label" ? <Label it={it} /> : <Block it={it} />}
    </AbsoluteFill>
  );
};

export type CoverProps = { bg: string; title: string[]; line: string; badge?: string };

export const Cover: React.FC<CoverProps> = ({ bg, title, line, badge }) => {
  useTeluguFont();
  return (
    <AbsoluteFill style={{ background: "#1a0e08" }}>
      {bg ? <Img src={staticFile(bg)} style={{ width: "100%", height: "100%", objectFit: "cover" }} /> : null}
      <AbsoluteFill style={{ background: "linear-gradient(180deg, rgba(10,5,2,0.55) 0%, rgba(10,5,2,0) 38%, rgba(10,5,2,0) 55%, rgba(10,5,2,0.8) 100%)" }} />
      <div style={{ position: "absolute", left: 50, right: 50, top: 170, textAlign: "center", fontFamily: F, textShadow: SHADOW }}>
        <div style={{ fontSize: 104, fontWeight: 900, color: GOLD, lineHeight: 1.15 }}>{title[0]}</div>
        {title[1] ? <div style={{ fontSize: 124, fontWeight: 900, color: CREAM, lineHeight: 1.15 }}>{title[1]}</div> : null}
      </div>
      <div style={{ position: "absolute", left: 60, right: 60, bottom: 330, display: "flex", justifyContent: "center" }}>
        <div style={{ padding: "18px 34px 22px", borderRadius: 26, background: "rgba(20,10,14,0.72)", fontFamily: F, fontWeight: 800, fontSize: 64,
          lineHeight: 1.4, color: CREAM, textAlign: "center", textShadow: SHADOW }}>
          {line}
        </div>
      </div>
      {badge ? (
        <div style={{ position: "absolute", left: 36, top: 36, padding: "8px 16px", borderRadius: 8, background: "#c2410c", color: "white",
          fontFamily: "Helvetica, Arial, sans-serif", fontSize: 28, fontWeight: 800 }}>{badge}</div>
      ) : null}
    </AbsoluteFill>
  );
};
