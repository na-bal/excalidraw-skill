# Mermaid → board

Everything below was verified by running it on a sequence diagram of an ERP data
exchange (5 participants, 14 messages). The compaction recipe below took it from
2193 → 1021 px wide.

## How it works

`scripts/mmd/mmd.mjs` is the same converter as Excalidraw's "Mermaid to Excalidraw"
dialog (`@excalidraw/mermaid-to-excalidraw` 1.1.4 + `convertToExcalidrawElements` from
Excalidraw 0.18.1, as in ExcaliDash 0.6.0), but running in headless Chromium (from
Playwright, installed by `scripts/setup.sh`). No browser tab needed. Libraries are
loaded from a CDN, so network access is required.

```sh
node scripts/mmd/mmd.mjs diagram.mmd -o diagram.excalidraw --png diagram.png
scripts/board.py push diagram.excalidraw --name "Name"
```

Exit codes: `0` ok · `1` error or forbidden construct · `2` usage error ·
`3` wider than `--max-width` (1100 by default) — the file is written but needs
compacting. Always look at the PNG: counters don't catch labels overlapping arrows.
The PNG is an export and won't show clipped letters; the final check is `shot.mjs`
(see recipe.md).

Keep the `.mmd` next to the `.excalidraw` — it's the source, edits go there.

## What converts

- **flowchart, sequence, class** — into live shapes and arrows.
- **Everything else** (gantt, pie, er, state, mindmap, journey…) — **as a single
  image** that can't be edited on the board. The script says so in its output. Tell
  the user or draw it natively.

## Why the obvious doesn't work

- **The esm.sh build of mermaid ignores config**: `%%{init}%%`, frontmatter and the
  converter's `config` parameter are accepted, but the width doesn't change. That's
  why mermaid is loaded from the official jsdelivr build via an importmap. Don't
  "simplify" this.
- **A multi-line arrow label in a sequence diagram breaks the converter.** It takes
  labels from the SVG by message index; `<br>` or `wrap` produce several text nodes,
  the indices shift — labels overlap arrows, some arrows disappear. The script rejects
  such labels and a global `sequence.wrap: true` by itself.
- **The converter leaves `<br>` in nodes and notes literally** — the script replaces it
  with a line break. It's allowed there.
- **Mermaid must lay out with Excalifont.** Otherwise it reserves space using its own
  font, and Excalifont is wider — note text overflows the boxes downward after
  rewrapping. The script preloads Excalifont and passes it to mermaid as `fontFamily`;
  the result also goes through `fitText`, so widths are exact.

## Making it compact

Target width is **up to ~1100 px**: readable on a laptop without horizontal scrolling.
Grow downward, not sideways.

### Sequence diagram

Width is driven by **arrow labels**: the gap between adjacent participants stretches to
fit the longest label between them. So:

1. First line:
   `%%{init: {"sequence": {"width": 120, "actorMargin": 40, "noteMargin": 8}}}%%`.
2. **Arrow label — 1–3 words, up to ~20 characters, one line.** What exactly is sent
   goes into a note under the arrow:
   ```
   R->>S: optin
   Note over R,S: wrap:phone, card, store, items
   ```
3. **Notes use `wrap:`** and span a **pair of adjacent** participants
   (`Note over S,A:`), not one: over a single one with `width: 120` you get a narrow
   tall column.
4. **Participant order** — those who talk most sit next to each other. A long label is
   fine on an arrow that already spans several participants.
5. A participant that appears in only one message is a candidate for merging or moving
   into a note.

Cosmetics we don't fix: mermaid wraps note text by its own metrics, then Excalidraw
rewraps it in Excalifont, so a line sometimes touches the box border.

### Flowchart

- Long chain — `flowchart TD`, not `LR`.
- Long node text — break with `<br>` into lines of 2–4 words.
- Edge labels — short; explanations go into a separate node or the node text.
- Parallel branches — `subgraph` with `direction TB` so they don't sprawl sideways.
