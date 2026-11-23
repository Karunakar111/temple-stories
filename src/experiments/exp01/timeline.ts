/**
 * Experiment 01 timeline. All narration comes from the approved paced master
 * (audio/01-mallanna-full-paced.mp3); `offset` maps master seconds to output seconds.
 * Word times were measured from the master's energy envelope.
 */
export const FPS = 30;
export const DURATION_S = 22.8;
export const DURATION = Math.round(DURATION_S * FPS);

export const BEATS = {
  location: { a: 0, b: 6.4, master: [5.16, 10.21], at: 0.6 },
  time: { a: 6.4, b: 13.9, master: [37.49, 43.66], at: 6.7 },
  offering: { a: 13.9, b: 19.3, master: [69.72, 72.14], at: 14.9 },
  closing: { a: 19.3, b: DURATION_S, master: [105.21, 107.84], at: 19.6 },
} as const;

const off = (beat: keyof typeof BEATS) => BEATS[beat].at - BEATS[beat].master[0];
export const toOut = (beat: keyof typeof BEATS, masterS: number) => masterS + off(beat);

export const WORDS = {
  distance: toOut("location", 5.46), // హైదరాబాద్ నుంచి ఎనభై ఐదు కిలోమీటర్లు
  district: toOut("location", 8.27), // సిద్దిపేట జిల్లా
  place: toOut("location", 9.44), // కొమురవెల్లి
  someTime: toOut("time", 40.68), // కొంతకాలం …
  giveCut: toOut("offering", 71.1), // just before ఎల్లమ్మకిచ్చిండు
  closing1: toOut("closing", 105.41),
  closing2: toOut("closing", 106.91),
};

/**
 * Caption text = the spoken words (as corrected for Episode 1's final export).
 * Captions sit high (top 360) in this experiment so they never cover the hands or the water,
 * which is where the action is.
 */
export const CAPTIONS = [
  { a: toOut("time", 37.66), b: toOut("time", 39.19), text: "అక్కడ తోటమాలిగా చేరిండు", top: 360 },
  { a: toOut("time", 39.51), b: toOut("time", 40.34), text: "పేరు మార్చుకున్నాడు", top: 360 },
  { a: toOut("time", 40.68), b: toOut("time", 43.5), text: "కొంతకాలం అక్కడే ఉండి వాళ్ళ నమ్మకం గెలుచుకున్నాడు", top: 360 },
  { a: toOut("offering", 70.09), b: toOut("offering", 72.0), text: "బండారిల కొంత ఎల్లమ్మకిచ్చిండు", top: 360 },
];
