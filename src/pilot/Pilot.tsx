import React from "react";
import {
  AbsoluteFill, Audio, Img, Sequence, interpolate, spring, staticFile,
  useCurrentFrame, useVideoConfig, getRemotionEnvironment,
} from "remotion";
import { PALETTE } from "../design/palette";

/**
 * Komuravelli pilot — 9.6 s, three shots, cut to the real narration.
 *
 * v2 (2026-11-23), two corrections:
 *
 * 1. The narration no longer claims "ఈ కథ ఏ పుస్తకంల లేదు" (this story is in no book).
 *    It is not true — research §8 cites Sakshi and the folklore literature, and Oggu
 *    Katha has been collected and published. The clause was excised from the audio
 *    between its surrounding pauses; script v1.1 replaces it with
 *    "ఈ కథ ఇప్పటికీ పాటల్లనే ఉంది".
 *
 * 2. No frozen tail. Every shot now runs entirely on live footage — the longest,
 *    shot 3, uses 130 of its clip's 151 frames, so nothing is ever held.
 *
 * Captions are decoupled from shots: a sentence can span a cut, which is how speech
 * actually behaves.
 *
 * The clips play as pre-extracted JPEG sequences rather than through Remotion's
 * <Video>: Remotion decodes video with its bundled compositor, which is the
 * macOS-15-only binary that cannot run here (docs/SETUP_NOTES.md). Our own FFmpeg
 * does the extraction instead.
 */

export const PILOT_FRAMES = 288; // 9.60 s @ 30 fps

export const SHOTS = [
  { id: "shot1", from: 0, to: 88, clipFrames: 122 },
  { id: "shot2", from: 88, to: 158, clipFrames: 71 },
  { id: "shot3", from: 158, to: 288, clipFrames: 151 },
] as const;

// Cut points come from the RMS gap map of the corrected narration: 2.84–3.04 s and
// 5.04–5.50 s. Every shot's length is <= its clip's length, so no frame is ever held.

const CAPTIONS = [
  { from: 0, to: 117, text: "ఆ బండారే — ఈ రోజు మీరు జాతరల చల్లే పసుపు" },
  { from: 117, to: 288, text: "ఒగ్గు పూజారి పాడతడు — పాడుకుంటనే నేల మీద గీస్తడు" },
] as const;

const Clip: React.FC<{ id: string; clipFrames: number }> = ({ id, clipFrames }) => {
  const frame = useCurrentFrame();
  const idx = Math.min(clipFrames - 1, Math.max(0, frame));
  const n = String(idx + 1).padStart(4, "0");
  return (
    <AbsoluteFill style={{ backgroundColor: "#000", overflow: "hidden" }}>
      <Img
        src={staticFile(`frames/${id}/f${n}.jpg`)}
        style={{ width: "100%", height: "100%", objectFit: "cover" }}
      />
    </AbsoluteFill>
  );
};

const Caption: React.FC<{ text: string; duration: number }> = ({ text, duration }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame: frame - 4, fps, config: { damping: 18, mass: 0.6 } });
  const out = interpolate(frame, [duration - 10, duration], [1, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });
  return (
    <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: 170 }}>
      <div
        style={{
          opacity: Math.min(s, out),
          transform: `translateY(${interpolate(s, [0, 1], [22, 0])}px)`,
          maxWidth: "86%", textAlign: "center",
          background: "rgba(16,10,8,0.58)", borderRadius: 18, padding: "20px 30px",
          color: PALETTE.bone, fontSize: 50, lineHeight: 1.3, fontWeight: 800,
          textShadow: "0 4px 18px rgba(0,0,0,0.95)",
        }}
      >
        {text}
      </div>
    </AbsoluteFill>
  );
};

export const Pilot: React.FC = () => {
  const frame = useCurrentFrame();
  // short dip to black at each cut so the joins read as edits, not glitches
  const dip = SHOTS.slice(1).reduce((acc, s) => {
    const d = Math.abs(frame - s.from);
    return Math.max(acc, d < 4 ? 1 - d / 4 : 0);
  }, 0);

  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      {getRemotionEnvironment().isRendering ? null : (
        <Audio src={staticFile("audio/pilot-narration.mp3")} />
      )}
      {SHOTS.map((s) => (
        <Sequence key={s.id} from={s.from} durationInFrames={s.to - s.from} name={s.id}>
          <Clip id={s.id} clipFrames={s.clipFrames} />
        </Sequence>
      ))}
      <AbsoluteFill style={{ backgroundColor: "#000", opacity: dip * 0.85 }} />
      {CAPTIONS.map((c, i) => (
        <Sequence key={i} from={c.from} durationInFrames={c.to - c.from} name={`caption${i + 1}`}>
          <Caption text={c.text} duration={c.to - c.from} />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};
