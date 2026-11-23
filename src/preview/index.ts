// Separate entry point for episode technical previews; never touches src/Root.tsx or EP01.
// Render (cloud):  npx remotion render src/preview/index.ts EpisodePreview out.mp4 --props=build/ep02-preview/props.json
// Render (Mac):    node scripts/render.mjs EpisodePreview --entry src/preview/index.ts --props build/ep02-preview/props.json
import React from "react";
import { Composition, registerRoot } from "remotion";
import { EpisodePreview, PreviewProps } from "./EpisodePreview";

const Root: React.FC = () =>
  React.createElement(Composition, {
    id: "EpisodePreview",
    component: EpisodePreview as React.FC<Record<string, unknown>>,
    fps: 30,
    width: 1080,
    height: 1920,
    durationInFrames: 300,
    defaultProps: { episode: "none", revision: "", timing: "", total_s: 10, music: "", shots: [] } as unknown as Record<string, unknown>,
    calculateMetadata: ({ props }: { props: Record<string, unknown> }) => ({
      durationInFrames: Math.ceil(((props as unknown as PreviewProps).total_s || 10) * 30),
    }),
  });

registerRoot(Root);
