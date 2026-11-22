/**
 * Which image each shot shows, and how the camera moves on it.
 *
 * `move` is deliberately restrained. These are still illustrations: a slow push or
 * drift makes them feel alive, a fast one makes them feel like a slideshow with
 * effects. Only the four shots flagged in the style guide get a real move; the rest
 * sit nearly still so the moving ones land.
 */
export type Move = "still" | "push" | "pull" | "driftLeft" | "driftRight" | "riseUp";

export type Shot = {
  /** File under public/scenes, or null to fall back to the placeholder. */
  image: string | null;
  move: Move;
  /** Extra zoom headroom so a drift never exposes an edge. */
  overscan?: number;
};

export const SHOTS: Record<1 | 2, Shot[]> = {
  1: [
    { image: "p1-01-turmeric-hand.png", move: "push" },      // 1 chant
    { image: "p1-02-hill-dawn.png", move: "pull", overscan: 1.18 }, // 2 location
    { image: "p1-03-termite-mound.png", move: "riseUp", overscan: 1.16 }, // 3 origin
    { image: "p1-04-brothers.png", move: "push" },           // 4 the condition
    { image: "p1-05-serpent-guard.png", move: "push" },      // 5 the bandari
    { image: "p1-06-horse-night.png", move: "driftLeft", overscan: 1.2 }, // 6 setting out
    { image: "p1-07-gardener.png", move: "still" },          // 7 the long wait
    { image: "p1-08-the-theft.png", move: "push" },          // 8 the theft
    { image: "p1-01-turmeric-hand.png", move: "still" },     // 9 his hand / the ask
  ],
  2: [
    { image: "p1-08-the-theft.png", move: "push" },          // 1 chant + seen
    { image: "p2-02-black-dog.png", move: "driftLeft", overscan: 1.18 }, // 2 the dog
    { image: "p2-03-chase.png", move: "driftLeft", overscan: 1.22 },     // 3 the chase
    { image: "p2-04-ganga.png", move: "still" },             // 4 Ganga — see GANGA_AFTER
    { image: "p2-05-return-hill.png", move: "pull", overscan: 1.14 },    // 5 the return
    { image: "p2-06-oggu-priest.png", move: "push" },        // 6 the singer — see PATNAM
    { image: "p2-07-field.png", move: "riseUp", overscan: 1.16 },        // 7 the fields
    { image: "p1-01-turmeric-hand.png", move: "still" },     // 8 back to your hand
  ],
};

/**
 * Shots that cut to a second image partway through, as a fraction of the shot.
 * Part 2 shot 4 is the episode's peak: she blocks, the blow lands, and we come back
 * to her standing with the hand gone. Shot 6 turns from the singer to what he is
 * drawing — that reveal is the whole point of the ending.
 */
export const SECOND_IMAGE: Record<string, { at: number; image: string; blackout?: number }> = {
  "2-4": { at: 0.55, image: "p2-04b-ganga-after.png", blackout: 30 },
  "2-6": { at: 0.45, image: "p2-06b-patnam.png" },
};
