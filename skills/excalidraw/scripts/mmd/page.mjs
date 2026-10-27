// Headless page with the real Excalidraw 0.18.1 (same as ExcaliDash 0.6.0).
//
// Why mount the whole component: Excalidraw fonts (Excalifont, Virgil…) are
// registered by App itself, in unicode-range chunks. Without them canvas measures
// text with a fallback font — about 10% narrower — and that width is stored in
// the element. The editor doesn't recompute it, it draws text into a box of the
// stored width, so the outer letters get clipped. That's why every scene goes
// through fitText before publishing — the same restoreElements({refreshDimensions}),
// but with the fonts loaded.
import { chromium } from "./pw.mjs";

const V = "0.18.1";
export const MERMAID = "https://cdn.jsdelivr.net/npm/mermaid@10.9.4/dist/mermaid.esm.min.mjs";
export const CONVERTER = "https://esm.sh/@excalidraw/mermaid-to-excalidraw@1.1.4?external=mermaid";
const EXCALIDRAW = `https://esm.sh/@excalidraw/excalidraw@${V}?deps=react@19.0.0,react-dom@19.0.0`;
const REACT = "https://esm.sh/react@19.0.0";
const REACT_DOM = "https://esm.sh/react-dom@19.0.0/client";
const ASSETS = `https://cdn.jsdelivr.net/npm/@excalidraw/excalidraw@${V}/dist/prod/`;

export async function withExcalidraw(fn) {
  const browser = await chromium.launch();
  try {
    const page = await browser.newPage();
    page.on("pageerror", (e) => console.error("[page]", e.message));
    // The esm.sh build of mermaid ignores config — use the official one via importmap.
    await page.setContent(`<!doctype html><meta charset=utf-8>
<script type=importmap>{"imports":{"mermaid":"${MERMAID}"}}</script>
<link rel=stylesheet href="${ASSETS}index.css"><body style="margin:0"></body>`);
    await page.evaluate(async ([EXCALIDRAW, REACT, REACT_DOM, ASSETS]) => {
      window.EXCALIDRAW_ASSET_PATH = ASSETS;
      const X = await import(EXCALIDRAW);
      const React = (await import(REACT)).default;
      const { createRoot } = await import(REACT_DOM);
      const host = document.createElement("div");
      host.style.cssText = "width:800px;height:600px;position:absolute;left:-9999px";
      document.body.append(host);
      await new Promise((ready) => createRoot(host).render(
        React.createElement(X.Excalidraw, { excalidrawAPI: (api) => api && ready() })));
      const NAMES = Object.fromEntries(Object.entries(X.FONT_FAMILY).map(([k, v]) => [v, k]));
      window.X = X;
      // Loads the font chunks needed for all scene text and recomputes text
      // dimensions: wrapping in containers, width, height, x/y by alignment.
      window.fontString = (fam) => `"${NAMES[fam] || "Excalifont"}", Xiaolai, "Segoe UI Emoji"`;
      window.loadFonts = async (fam, text) => {
        await document.fonts.load(`20px ${window.fontString(fam)}`, [...new Set(text)].join(""));
        await document.fonts.ready;
      };
      window.fitText = async (elements) => {
        const byFamily = {};
        for (const e of elements) if (e.type === "text" && !e.isDeleted) byFamily[e.fontFamily] = (byFamily[e.fontFamily] || "") + e.originalText + e.text;
        for (const [fam, s] of Object.entries(byFamily)) await window.loadFonts(fam, s);
        return X.restoreElements(elements, null, { refreshDimensions: true, repairBindings: true });
      };
    }, [EXCALIDRAW, REACT, REACT_DOM, ASSETS]);
    return await fn(page);
  } finally {
    await browser.close();
  }
}
