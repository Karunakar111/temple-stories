import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { PALETTE } from "../design/palette";

/**
 * Phrase-by-phrase subtitles.
 *
 * A whole paragraph held for twelve seconds is unreadable on a phone and looks
 * nothing like the short-form reels this is competing with. So each shot's line is
 * split into speakable phrases and shown one at a time across the shot.
 *
 * Phrase timing is proportional to character count, not word-level alignment —
 * we have no per-word timestamps for the narration. That is close enough because
 * the split points are the same punctuation the voice actually pauses on, and the
 * shot boundaries themselves are already snapped to measured pauses.
 */

const MIN_WORDS = 3;
const MAX_WORDS = 9;

const wc = (t: string) => t.trim().split(/\s+/).filter(Boolean).length;

/** Split one chunk on a separator, but only where both sides are worth showing. */
const softSplit = (chunk: string, re: RegExp): string[] => {
  const parts = chunk.split(re).map((p) => p.trim()).filter(Boolean);
  if (parts.length < 2) return [chunk];
  if (parts.some((p) => wc(p) < MIN_WORDS)) return [chunk]; // would make a runt
  return parts;
};

export const splitPhrases = (text: string): string[] => {
  // Sentences are the hard boundary — the read always stops there.
  let out = text
    .split(/(?<=[.?!])\s+/)
    .map((t) => t.trim())
    .filter(Boolean);

  // Only break a sentence further if it is actually too long. Em-dash first
  // (that is where this script breathes), then commas.
  for (const re of [/\s+—\s+/, /,\s+/]) {
    out = out.flatMap((c) => (wc(c) > MAX_WORDS ? softSplit(c, re) : [c]));
  }

  // Anything still over the cap gets hard-wrapped rather than left unreadable.
  out = out.flatMap((c) => {
    if (wc(c) <= MAX_WORDS) return [c];
    const w = c.split(/\s+/);
    const chunks: string[] = [];
    for (let i = 0; i < w.length; i += MAX_WORDS) {
      chunks.push(w.slice(i, i + MAX_WORDS).join(" "));
    }
    return chunks;
  });

  // Fold a leftover runt backwards, but never past the cap.
  return out.reduce<string[]>((acc, p) => {
    const prev = acc[acc.length - 1];
    if (acc.length && wc(p) < MIN_WORDS && prev && wc(prev) + wc(p) <= MAX_WORDS + 2) {
      acc[acc.length - 1] = prev + " " + p;
    } else {
      acc.push(p);
    }
    return acc;
  }, []);
};

export const Subtitle: React.FC<{ text: string }> = ({ text }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  const phrases = React.useMemo(() => splitPhrases(text), [text]);
  if (phrases.length === 0) return null;

  // Weight each phrase by its length so long ones get more screen time.
  const weights = phrases.map((p) => Math.max(p.length, 12));
  const totalWeight = weights.reduce((a, b) => a + b, 0);

  let acc = 0;
  const spans = weights.map((w) => {
    const start = (acc / totalWeight) * durationInFrames;
    acc += w;
    return { start, end: (acc / totalWeight) * durationInFrames };
  });

  const i = Math.max(0, spans.findIndex((s) => frame < s.end));
  const span = spans[i] ?? spans[spans.length - 1];
  const len = Math.max(1, span.end - span.start);
  const local = frame - span.start;

  // Short cross-fade in and out, capped so brief phrases don't spend their whole
  // life fading.
  const fade = Math.min(4, len / 4);
  const opacity = interpolate(
    local,
    [0, fade, len - fade, len],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );

  return (
    <AbsoluteFill
      style={{
        justifyContent: "flex-start",
        alignItems: "center",
        paddingTop: 165,
        paddingLeft: 80,
        paddingRight: 80,
      }}
    >
      <div
        style={{
          color: PALETTE.bone,
          fontFamily: "Inter, Helvetica, sans-serif",
          fontSize: 56,
          lineHeight: 1.22,
          fontWeight: 800,
          textAlign: "center",
          letterSpacing: 0.2,
          textShadow: "0 4px 22px rgba(0,0,0,0.9)",
          opacity,
        }}
      >
        {phrases[i] ?? ""}
      </div>
    </AbsoluteFill>
  );
};
