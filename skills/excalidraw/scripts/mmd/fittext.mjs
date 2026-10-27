#!/usr/bin/env node
// Recompute text sizes in an .excalidraw file with the real Excalidraw fonts.
// Without this the editor clips the edge letters of labels (see page.mjs).
//
//   node fittext.mjs scene.excalidraw [-o out.excalidraw] [--check]
//
// --check writes nothing, only counts clipped labels; exits 1 if there are any.
import fs from "node:fs";
import { withExcalidraw } from "./page.mjs";

const args = process.argv.slice(2);
const check = args.includes("--check");
const oi = args.indexOf("-o");
const out = oi >= 0 ? args[oi + 1] : null;
const input = args.find((a, i) => !a.startsWith("-") && args[i - 1] !== "-o");
if (!input) { console.error("usage: fittext.mjs file.excalidraw [-o out] [--check]"); process.exit(2); }

const scene = JSON.parse(fs.readFileSync(input, "utf8"));
const before = scene.elements;
const after = await withExcalidraw((page) => page.evaluate((els) => window.fitText(els), before));

const byId = new Map(after.map((e) => [e.id, e]));
const clipped = before.filter((e) => e.type === "text" && !e.isDeleted && byId.get(e.id)?.width > e.width + 1);
console.log(`${input}: ${before.filter((e) => e.type === "text" && !e.isDeleted).length} labels, ${clipped.length} clipped`);
clipped.slice(0, 5).forEach((e) => console.log(`  ${Math.round(e.width)} → ${Math.round(byId.get(e.id).width)}  ${e.text.slice(0, 40).replace(/\n/g, "⏎")}`));

// Inner box Excalidraw wraps bound text into (getBoundTextMaxWidth/Height in
// 0.18): an ellipse keeps the inscribed rectangle (side·√2/2), a diamond half
// of each side, minus 5px padding on both sides.
const inner = (c, side) => (c.type === "ellipse" ? Math.round(side / 2 * Math.SQRT2)
  : c.type === "diamond" ? Math.round(side / 2) : side) - 10;
const lines = (t) => (t || "").split("\n").length;
const label = (e) => (e.originalText || e.text).slice(0, 50).replace(/\n/g, "⏎");
const bound = after.filter((e) => e.type === "text" && !e.isDeleted && e.containerId &&
  byId.get(e.containerId) && byId.get(e.containerId).type !== "arrow");

// Excalidraw rewraps container text to the inner width on its own: more lines
// than the author wrote means the shape is too narrow for the label.
const prev = new Map(before.map((e) => [e.id, e]));
const rewrapped = bound.filter((e) => lines(e.text) > lines(prev.get(e.id)?.originalText ?? prev.get(e.id)?.text));
if (rewrapped.length) {
  console.error(`rewrapped to more lines than written: ${rewrapped.length} — widen the shape`);
  rewrapped.slice(0, 5).forEach((e) => { const c = byId.get(e.containerId);
    console.error(`  ${c.type} ${Math.round(c.width)} wide (text ${inner(c, c.width)}): ${lines(prev.get(e.id).originalText ?? prev.get(e.id).text)} → ${lines(e.text)} lines  ${label(e)}`); });
}

// After recomputing, container text may wrap onto extra lines and not fit
// vertically — the generator must make the frame bigger; we don't resize it.
const overflow = bound.filter((e) => e.height > inner(byId.get(e.containerId), byId.get(e.containerId).height) + 1);
if (overflow.length) {
  console.error(`does not fit its frame vertically: ${overflow.length}`);
  overflow.slice(0, 5).forEach((e) => { const c = byId.get(e.containerId);
    console.error(`  ${c.type} inner height ${inner(c, c.height)}, text ${Math.round(e.height)}: ${label(e)}`); });
}

if (check) process.exit(clipped.length || overflow.length ? 1 : 0);
scene.elements = after;
fs.writeFileSync(out || input, JSON.stringify(scene));
