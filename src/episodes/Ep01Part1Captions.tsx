import React from "react";
import { AbsoluteFill, Sequence, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { PALETTE } from "../design/palette";
import timing from "./01-part1-timing.json";

/**
 * Episode 1, Part 1 — the caption / title layer ONLY.
 *
 * This composition renders on a TRANSPARENT background and is composited over
 * exports/ep01-picture.mp4 by FFmpeg. It exists separately because this machine
 * has under a gigabyte of free disk: extracting the whole 2030-frame picture
 * track to a JPEG sequence so Remotion could draw over it would need well over
 * a gigabyte, while a mostly-empty PNG sequence costs a fraction of that.
 *
 * Timings come from 01-part1-timing.json, which was derived from the RMS
 * envelope of the real narration, so every caption change lands on speech.
 */

export const FPS = 30;
export const EP01_FRAMES = timing.durationInFrames; // 2030 = 67.68 s

const F = (s: number) => Math.round(s * FPS);

/** Cut points of the picture track, for the short dip to black at each join. */
const CUTS = [3.4, 5.08, 9.8, 14.48, 20.6, 26.8, 28.0, 33.7, 40.38, 44.22, 51.38, 59.24].map(F);

type Chunk = { te: string; en: string; w: number };

/** Each narration beat split into readable chunks, weighted by word count. */
const BEATS: { shot: number; chunks: Chunk[] }[] = [
  {
    shot: 1,
    chunks: [{ te: "కొమురవెల్లి మల్లన్నకు — కోటి దండాలు!", en: "Komuravelli Mallanna — a crore of salutations!", w: 5 }],
  },
  {
    shot: 2,
    chunks: [
      { te: "హైదరాబాద్ నుంచి ఎనభై ఐదు కిలోమీటర్లు.", en: "Eighty-five kilometres from Hyderabad.", w: 5 },
      { te: "సిద్దిపేట జిల్లా — కొమురవెల్లి కొండ.", en: "Siddipet district — the hill at Komuravelli.", w: 4 },
      { te: "ఇక్కడ మీరు చల్లే ఈ పసుపు —", en: "This turmeric you throw here —", w: 5 },
      { te: "ఇది ఎక్కడి నుంచి వచ్చిందో తెలుసా?", en: "do you know where it came from?", w: 5 },
    ],
  },
  {
    shot: 3,
    chunks: [
      { te: "ఇక్కడ ఒగ్గు పూజారులు పాడే కథ ప్రకారం —", en: "By the story the Oggu priests sing here —", w: 6 },
      { te: "గుడి కట్టకముందు ఈ కొండ మీద అడివి ఉండేది.", en: "before the temple, this hill was forest.", w: 6 },
      { te: "గొర్రెలు, వాటి కాపర్లు.", en: "Sheep, and their herders.", w: 3 },
      { te: "వాళ్ల కోసం దిగొచ్చిన దేవుడే మల్లన్న.", en: "The god who came down for them was Mallanna.", w: 5 },
      { te: "రాయి కాదు — పుట్టమట్టి.", en: "Not stone — termite-mound earth.", w: 4 },
    ],
  },
  {
    shot: 4,
    chunks: [
      { te: "మల్లన్నకు మేడలమ్మ అంటే ఇష్టం.", en: "Mallanna loved Medalamma.", w: 4 },
      { te: "లింగ బలిజల బిడ్డ.", en: "A daughter of the Linga Balijas.", w: 3 },
      { te: "కానీ ఆమె అన్నలు ఒక షరతు పెట్టిండ్రు.", en: "But her brothers set one condition.", w: 6 },
    ],
  },
  {
    shot: 5,
    chunks: [
      { te: "బండారి తీసుకురా. పసుపు కొమ్ములు.", en: "Bring the bandari. The turmeric horns.", w: 4 },
      { te: "అవి ఎక్కడో దూరంగ ఉన్నయ్ —", en: "They were kept far away —", w: 4 },
      { te: "ఐదు తలల పాము కాపలగ.", en: "with a five-headed serpent on guard.", w: 4 },
    ],
  },
  {
    shot: 6,
    chunks: [
      { te: "దేవతలు ఆయనకు ఒక ఎగిరే గుర్రం ఇచ్చిండ్రు.", en: "The gods gave him a flying horse.", w: 6 },
      { te: "మల్లన్న బయల్దేరిండు.", en: "Mallanna set out.", w: 2 },
    ],
  },
  {
    shot: 7,
    chunks: [
      { te: "అక్కడ ఆయన దేవుడిలా పోలే.", en: "He didn't arrive as a god.", w: 4 },
      { te: "తోటమాలిగ చేరిండు. పేరు మార్చుకున్నడు.", en: "He joined as a gardener. Changed his name.", w: 4 },
      { te: "రోజులు గడిచినయ్. నెలలు గడిచినయ్.", en: "Days passed. Months passed.", w: 4 },
      { te: "అందరూ నమ్మేదాకా — ఆగిండు.", en: "Until every one of them trusted him — he waited.", w: 4 },
    ],
  },
  {
    shot: 8,
    chunks: [
      { te: "ఒక రోజు — పాము కళ్లు మూసుకున్న క్షణంల —", en: "One day — in the moment the serpent's eyes closed —", w: 6 },
      { te: "బండారి ఆయన చేతిల. మొదటిసారి.", en: "the bandari was in his hand. For the first time.", w: 4 },
      { te: "కానీ ఎవరో చూసిండ్రు.", en: "But someone saw.", w: 3 },
    ],
  },
  {
    shot: 9,
    chunks: [
      { te: "పసుపు దొరికింది. ఇగ ఇంటికి చేరాలె.", en: "He had the turmeric. Now he had to get it home.", w: 5 },
      { te: "అది తర్వాతి కథ.", en: "That's the next story.", w: 3 },
      { te: "ఈలోపు చెప్పుండ్రి — మీ ఊళ్ల ఆ అన్నలు ఏం అడిగిండ్రని చెప్తరు?", en: "Till then — in your village, what do they say the brothers asked for?", w: 10 },
    ],
  },
];

/** Flatten beats into absolute frame ranges, dividing each beat by word weight. */
const CAPTIONS: { from: number; to: number; te: string; en: string }[] = [];
for (const beat of BEATS) {
  const t = timing.shots.find((s) => s.n === beat.shot)!;
  const totalW = beat.chunks.reduce((a, c) => a + c.w, 0);
  let cursor = t.startFrame;
  beat.chunks.forEach((c, i) => {
    const span = Math.round((t.endFrame - t.startFrame) * (c.w / totalW));
    const to = i === beat.chunks.length - 1 ? t.endFrame : cursor + span;
    CAPTIONS.push({ from: cursor, to, te: c.te, en: c.en });
    cursor = to;
  });
}

const Caption: React.FC<{ te: string; en: string; duration: number }> = ({ te, en, duration }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame: frame - 2, fps, config: { damping: 20, mass: 0.5 } });
  const out = interpolate(frame, [duration - 7, duration], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return (
    <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: 190 }}>
      <div
        style={{
          opacity: Math.min(s, out),
          transform: `translateY(${interpolate(s, [0, 1], [18, 0])}px)`,
          maxWidth: "88%",
          textAlign: "center",
          background: "rgba(14,9,7,0.62)",
          borderRadius: 20,
          padding: "20px 30px 17px",
        }}
      >
        <div
          style={{
            color: PALETTE.bone,
            fontSize: 48,
            lineHeight: 1.32,
            fontWeight: 800,
            textShadow: "0 4px 18px rgba(0,0,0,0.95)",
          }}
        >
          {te}
        </div>
        <div
          style={{
            marginTop: 10,
            color: "rgba(255,241,219,0.78)",
            fontSize: 28,
            lineHeight: 1.28,
            fontWeight: 500,
            letterSpacing: 0.2,
          }}
        >
          {en}
        </div>
      </div>
    </AbsoluteFill>
  );
};

/** The chant, big and centred, before any picture arrives. */
const ChantOpen: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame: frame - 4, fps, config: { damping: 22, mass: 0.8 } });
  const out = interpolate(frame, [F(2.9), F(3.3)], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      <div
        style={{
          opacity: Math.min(s, out),
          transform: `scale(${interpolate(s, [0, 1], [0.94, 1])})`,
          textAlign: "center",
          padding: "0 70px",
        }}
      >
        <div style={{ color: "#F2B631", fontSize: 76, fontWeight: 900, lineHeight: 1.25 }}>
          కొమురవెల్లి మల్లన్నకు
        </div>
        <div style={{ color: PALETTE.bone, fontSize: 92, fontWeight: 900, marginTop: 14, lineHeight: 1.2 }}>
          కోటి దండాలు
        </div>
      </div>
    </AbsoluteFill>
  );
};

/** Location pin — spoken in the narration, shown here for sound-off viewers. */
const LocationPin: React.FC<{ duration: number }> = ({ duration }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame, fps, config: { damping: 20, mass: 0.6 } });
  const out = interpolate(frame, [duration - 14, duration], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return (
    <AbsoluteFill style={{ justifyContent: "flex-start", alignItems: "center", paddingTop: 150 }}>
      <div
        style={{
          opacity: Math.min(s, out),
          transform: `translateY(${interpolate(s, [0, 1], [-16, 0])}px)`,
          background: "rgba(14,9,7,0.70)",
          border: "2px solid rgba(242,182,49,0.55)",
          borderRadius: 16,
          padding: "16px 26px",
          textAlign: "center",
        }}
      >
        <div style={{ color: "#F2B631", fontSize: 36, fontWeight: 800 }}>
          కొమురవెల్లి మల్లన్న
        </div>
        <div style={{ color: PALETTE.bone, fontSize: 26, marginTop: 6, fontWeight: 600 }}>
          సిద్దిపేట జిల్లా · హైదరాబాద్ నుంచి 85 కి.మీ.
        </div>
      </div>
    </AbsoluteFill>
  );
};

/** The one card of the part, at the hinge: the condition. */
const ConditionCard: React.FC<{ duration: number }> = ({ duration }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame, fps, config: { damping: 18, mass: 0.7 } });
  const out = interpolate(frame, [duration - 12, duration], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      <div
        style={{
          opacity: Math.min(s, out),
          transform: `scale(${interpolate(s, [0, 1], [0.92, 1])})`,
          background: "rgba(10,7,5,0.82)",
          border: "3px solid rgba(242,182,49,0.85)",
          borderRadius: 10,
          padding: "26px 46px",
          textAlign: "center",
        }}
      >
        <div style={{ color: "#F2B631", fontSize: 64, fontWeight: 900 }}>పసుపు కొమ్ములు</div>
        <div style={{ color: "rgba(255,241,219,0.8)", fontSize: 26, marginTop: 10, letterSpacing: 1 }}>
          the turmeric horns
        </div>
      </div>
    </AbsoluteFill>
  );
};

/** Next-part pin, at the very end. */
const NextPin: React.FC<{ duration: number }> = ({ duration }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame, fps, config: { damping: 20, mass: 0.6 } });
  const out = interpolate(frame, [duration - 10, duration], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return (
    <AbsoluteFill style={{ justifyContent: "flex-start", alignItems: "center", paddingTop: 150 }}>
      <div
        style={{
          opacity: Math.min(s, out),
          transform: `translateY(${interpolate(s, [0, 1], [-14, 0])}px)`,
          background: "rgba(14,9,7,0.72)",
          border: "2px solid rgba(242,182,49,0.5)",
          borderRadius: 16,
          padding: "14px 26px",
          textAlign: "center",
        }}
      >
        <div style={{ color: "#F2B631", fontSize: 34, fontWeight: 800 }}>
          రెండో భాగం — వచ్చే ఆదివారం
        </div>
      </div>
    </AbsoluteFill>
  );
};

export const Ep01Part1Captions: React.FC = () => {
  const frame = useCurrentFrame();
  // a short dip to black on each picture cut, so joins read as edits
  const dip = CUTS.reduce((acc, c) => {
    const d = Math.abs(frame - c);
    return Math.max(acc, d < 3 ? 1 - d / 3 : 0);
  }, 0);

  return (
    <AbsoluteFill>
      <AbsoluteFill style={{ backgroundColor: "#000", opacity: dip * 0.8 }} />

      <Sequence from={0} durationInFrames={F(3.4)} name="chant">
        <ChantOpen />
      </Sequence>

      <Sequence from={F(5.6)} durationInFrames={F(4.4)} name="pin">
        <LocationPin duration={F(4.4)} />
      </Sequence>

      <Sequence from={F(33.9)} durationInFrames={F(2.6)} name="card-condition">
        <ConditionCard duration={F(2.6)} />
      </Sequence>

      <Sequence from={F(62.0)} durationInFrames={EP01_FRAMES - F(62.0)} name="pin-next">
        <NextPin duration={EP01_FRAMES - F(62.0)} />
      </Sequence>

      {CAPTIONS.map((c, i) => (
        <Sequence key={i} from={c.from} durationInFrames={c.to - c.from} name={`cap${i + 1}`}>
          <Caption te={c.te} en={c.en} duration={c.to - c.from} />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};
