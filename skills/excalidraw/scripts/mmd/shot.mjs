#!/usr/bin/env node
// Screenshot of a scene as the editor draws it (canvas), not an SVG export.
// The difference matters: export never clips text, the editor clips it to the
// element width. Clipped letters are only visible here.
//
//   node shot.mjs scene.excalidraw out.png [--width 1400] [--height 900]
//
// Fits the whole scene into the viewport; a smaller window won't give a
// close-up — crop the scene or use fittext.mjs --check.
import fs from "node:fs";
import { chromium } from "./pw.mjs";

const args = process.argv.slice(2);
const opt = (n, d) => { const i = args.indexOf(n); return i >= 0 ? Number(args.splice(i, 2)[1]) : d; };
const width = opt("--width", 1400), height = opt("--height", 900);
const [input, out] = args;
if (!input || !out) { console.error("usage: shot.mjs file.excalidraw out.png [--width N] [--height N]"); process.exit(2); }
const scene = JSON.parse(fs.readFileSync(input, "utf8"));
const V = "0.18.1", ASSETS = `https://cdn.jsdelivr.net/npm/@excalidraw/excalidraw@${V}/dist/prod/`;

const browser = await chromium.launch();
try {
  const page = await browser.newPage({ viewport: { width, height }, deviceScaleFactor: 2 });
  await page.setContent(`<!doctype html><meta charset=utf-8><link rel=stylesheet href="${ASSETS}index.css">
<style>.excalidraw .layer-ui__wrapper, .excalidraw .App-bottom-bar, .excalidraw .HintViewer,
.excalidraw .welcome-screen-center, .excalidraw .scroll-back-to-content { display: none !important }</style>
<body style="margin:0"><div id=h style="width:${width}px;height:${height}px"></div></body>`);
  await page.evaluate(async ([scene, V, ASSETS]) => {
    window.EXCALIDRAW_ASSET_PATH = ASSETS;
    const X = await import(`https://esm.sh/@excalidraw/excalidraw@${V}?deps=react@19.0.0,react-dom@19.0.0`);
    const React = (await import("https://esm.sh/react@19.0.0")).default;
    const { createRoot } = await import("https://esm.sh/react-dom@19.0.0/client");
    const api = await new Promise((ok) => createRoot(document.getElementById("h")).render(
      React.createElement(X.Excalidraw, {
        initialData: { elements: scene.elements, files: scene.files || {}, appState: { viewBackgroundColor: "#ffffff" } },
        // No toolbar, hints or zoom bar over the scene — only the editor canvas.
        viewModeEnabled: true, zenModeEnabled: true,
        excalidrawAPI: (a) => a && ok(a),
      })));
    await document.fonts.ready;
    api.scrollToContent(undefined, { fitToViewport: true, viewportZoomFactor: 0.95 });
  }, [scene, V, ASSETS]);
  await page.waitForTimeout(3000); // fonts and repaint
  await page.screenshot({ path: out });
  console.log(out);
} finally {
  await browser.close();
}
