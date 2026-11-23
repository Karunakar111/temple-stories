// Separate entry point for episode previews and films; never touches src/Root.tsx or EP01.
// Preview (cloud): npx remotion render src/preview/index.ts EpisodePreview out.mp4 --props=build/ep02-preview/props.json
// Film:            python3 -m gudi film <episode>   (gudi/render.py writes props and calls Remotion)
import React from "react";
import { Composition, registerRoot } from "remotion";
import { EpisodePreview, PreviewProps } from "./EpisodePreview";
import { EpisodeFilm, FilmProps } from "./EpisodeFilm";

const meta = (fallback: number) => ({ props }: { props: Record<string, unknown> }) => ({
  durationInFrames: Math.ceil(((props as unknown as { total_s?: number }).total_s || fallback) * 30),
});

const Root: React.FC = () =>
  React.createElement(
    React.Fragment,
    null,
    React.createElement(Composition, {
      id: "EpisodePreview",
      component: EpisodePreview as React.FC<Record<string, unknown>>,
      fps: 30,
      width: 1080,
      height: 1920,
      durationInFrames: 300,
      defaultProps: { episode: "none", revision: "", timing: "", total_s: 10, music: "", shots: [] } as unknown as Record<string, unknown>,
      calculateMetadata: meta(10),
    }),
    React.createElement(Composition, {
      id: "EpisodeFilm",
      component: EpisodeFilm as React.FC<Record<string, unknown>>,
      fps: 30,
      width: 1080,
      height: 1920,
      durationInFrames: 300,
      defaultProps: { episode: "none", title: [], total_s: 10, narration: "", music: null, label: null, shots: [] } as unknown as Record<string, unknown>,
      calculateMetadata: meta(10),
    }),
  );

export type { PreviewProps, FilmProps };
registerRoot(Root);
