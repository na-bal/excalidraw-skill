// Playwright lives outside the skill dir (installed by scripts/setup.sh), so a
// skill update or a symlinked install never loses it. Falls back to a local
// node_modules next to this file for development checkouts.
import { createRequire } from "node:module";
import os from "node:os";
import path from "node:path";

export const HOME = process.env.EXCALIDRAW_SKILL_CACHE ||
  path.join(process.env.XDG_CACHE_HOME || path.join(os.homedir(), ".cache"), "excalidraw-skill");

function load() {
  for (const base of [path.join(HOME, "node", "package.json"), import.meta.url]) {
    try { return createRequire(base)("playwright-core"); } catch {}
  }
  console.error("playwright-core not found — run scripts/setup.sh first");
  process.exit(5);
}

export const { chromium } = load();
