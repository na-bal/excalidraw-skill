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

// After recomputing, container text may wrap onto extra lines and not fit
// vertically — the generator must make the frame wider; we don't resize it.
const overflow = after.filter((e) => e.type === "text" && !e.isDeleted && e.containerId &&
  byId.get(e.containerId) && byId.get(e.containerId).type !== "arrow" &&
  e.height > byId.get(e.containerId).height - 10 + 1);
if (overflow.length) {
  console.error(`does not fit its frame vertically: ${overflow.length}`);
  overflow.slice(0, 5).forEach((e) => console.error(`  ${e.text.slice(0, 50).replace(/\n/g, "⏎")}`));
}

if (check) process.exit(clipped.length || overflow.length ? 1 : 0);
scene.elements = after;
fs.writeFileSync(out || input, JSON.stringify(scene));
