// Separate entry point: the experiment never touches src/Root.tsx or any Episode 1 file.
// Render: npx remotion render src/experiments/exp01/index.ts Exp01Animation out.mp4
import { registerRoot } from "remotion";
import { Exp01Root } from "./Root";

registerRoot(Exp01Root);
