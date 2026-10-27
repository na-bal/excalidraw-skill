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
The table is coarse: digits (0.43–0.70, "2" is 0.70), "T" 0.86, "$" 0.72, "%" and
"—" 0.93, arrows 1.0 don't fit the letter classes. `scene.text_width()` uses a
per-character table of measured Excalifont widths, each rounded up to a bucket
(≤6% step); unknown letters fall back to 0.72 (0.88 uppercase), emoji/CJK to 1.1.
It is an upper bound: on ~530 labels from 13 sample scenes fittext never had to
widen one, and the estimate is ~4% wider on average (max 10%).

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
move the container. Excalidraw wraps container text to the shape's inner box, not its
bounding box: about `w·0.71` for an ellipse and `w/2` for a diamond (minus 10px
padding), same for height. fittext warns `rewrapped to more lines than written` with
the label when that adds lines — widen the shape; the vertical check uses the same
inner height.

**To look at it, use `node scripts/mmd/shot.mjs scene.excalidraw out.png`.** It is a
screenshot of the real editor canvas, i.e. what the user will see, with the editor
UI (toolbar, hints, zoom bar) hidden so it doesn't cover titles and legends. PNG from
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
