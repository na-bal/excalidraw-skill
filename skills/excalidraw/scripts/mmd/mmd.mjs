#!/usr/bin/env node
// Mermaid → .excalidraw without a browser tab: the same converter as the
// "Mermaid to Excalidraw" dialog (parseMermaidToExcalidraw + convertToExcalidrawElements),
// but in headless Chromium. Also renders a PNG preview to check the result.
//
//   node mmd.mjs diagram.mmd [-o diagram.excalidraw] [--png diagram.png] [--max-width 1100]
//
// The gotcha behind this setup: the esm.sh mermaid build ignores config
// (%%{init}%%, sequence.width, etc.) — width doesn't change. So mermaid comes from
// the official jsdelivr build via importmap, and the converter from esm.sh with
// `external=mermaid`. Versions are pinned to those in ExcaliDash 0.6.0.
import fs from "node:fs";
import path from "node:path";
import { withExcalidraw, CONVERTER } from "./page.mjs";

const args = process.argv.slice(2);
const opt = (name) => { const i = args.indexOf(name); return i >= 0 ? args.splice(i, 2)[1] : undefined; };
const out = opt("-o");
const png = opt("--png");
const maxWidth = Number(opt("--max-width") || 1100);
const input = args[0];
if (!input) { console.error("usage: mmd.mjs file.mmd [-o out.excalidraw] [--png out.png] [--max-width N]"); process.exit(2); }
const src = fs.readFileSync(input, "utf8");
const outPath = out || input.replace(/\.(mmd|mermaid|md)$/i, "") + ".excalidraw";

// The converter takes arrow labels from the SVG by message index. A multi-line label
// (<br> or wrap) yields several text nodes, indexes shift — arrows disappear and
// labels overlap. Line breaks only in notes (`Note …: wrap:…`).
const isSeq = /^\s*sequenceDiagram/m.test(src);
const msgRe = /^\s*[^%\s][^:]*?(-{1,2}>>|-{1,2}>|-{1,2}x|-{1,2}\))\+?-?[^:]*:(.*)$/;
const messages = isSeq ? src.split("\n").filter((l) => msgRe.test(l) && !/^\s*Note\b/i.test(l)) : [];
if (isSeq) {
  const bad = messages.filter((l) => /<br\s*\/?>|:\s*wrap:/i.test(l));
  const globalWrap = /"wrap"\s*:\s*true|^\s*wrap\s*:\s*true/m.test(src);
  if (bad.length || globalWrap) {
    console.error("Multi-line arrow labels break the converter. Shorten the label, put details in a Note with wrap:.");
    bad.forEach((l) => console.error("  " + l.trim()));
    if (globalWrap) console.error("  global sequence.wrap: true — remove it, use wrap: only in notes");
    process.exit(1);
  }
}

await withExcalidraw(async (page) => {
  const res = await page.evaluate(async ([src, CONVERTER, wantPng]) => {
    const M = await import(CONVERTER);
    const X = window.X;
    // Mermaid lays out by its own font metrics. If left as is, Excalifont in the
    // final scene is wider and labels overflow note frames. So we load the
    // Excalidraw font up front and hand it to mermaid for layout.
    const FONT_FAMILY = X.FONT_FAMILY.Excalifont;
    await window.loadFonts(FONT_FAMILY, src);
    const font = window.fontString(FONT_FAMILY);
    const cfg = { fontFamily: font, themeVariables: { fontFamily: font } };
    let r;
    // Like the Excalidraw dialog: on parse error, retry with " replaced by '.
    try { r = await M.parseMermaidToExcalidraw(src, cfg); }
    catch { r = await M.parseMermaidToExcalidraw(src.replace(/"/g, "'"), cfg); }
    // The converter leaves <br> in node and note text literally — turn it into a newline.
    const br = (s) => (typeof s === "string" ? s.replace(/<br\s*\/?>/gi, "\n") : s);
    for (const e of r.elements) { e.text = br(e.text); if (e.label) e.label.text = br(e.label.text); }
    const elements = await window.fitText(X.convertToExcalidrawElements(r.elements, { regenerateIds: true }));
    const files = r.files || {};
    if (wantPng) {
      const svg = await X.exportToSvg({ elements, files, appState: { exportBackground: true, viewBackgroundColor: "#ffffff" }, exportPadding: 20 });
      svg.id = "preview";
      document.body.append(svg);
    }
    return { elements, files };
  }, [src, CONVERTER, Boolean(png)]);

  const els = res.elements;
  if (!els.length) throw new Error("converter returned an empty scene");
  fs.writeFileSync(outPath, JSON.stringify({
    type: "excalidraw", version: 2, source: "mermaid",
    elements: els, appState: { viewBackgroundColor: "#ffffff", gridSize: null }, files: res.files,
  }));
  if (png) {
    await page.waitForTimeout(800); // let SVG fonts finish loading
    await page.locator("#preview").screenshot({ path: png });
  }

  const x0 = Math.min(...els.map((e) => e.x)), x1 = Math.max(...els.map((e) => e.x + e.width));
  const y0 = Math.min(...els.map((e) => e.y)), y1 = Math.max(...els.map((e) => e.y + e.height));
  const w = Math.round(x1 - x0), h = Math.round(y1 - y0);
  const kinds = els.some((e) => e.type === "image") && els.length <= 2 ? " — THIS IS AN IMAGE, this diagram type doesn't convert to shapes" : "";
  console.log(`${path.basename(outPath)}: ${els.length} elements, ${w}×${h}${kinds}`);

  let code = 0;
  if (isSeq) {
    const arrows = els.filter((e) => e.type === "arrow").length;
    if (arrows < messages.length) { console.error(`${arrows} arrows for ${messages.length} messages — some were lost`); code = 1; }
  }
  if (w > maxWidth) { console.error(`wider than ${maxWidth} px — compress it (see references/mermaid.md)`); code = code || 3; }
  process.exitCode = code;
});
