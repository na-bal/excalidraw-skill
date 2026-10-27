# Details

Everything below was confirmed by actually running it: a comparison of Excalidraw
tooling and a full generate-check-fix loop on a 173-element map. Only verified facts
are kept here.

## Why this pipeline

The agent has to **see what it drew and be able to fix it**. That rules out the
official `excalidraw-mcp`: it has no tool that reads the scene back, and
`export_to_excalidraw` is marked `visibility:["app"]` — a human calls it from the UI,
not the model. `mmd2excalidraw` was broken at the time of testing.

So the skill generates `.excalidraw` files directly, renders them in the real
Excalidraw editor in headless Chromium (Playwright, installed by `scripts/setup.sh`),
and publishes them with `scripts/board.py`. Requirements: Node 22+, Python 3.10+.

## Font metrics

`measureText` on the loaded Excalidraw 0.18.1 fonts, share of font size per character
(× fontSize = pixels):

| fontFamily | lowercase Cyrillic | UPPERCASE | Latin | m, w, Ж, Ш… |
| --- | --- | --- | --- | --- |
| 5 — Excalifont (default) | 0.52–0.56 | ~0.63 | ~0.48 | up to 0.67 |
| 1 — Virgil | 0.52–0.56 | ~0.63 | ~0.49 | up to 0.65 |
| 6 — Nunito | 0.52–0.55 | ~0.67 | ~0.45 | up to 0.79 |
| 8 — Comic Shanns | 0.49–0.53 | ~0.69 | 0.55 | 0.55 |

Note: 1 is Virgil, not Excalifont, and these are ceilings, not averages.
`scene.text_width()` rounds up with headroom: uppercase 0.68, Cyrillic 0.58,
Latin 0.52, wide letters 0.80.

## Text width and clipped letters

The rule "stored width doesn't affect rendering, Excalidraw re-measures on its own"
is **wrong for the Excalidraw editor** (both ExcaliDash and the local board). Some
import paths recompute dimensions, but the editor does not: it draws text into a box
of the stored width, and whatever doesn't fit is clipped at the edges. Centered text
gets clipped on both sides. In one audit, 18 of 24 boards had broken labels because
of this.

The fix is built into publishing: `board.py push` runs the scene through
`scripts/mmd/fittext.mjs`. It boots the real Excalidraw in headless Chromium, loads its
fonts and calls `restoreElements({refreshDimensions})`. If fittext fails, push does not
publish. Use `--no-fit` only deliberately.

`fittext.mjs file --check` checks without writing: how many labels are clipped, and
which text inside a container no longer fits vertically after re-measuring. In the
second case widen the container in the generator: fittext rewraps text but does not
move the container.

**To look at it, use `node scripts/mmd/shot.mjs scene.excalidraw out.png`.** It is a
screenshot of the real editor canvas, i.e. what the user will see. PNG from
`mmd.mjs --png` (an export) **does not show** clipping. For interactive viewing, open
the scene on the local board (`board.py open [id]`, http://127.0.0.1:3200).

## Containers

An earlier assessment said "don't use containers, text on top of a rectangle is more
predictable". **That's wrong — rechecked visually** on three variants side by side:

1. container, wrapping left to the engine — text **did not wrap**, a single line
   overflowed the box on both sides;
2. container, wrapping done by hand with `\n` — **best result**: Excalidraw centered
   the lines on both axes inside the box;
3. separate text element on top — works, but stuck to the top-left corner.

Only half of it was true: the engine really doesn't wrap text. But it doesn't wrap it
**in any variant**, and wrapping is computed with the formula from this file anyway.
Handing the text to a container gets you centering, double-click editing and moving
with the box without `groupIds` for free.

## ExcaliDash API (excalidash backend)

Tested against ExcaliDash 0.6.0. Configure `EXCALIDASH_URL` and `EXCALIDASH_API_KEY`
in `~/.config/excalidraw-skill/config`.

The key is sent as `Authorization: Bearer <key>`. Only `/api/drawings*` and
`/api/collections*` routes are allowed — this is hardcoded in the backend, the key
physically can't touch users or settings.

- `GET /api/drawings` — list.
- `GET /api/drawings/:id` — the full scene. `elements`, `appState`, `files` may arrive
  as JSON strings — `board.py` handles that.
- `POST /api/drawings` — create: `name`, `elements`, `appState`, `files`.
- `PUT /api/drawings/:id` — replace content, version goes up by one.
  **Version history is still recorded**: an API edit goes through the same path as a
  browser save and stores a snapshot of the previous state (verified in the database
  after `push --id`). The key can't read the history itself (`/history` returns 401) —
  view it in the UI.
- 0.6.0 has **no** `/summary` and `/elements` — those appeared later, in dev.
- The `preview` field (SVG) is filled by the frontend on a browser save. A board created
  via the API has no preview — **you can't see your work through the server**; use
  `shot.mjs` for that.

Board URL in the UI: `<EXCALIDASH_URL>/editor/<id>` (local backend:
`http://127.0.0.1:3200/#<id>`).
