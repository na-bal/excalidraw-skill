// Playwright lives outside the skill dir (installed by scripts/setup.sh), so a
// skill update or a symlinked install never loses it. Falls back to a local
// node_modules next to this file for development checkouts.
import { createRequire } from "node:module";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

export const HOME = process.env.EXCALIDRAW_SKILL_CACHE ||
  path.join(process.env.XDG_CACHE_HOME || path.join(os.homedir(), ".cache"), "excalidraw-skill");

function load() {
  const bases = [path.join(HOME, "node", "package.json"), import.meta.url];
  for (const base of bases) {
    try { return createRequire(base)("playwright-core"); } catch {}
  }
  // Name the paths: a different EXCALIDRAW_SKILL_CACHE looks like a missing install.
  console.error(`playwright-core not found, looked in:
  ${path.join(HOME, "node", "node_modules")}  (EXCALIDRAW_SKILL_CACHE=${process.env.EXCALIDRAW_SKILL_CACHE || "unset"})
  node_modules next to ${path.dirname(fileURLToPath(import.meta.url))}
Run scripts/setup.sh with the same EXCALIDRAW_SKILL_CACHE, or export the cache dir it installed to.`);
  process.exit(5);
}

export const { chromium } = load();
