import React from "react";
import {
  AbsoluteFill, Audio, Img, Sequence, interpolate, spring, staticFile,
  useCurrentFrame, useVideoConfig, getRemotionEnvironment,
} from "remotion";
import { PALETTE } from "../design/palette";

/**
 * Komuravelli pilot — 16 s, three shots, cut to the real narration.
 *
 * Shot boundaries come from the RMS gap map of audio/pilot-narration.mp3 (cut from
 * part 2 at 33.80 s), so every cut lands in a pause the voice already leaves.
 *
 * The clips play as pre-extracted JPEG sequences rather than through Remotion's
 * <Video>: Remotion decodes video with its bundled compositor, which is the
 * macOS-15-only binary that cannot run here (docs/SETUP_NOTES.md). Our own FFmpeg
 * does the extraction instead.
 */

export const SHOTS = [
  { id: "shot1", from: 0, to: 123, clipFrames: 122, caption: "ఆ బండారే — ఈ రోజు మీరు జాతరల చల్లే పసుపు" },
  { id: "shot2", from: 123, to: 193, clipFrames: 71, caption: "ఈ కథ ఏ పుస్తకంల లేదు" },
  { id: "shot3", from: 193, to: 480, clipFrames: 151, caption: "ఒగ్గు పూజారి పాడతడు — పాడుకుంటనే నేల మీద గీస్తడు" },
] as const;

const Clip: React.FC<{ id: string; clipFrames: number; duration: number }> = ({
  id, clipFrames, duration,
}) => {
  const frame = useCurrentFrame();
  const idx = Math.min(clipFrames - 1, Math.max(0, frame));
  const held = Math.max(0, frame - (clipFrames - 1));
  // only the held tail gets a push, so live footage is never re-scaled
  const scale = 1 + interpolate(held, [0, Math.max(1, duration - clipFrames)], [0, 0.06], {
    extrapolateRight: "clamp",
  });
  const n = String(idx + 1).padStart(4, "0");
  return (
    <AbsoluteFill style={{ backgroundColor: "#000", overflow: "hidden" }}>
      <Img
        src={staticFile(`frames/${id}/f${n}.jpg`)}
        style={{ width: "100%", height: "100%", objectFit: "cover", transform: `scale(${scale})` }}
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
      {SHOTS.map((s) => {
        const dur = s.to - s.from;
        return (
          <Sequence key={s.id} from={s.from} durationInFrames={dur} name={s.id}>
            <Clip id={s.id} clipFrames={s.clipFrames} duration={dur} />
            <Caption text={s.caption} duration={dur} />
          </Sequence>
        );
      })}
      <AbsoluteFill style={{ backgroundColor: "#000", opacity: dip * 0.85 }} />
    </AbsoluteFill>
  );
};
