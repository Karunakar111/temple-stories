import React from "react";
import { AbsoluteFill } from "remotion";
import { PALETTE } from "../design/palette";

/**
 * The series signature. Identical position and design in every episode, inside the
 * first 16 seconds: temple, district, distance from Hyderabad. The narration says it
 * too — this is for the sound-off viewer.
 */
export const LocationPin: React.FC<{ part: 1 | 2 }> = ({ part }) => (
  <AbsoluteFill
    style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: 230 }}
  >
    <div
      style={{
        border: `3px solid ${PALETTE.murtiGold}`,
        borderRadius: 18,
        padding: "22px 40px",
        background: "rgba(28,26,34,0.82)",
        textAlign: "center",
      }}
    >
      <div style={{ color: PALETTE.murtiGold, fontSize: 44, fontWeight: 800, letterSpacing: 1 }}>
        కొమురవెల్లి మల్లన్న
      </div>
      <div style={{ color: PALETTE.bone, fontSize: 30, marginTop: 10, opacity: 0.95 }}>
        సిద్దిపేట జిల్లా · హైదరాబాద్ నుంచి 85 కి.మీ.
      </div>
      {part === 2 ? (
        <div style={{ color: PALETTE.turmeric, fontSize: 26, marginTop: 12, letterSpacing: 2 }}>
          రెండవ భాగం
        </div>
      ) : null}
    </div>
  </AbsoluteFill>
);
