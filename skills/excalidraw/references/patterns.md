# Plan and patterns

A diagram should **prove a point**, not lay out boxes. Monotony is fixed not by
the palette but by choosing a pattern before writing code. Sketches of every
pattern below live in `examples/skill_map.py` — run it and look at the result.

## The plan — four moves, before the generator

The plan ends up as the docstring at the top of the generator: the point, the
zones, the pattern for each zone. It takes seconds, not a render; don't skip it.

1. **The main point in one sentence.** What the diagram proves. Example: "the
   summary grows chunk by chunk". If you can't phrase it, it's too early to draw.
2. **The question type** sets the overall form (Dan Roam):
   who/what → portrait · how much → chart · where → map · when → timeline ·
   how → flow · why → comparison.
3. **Concept → pattern.** Each major concept gets its own pattern from the
   vocabulary below. **Two identical patterns in one diagram — reconsider.**
   A grid of identical cards is not a pattern.
4. **Zone sketch** — ASCII: which zones go where, width up to ~1100 px, grow downward.

## Checking the snapshot — not just for bugs

- **Isomorphism test:** if you erase all the text, does the structure still
  carry the idea? No — rework the shape, not the labels.
- **Five seconds:** is the main point readable at once? The most important
  thing is the largest, with the most empty space around it.
- **Frames on fewer than 30%** of labels. For each frame ask: would free text
  work here? Yes — remove the frame. Hierarchy comes from font size
  (28/22/16/14) and color.
- Arrows don't cut through other shapes, labels don't overlap, letters aren't clipped.
- 2–3 "fix → look" rounds. After that, tell the user what's still wrong.

## Metaphor vocabulary: what the concept does → how to draw it

| Concept | Pattern | How |
| --- | --- | --- |
| spawns many | fan-out | dot → 3 arrows → dots |
| gathers from many | convergence | inputs as free text with colored dots, curves converge into one |
| happens in order | timeline | line, dots, labels under them |
| repeats | ring | outlined ellipse with an arrowhead; return arrow along the margin |
| transforms | conveyor | ○○○ → [process] → □□□ |
| comparison | side by side | two columns, one axis |
| hierarchy | tree | lines and free text, no boxes |
| grows | growing row | circles/bars grow step by step |
| made of parts | assembly | stack of sheets, parts labeled outside |
| real data | code_card | `scene.code_card()` with real lines instead of an "Answer" box |
| detail up close | zoom callout | small circle on the object → lines → big circle |

## Notation catalog — what's already supported

Status: **M** — Mermaid, live shapes · **M-img** — Mermaid, image only ·
**by hand** — drawn before, no helper · **none**. Sketches of each are the
`sk_*` functions in `examples/skill_map.py`: 5–10 lines each, extend those into a helper.

**Engineering.** sequence — M · flowchart — M · state machine —
M-img · C4, zoom levels (nested frames + dashed lines to the zoomed one) — none ·
layers, stack (bands stacked vertically) — none · data flow, ETL (db → process →
db) — by hand · ER and classes — M-img (classes M) · network, deployment (cloud and
nodes as stamps) — none · request lifecycle (waterfall of offset bars) — none.

**Business.** swimlanes (horizontal lanes, steps zigzag) — none ·
2×2 matrix (crossed axes, one quadrant highlighted) — none · funnel, pyramid,
iceberg (`poly(closed=True)`) — none · customer journey (dashed stages + emotion
curve + emoji faces) — M-img · roadmap, Gantt (bars per lane + "today"
line) — M-img · org chart — M · flywheel (ring + dots on it) —
by hand · SWOT, canvas (2×2 grid by color) — none · Venn (ellipses with opacity 60) — none.

**Quantitative and explainers.** scale (bars from one axis, like "cost over
time") — by hand · bar chart — none · was → is — none · before / after — none ·
"problem → solution" bridge (two banks and an arc) — none · storyboard (frames +
character stamps) — none.

Turn a sketch into a helper **when the pattern is needed a second time**, not in advance.
Likely first: swimlanes, 2×2, layers, roadmap, state machine.

## Samples

- `examples/meeting_summary.py` — "running summary": timeline with overlaps,
  convergence into a package, code_card, diamond filter, growing row, feedback
  loops along the left margin.
- `examples/skill_map.py` — vertical conveyor of steps with stamps and a cost
  scale on the right; below — the plan timeline, the vocabulary, three tool
  columns and all catalog sketches.

Before a diagram type you haven't drawn yet, open the closest sample instead of
starting from an empty file.
