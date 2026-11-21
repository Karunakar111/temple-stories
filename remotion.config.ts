/**
 * Note: When using the Node.JS APIs, the config file
 * doesn't apply. Instead, pass options directly to the APIs.
 *
 * All configuration options: https://remotion.dev/docs/config
 */

import { existsSync } from "node:fs";
import { Config } from "@remotion/cli/config";

Config.setRspack(true);
Config.setVideoImageFormat("jpeg");
Config.setOverwriteOutput(true);
Config.setDefaultPremountInSeconds(2);

/**
 * This machine runs macOS 12 (Monterey). Remotion 4.0.545 bundles a
 * chrome-headless-shell that links against macOS 15 VideoToolbox symbols, so it
 * cannot launch here (dyld: _kVTCompressionPropertyKey_ReferenceBufferCount).
 * The installed Google Chrome works, so point Remotion at it.
 * Override with REMOTION_BROWSER_EXECUTABLE if Chrome is elsewhere.
 * On macOS 15+ you can delete this block and use Remotion's bundled browser.
 */
const chromePath =
  process.env.REMOTION_BROWSER_EXECUTABLE ??
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";

if (existsSync(chromePath)) {
  Config.setBrowserExecutable(chromePath);
}

/**
 * Remotion's bundled FFmpeg (@remotion/compositor-darwin-x64) also needs
 * macOS 15 (it links _AVCaptureDeviceTypeContinuityCamera in AVFoundation), so
 * `remotion render out.mp4` cannot mux video on this machine. We render an
 * image sequence instead and mux with the project's own static FFmpeg.
 * See scripts/render.mjs and docs/SETUP_NOTES.md.
 */
