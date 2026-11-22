/** Locked palette — see design/style-guide.md. Two registers. */
export const PALETTE = {
  // Register 1: the remembered story. Dusk.
  turmeric: "#E8A33D",
  amber: "#C2702A",
  sienna: "#8E4A2E",
  indigo: "#2B2546",
  violet: "#5A4A72",
  bone: "#F2E4CE",
  vermillion: "#A32E2E",
  ink: "#1C1A22",
  // Register 2: the present-day temple, taken from the real murti.
  murtiBlue: "#1E4FA3",
  murtiGreen: "#1F8A4C",
  murtiMagenta: "#C2246B",
  murtiGold: "#F0B323",
} as const;

/** Which register a shot sits in — warmth tracks Mallanna's distance from home. */
export const SHOT_REGISTER: Record<1 | 2, ("dusk" | "cold" | "bright")[]> = {
  1: ["bright", "bright", "dusk", "dusk", "cold", "cold", "dusk", "cold", "dusk"],
  2: ["cold", "cold", "cold", "cold", "bright", "bright", "bright", "bright"],
};
