"""How the excalidraw skill works: steps on the left, time cost on the right.

Main point: cheap steps always, expensive ones only when needed.
Patterns: vertical conveyor with icons + cost bars + review loop.
Below: plan timeline, pattern vocabulary, tool columns and the notation catalog (sk_* sketches).

Run: python3 skill_map.py [out.excalidraw]
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))
from scene import _base, text, arrow, rect, text_width, save, wrap
from stamps import stamp

INK, MUTED = "#1e1e1e", "#868e96"
BLUE, ORANGE, ORANGE_BG, GREEN, VIOLET = "#1971c2", "#e8590c", "#ffd8a8", "#2f9e44", "#6741d9"
E = []


def label(x, y, s, size=16, color=INK):
    E.append(text(x, y, s, font_size=size, color=color))


def diamond(x, y, w, h, fill="#fff3bf"):
    d = _base(type="diamond", x=x, y=y, width=w, height=h, backgroundColor=fill,
              strokeColor=INK, roundness={"type": 2})
    E.append(d)
    label(x + w / 2 - 7, y + h / 2 - 14, "?", 22)
    return d


def curve(pts, color=INK, dashed=False, width=2):
    x0, y0 = pts[0]
    a = arrow(x0, y0, *pts[-1], color=color, strokeWidth=width)
    a["points"] = [[px - x0, py - y0] for px, py in pts]
    a["strokeStyle"] = "dashed" if dashed else "solid"
    E.append(a)


label(40, 20, "How the excalidraw skill works", 28)
label(40, 60, "cheap steps always, expensive ones only when there is no other way", 16, MUTED)

# cost column
CX = 800
label(CX, 100, "time cost", 16, MUTED)
E.append(_base(type="line", x=CX, y=130, points=[[0, 0], [0, 1010]], width=0, height=1010,
               strokeColor=MUTED, strokeStyle="dotted", roundness=None))


def cost(y, secs, note, color=BLUE, dashed=False):
    w = max(6, secs * 4)  # 1 s = 4 px, a minute = 240 px
    r = rect(CX, y, w, 22, fill=color if not dashed else "transparent", stroke=color,
             fillStyle="hachure" if dashed else "solid", roundness=None)
    E.append(r)
    label(CX + w + 10, y + 1, note, 14, color if dashed else MUTED)


# steps: (y, icon, title, captions, cost)
IX, TX = 60, 170
rows = {}


def step(y, icon, title, lines, icon_w=70, color=INK):
    E.extend(stamp(icon, IX, y, w=icon_w) if icon_w else [])
    label(TX, y, title, 22, color)
    for i, s in enumerate(lines):
        label(TX, y + 34 + i * 22, s, 16, MUTED)
    rows[title] = y


step(120, "person-talk", "1. Request", ["\"draw a diagram…\", \"put it on a board\", \"mermaid\""], icon_w=50)
cost(130, 0, "0")

# Mermaid fork
d1 = diamond(TX, 205, 70, 60)
label(TX + 90, 213, "said \"mermaid\" or sent code?", 16)
label(TX + 90, 236, "yes → mmd.mjs lays it out, straight to step 6", 14, MUTED)

step(300, "bulb", "2. Plan — before code", [
    "the main point in one sentence",
    "each concept gets its own pattern: timeline, assembly,",
    "loop, fan-out, before/after… no identical grids",
    "ASCII layout sketch, width up to ~1100 px",
], icon_w=60)
cost(310, 0.5, "seconds — it is thinking, not rendering")

step(470, "xxxdeveloper_icons:code", "3. Building the scene", [
    "scene.py: patterns, text without extra frames",
    "stamps: person, database, document, cloud — from libraries",
    "shape = meaning: model, storage, decision look different",
], icon_w=60)
cost(480, 2, "~2 s")

# image fork
d2 = diamond(TX, 590, 70, 60)
label(TX + 90, 598, "need a metaphor that no stamp covers?", 16)
label(TX + 90, 621, "no — skip (almost always)", 14, MUTED)

step(680, "magic", "4. Image via Codex (optional)", [
    "1–2 \"heroes\" per diagram, no more",
    "marker style, transparent background",
], icon_w=60, color=ORANGE)
cost(690, 60, "~1 min — only when needed", color=ORANGE, dashed=True)

step(800, "xxxdeveloper_icons:search", "5. Visual check", [
    "shot.mjs → editor PNG, look at it yourself",
    "clear without text? point readable in 5 seconds?",
    "arrows don't cut shapes, letters aren't clipped",
], icon_w=60)
cost(810, 10, "~10 s × round")

d3 = diamond(TX, 920, 70, 60)
label(TX + 90, 928, "anything to fix?", 16)
label(TX + 90, 951, "yes → back to building, at most 2–3 rounds", 14, MUTED)

step(1010, "send", "6. To the board", [
    "board.py push: fonts refitted, returns a board link",
], icon_w=60, color=GREEN)
cost(1020, 10, "~10 s")

# review loop — along the left margin
curve([(TX - 6, 950), (40, 900), (28, 700), (IX - 6, 510)], color=VIOLET, dashed=True)
# Mermaid shortcut — along the right edge of the text
curve([(TX + 90 + text_width("yes → mmd.mjs lays it out, straight to step 6", 14) + 8, 245), (745, 300), (750, 800), (TX + 420, 1020)], color=MUTED, dashed=True, width=1)

# totals, bottom right
label(CX, 1080, "regular diagram: ~30 s of work", 16, BLUE)
label(CX, 1104, "with images: +1 min each", 16, ORANGE)

# ════════════════════════════════════════════════════════════════════════
#  In detail: step 2 (plan) and step 3 (building)
# ════════════════════════════════════════════════════════════════════════
def ell(x, y, w, h, fill="transparent", stroke=INK, **kw):
    e = _base(type="ellipse", x=x, y=y, width=w, height=h, backgroundColor=fill,
              strokeColor=stroke, roundness=None, **kw)
    E.append(e)
    return e


def seg(x1, y1, x2, y2, color=INK, head=True, width=2):
    a = arrow(x1, y1, x2, y2, color=color, strokeWidth=width)
    if not head:
        a["endArrowhead"] = None
    E.append(a)


def dot(cx, cy, r=7, fill=INK):
    ell(cx - r, cy - r, 2 * r, 2 * r, fill=fill, stroke=fill)


E.append(_base(type="line", x=40, y=1170, points=[[0, 0], [1040, 0]], width=1040, height=0,
               strokeColor=MUTED, roundness=None))

# ── 2 in detail: plan ─────────────────────────────────────────────────
P = 1200
E.extend(stamp("bulb", 40, P, w=46))
label(100, P + 4, "Step 2 in detail: deciding what to draw", 24)
label(100, P + 40, "in the skill: step 0 of the workflow and references/patterns.md", 16, GREEN)

# timeline of four moves
TY = P + 130
E.append(_base(type="line", x=60, y=TY, points=[[0, 0], [1000, 0]], width=1000, height=0,
               strokeColor=INK, roundness=None, strokeWidth=2))
moves = [
    ("main point", ["one sentence the", "diagram must prove"], "want"),
    ("question type", ["who · how much · where ·", "when · how · why", "→ portrait, chart, map,", "timeline, flow, comparison"], "want"),
    ("concept → pattern", ["each concept gets its", "own pattern, frames < 30%", "vocabulary — below"], "want"),
    ("zone sketch", ["ASCII: which zones where,", "width up to ~1100 px", "(width — already there)"], "partial"),
]
for i, (t, lines, st) in enumerate(moves):
    cx = 110 + i * 260
    dot(cx, TY, 9, BLUE if st != "want" else ORANGE)
    label(cx - 20, TY - 44, f"{chr(ord('a') + i)}) {t}", 18)
    for j, s in enumerate(lines):
        label(cx - 20, TY + 22 + j * 21, s, 14, MUTED)
label(60, TY + 120, "●", 14, ORANGE); label(80, TY + 120, "to build in", 14, ORANGE)
label(250, TY + 120, "●", 14, BLUE); label(270, TY + 120, "partly there", 14, BLUE)
label(430, TY + 120, "plan output — docstring at the top of the generator: point, zones, patterns", 14, MUTED)

# pattern vocabulary — mini sketches
VY = TY + 190
label(60, VY, "Pattern vocabulary: what the concept does → how to draw it", 18)
VY += 50
cells = ["spawns → fan-out", "gathers → convergence", "in order → timeline",
         "repeats → ring", "transforms → conveyor", "compares → side by side", "hierarchy → tree"]
for i, name in enumerate(cells):
    x0, y0 = 50 + i * 148, VY
    cx, cy = x0 + 60, y0 + 40
    if i == 0:
        dot(x0 + 15, cy)
        for dy in (-28, 0, 28):
            seg(x0 + 25, cy, x0 + 95, cy + dy, width=1); dot(x0 + 105, cy + dy, 6, VIOLET)
    elif i == 1:
        for dy in (-28, 0, 28):
            dot(x0 + 15, cy + dy, 6, VIOLET); seg(x0 + 25, cy + dy, x0 + 95, cy, width=1)
        dot(x0 + 105, cy)
    elif i == 2:
        seg(x0 + 5, cy, x0 + 115, cy, head=False)
        for k in range(4):
            dot(x0 + 15 + k * 30, cy, 6, BLUE)
    elif i == 3:
        ell(cx - 38, cy - 30, 76, 60, stroke=GREEN)
        a = arrow(cx + 38, cy + 2, cx + 36, cy + 14, color=GREEN, strokeWidth=2); E.append(a)
    elif i == 4:
        for k in range(3):
            ell(x0 + 2, cy - 30 + k * 22, 14, 14, stroke=MUTED)
        E.append(rect(x0 + 40, cy - 18, 36, 36, fill="#fff3bf", roundness=None))
        seg(x0 + 20, cy, x0 + 38, cy, width=1); seg(x0 + 78, cy, x0 + 96, cy, width=1)
        for k in range(3):
            E.append(rect(x0 + 100, cy - 30 + k * 22, 14, 14, stroke=BLUE, roundness=None))
    elif i == 5:
        E.append(rect(x0 + 5, cy - 28, 45, 56, fill="#ffc9c9", roundness=None))
        E.append(rect(x0 + 70, cy - 28, 45, 56, fill="#b2f2bb", roundness=None))
        label(x0 + 52, cy - 10, "vs", 14, MUTED)
    elif i == 6:
        dot(cx, cy - 28)
        for dx in (-45, 0, 45):
            seg(cx, cy - 22, cx + dx, cy + 20, head=False, width=1); dot(cx + dx, cy + 26, 6, BLUE)
    for j, part in enumerate(name.split(" → ")):
        label(x0 + 2, y0 + 90 + j * 20, part if j == 0 else "→ " + part, 14, INK if j else MUTED)

# ── 3 in detail: build ───────────────────────────────────────────────
A = VY + 190
E.append(_base(type="line", x=40, y=A - 30, points=[[0, 0], [1040, 0]], width=1040, height=0,
               strokeColor=MUTED, roundness=None))
E.extend(stamp("xxxdeveloper_icons:code", 40, A, w=44))
label(100, A + 4, "Step 3 in detail: build tools and where they slow down", 24)
label(100, A + 40, "scene.py holds the primitives; everything else is written per generator", 16, MUTED)

cols = [
    ("check", "works", GREEN, [
        "text_width + wrap — measure and wrap lines yourself, the engine doesn't wrap",
        "box — text inside a shape: centered, double-click to edit",
        "connect — an arrow bound to both shapes",
        "ellipse, diamond, poly, curve, code_card — shape primitives",
        "stamp() — icons from the bundled libraries",
        "fittext on push — letters don't get clipped",
        "shot.mjs — editor snapshot, ~10 s",
    ]),
    ("warning", "works, but costs time", ORANGE, [
        "all coordinates by hand — the main cost",
        "multi-point curves bound only at the ends — middle points stay put when shapes move",
        "no pre-render check: overlaps are caught by eye on the PNG",
    ]),
    ("magic", "could add", BLUE, [
        "layout helpers: column, row, timeline, converge, fan_out — code computes coordinates",
        "linter: arrow cuts a shape, frames > 30%, wider than 1100 px",
        "helpers for catalog sketches once a pattern is needed twice",
    ]),
]
CY0 = A + 100
for i, (icon, head, color, items) in enumerate(cols):
    x0 = 50 + i * 350
    E.extend(stamp(icon, x0, CY0, h=34))
    label(x0 + 46, CY0 + 4, head, 20, color)
    y = CY0 + 56
    for it in items:
        lines = wrap(it, 310, 15)
        dot(x0 + 6, y + 10, 4, color)
        for j, s in enumerate(lines):
            label(x0 + 20, y + j * 20, s, 15, INK if j == 0 else MUTED)
        y += len(lines) * 20 + 14

label(50, CY0 + 420, "Order: add a layout helper only when the same layout repeats in two diagrams.", 15, VIOLET)

# ════════════════════════════════════════════════════════════════════════
#  Pattern catalog: three groups, each with a sketch and a status
# ════════════════════════════════════════════════════════════════════════
RED = "#e03131"
ST = {"live": ("Mermaid, live shapes", BLUE), "pic": ("Mermaid, image only", ORANGE),
      "hand": ("drawn by hand, no helper", VIOLET), "no": ("none", RED)}


def poly(pts, fill="transparent", stroke=INK, width=2, **kw):
    x0, y0 = pts[0]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    e = _base(type="line", x=x0, y=y0, points=[[px - x0, py - y0] for px, py in pts],
              width=max(xs) - min(xs), height=max(ys) - min(ys), strokeColor=stroke,
              backgroundColor=fill, strokeWidth=width, roundness=None,
              startBinding=None, endBinding=None, startArrowhead=None, endArrowhead=None, **kw)
    E.append(e)


def R(x, y, w, h, fill="transparent", stroke=INK, **kw):
    E.append(rect(x, y, w, h, fill=fill, stroke=stroke, roundness=None, **kw))


def dia(x, y, w, h, fill="#fff3bf"):
    E.append(_base(type="diamond", x=x, y=y, width=w, height=h, backgroundColor=fill,
                   strokeColor=INK, roundness=None))


LB, LG, LY, LR, LV = "#a5d8ff", "#b2f2bb", "#ffec99", "#ffc9c9", "#d0bfff"


def sk_sequence(x, y):
    for ax in (x + 10, x + 80):
        R(ax, y, 30, 14, fill=LB)
        poly([(ax + 15, y + 14), (ax + 15, y + 70)], stroke=MUTED, width=1, strokeStyle="dashed")
    seg(x + 25, y + 30, x + 95, y + 30, width=1); seg(x + 95, y + 50, x + 25, y + 50, width=1)


def sk_flow(x, y):
    R(x + 40, y, 40, 14, fill=LB); dia(x + 45, y + 24, 30, 22)
    seg(x + 60, y + 14, x + 60, y + 24, width=1)
    seg(x + 45, y + 35, x + 20, y + 56, width=1); seg(x + 75, y + 35, x + 100, y + 56, width=1)
    R(x + 5, y + 56, 30, 14, fill=LG); R(x + 85, y + 56, 30, 14, fill=LR)


def sk_state(x, y):
    dot(x + 8, y + 35, 5)
    for cx in (x + 35, x + 90):
        ell(cx - 16, y + 20, 32, 30, fill=LV, stroke=VIOLET)
    seg(x + 13, y + 35, x + 18, y + 35, width=1)
    curve([(x + 50, y + 26), (x + 62, y + 14), (x + 75, y + 26)], width=1)
    curve([(x + 75, y + 46), (x + 62, y + 58), (x + 50, y + 46)], width=1)


def sk_c4(x, y):
    R(x + 5, y + 5, 50, 60, fill=LB); R(x + 70, y, 50, 70, stroke=MUTED)
    R(x + 78, y + 10, 34, 24, fill=LB); R(x + 78, y + 40, 34, 22, fill=LB)
    poly([(x + 55, y + 5), (x + 70, y)], stroke=MUTED, width=1, strokeStyle="dashed")
    poly([(x + 55, y + 65), (x + 70, y + 70)], stroke=MUTED, width=1, strokeStyle="dashed")


def sk_layers(x, y):
    for i, c in enumerate((LB, LY, LG)):
        R(x + 5, y + i * 24, 110, 20, fill=c)


def sk_etl(x, y):
    E.extend(stamp("db", x, y + 20, w=30)); R(x + 45, y + 22, 30, 26, fill=LY)
    E.extend(stamp("db", x + 90, y + 20, w=30))
    seg(x + 31, y + 35, x + 44, y + 35, width=1); seg(x + 76, y + 35, x + 89, y + 35, width=1)


def sk_er(x, y):
    for ex in (x + 5, x + 75):
        R(ex, y + 10, 40, 50, fill="#ffffff")
        poly([(ex, y + 24), (ex + 40, y + 24)], width=1)
    poly([(x + 45, y + 35), (x + 75, y + 35)], width=1)
    label(x + 48, y + 16, "1..*", 12, MUTED)


def sk_net(x, y):
    E.extend(stamp("cloud", x + 30, y + 18, w=60))
    for (px, py) in ((x, y), (x + 100, y), (x + 50, y + 58)):
        R(px, py, 18, 14, fill=LB)
    seg(x + 18, y + 10, x + 38, y + 22, head=False, width=1)
    seg(x + 100, y + 10, x + 82, y + 22, head=False, width=1)


def sk_waterfall(x, y):
    for i, (off, w, c) in enumerate(((0, 30, LB), (25, 50, LY), (70, 20, LG), (85, 30, LR))):
        R(x + 5 + off, y + 5 + i * 16, w, 12, fill=c)


def sk_swim(x, y):
    for i in range(3):
        R(x, y + i * 24, 120, 24, stroke=MUTED)
    R(x + 8, y + 5, 22, 14, fill=LB); R(x + 45, y + 29, 22, 14, fill=LY); R(x + 85, y + 53, 22, 14, fill=LG)
    seg(x + 30, y + 12, x + 50, y + 28, width=1); seg(x + 67, y + 36, x + 88, y + 52, width=1)


def sk_2x2(x, y):
    R(x + 60, y, 50, 35, fill=LG)
    poly([(x + 10, y + 35), (x + 110, y + 35)], width=2); poly([(x + 60, y), (x + 60, y + 70)], width=2)
    dot(x + 85, y + 17, 4, GREEN); dot(x + 30, y + 52, 4, MUTED)


def sk_funnel(x, y):
    poly([(x + 10, y), (x + 110, y), (x + 72, y + 45), (x + 72, y + 70), (x + 48, y + 70), (x + 48, y + 45), (x + 10, y)], fill=LB)
    poly([(x + 28, y + 22), (x + 92, y + 22)], width=1)


def sk_pyramid(x, y):
    poly([(x + 60, y), (x + 115, y + 70), (x + 5, y + 70), (x + 60, y)], fill=LY)
    poly([(x + 38, y + 28), (x + 82, y + 28)], width=1); poly([(x + 22, y + 50), (x + 98, y + 50)], width=1)


def sk_iceberg(x, y):
    poly([(x + 60, y), (x + 78, y + 22), (x + 42, y + 22), (x + 60, y)], fill="#ffffff")
    poly([(x + 42, y + 22), (x + 78, y + 22), (x + 105, y + 70), (x + 15, y + 70), (x + 42, y + 22)], fill=LB, stroke=BLUE)
    poly([(x, y + 22), (x + 120, y + 22)], stroke=BLUE, width=1, strokeStyle="dashed")


def sk_journey(x, y):
    for k in (40, 80):
        poly([(x + k, y), (x + k, y + 70)], stroke=MUTED, width=1, strokeStyle="dashed")
    curve([(x + 5, y + 40), (x + 30, y + 15), (x + 60, y + 60), (x + 95, y + 30), (x + 115, y + 10)], color=VIOLET, dashed=False)
    E[-1]["endArrowhead"] = None


def sk_gantt(x, y):
    for i, (off, w, c) in enumerate(((0, 60, LB), (40, 55, LY), (20, 90, LG))):
        R(x + 5 + off, y + 8 + i * 20, w, 12, fill=c)
    poly([(x + 70, y), (x + 70, y + 70)], stroke=RED, width=1)


def sk_org(x, y):
    R(x + 45, y, 30, 16, fill=LB)
    for dx in (5, 45, 85):
        R(x + dx, y + 50, 30, 16, fill=LY)
        poly([(x + 60, y + 16), (x + 60, y + 32), (x + dx + 15, y + 32), (x + dx + 15, y + 50)], width=1)


def sk_flywheel(x, y):
    ell(x + 25, y, 70, 70, stroke=GREEN)
    for (px, py) in ((x + 60, y - 4), (x + 92, y + 42), (x + 26, y + 42)):
        dot(px, py + 4, 5, GREEN)
    seg(x + 90, y + 20, x + 92, y + 30, color=GREEN); seg(x + 32, y + 56, x + 28, y + 46, color=GREEN)


def sk_swot(x, y):
    for i, c in enumerate((LG, LR, LB, LY)):
        R(x + 5 + (i % 2) * 55, y + (i // 2) * 35, 55, 35, fill=c)


def sk_venn(x, y):
    ell(x + 5, y + 5, 70, 60, fill=LB, stroke=BLUE, opacity=60)
    ell(x + 45, y + 5, 70, 60, fill=LY, stroke=ORANGE, opacity=60)


def sk_scale(x, y):
    poly([(x + 10, y), (x + 10, y + 70)], stroke=MUTED, width=1, strokeStyle="dotted")
    for i, w in enumerate((8, 20, 90, 30)):
        R(x + 10, y + 4 + i * 17, w, 11, fill=ORANGE if w > 60 else BLUE, stroke=ORANGE if w > 60 else BLUE)


def sk_bars(x, y):
    poly([(x + 5, y + 70), (x + 115, y + 70)], width=1)
    for i, h in enumerate((25, 45, 35, 65)):
        R(x + 15 + i * 25, y + 70 - h, 16, h, fill=LB, stroke=BLUE)


def sk_beforeafter_num(x, y):
    R(x + 10, y + 30, 30, 40, fill=LR); R(x + 80, y + 5, 30, 65, fill=LG)
    seg(x + 44, y + 40, x + 76, y + 30, color=GREEN)


def sk_zoom(x, y):
    R(x + 5, y + 30, 40, 30, fill=LY); ell(x + 25, y + 38, 12, 12, stroke=RED)
    ell(x + 62, y, 55, 55, stroke=RED)
    poly([(x + 36, y + 40), (x + 66, y + 12)], stroke=RED, width=1)
    poly([(x + 36, y + 49), (x + 70, y + 45)], stroke=RED, width=1)


def sk_before_after(x, y):
    R(x + 5, y + 10, 45, 50, stroke=MUTED); R(x + 70, y + 10, 45, 50, fill=LG)
    poly([(x + 12, y + 20), (x + 42, y + 50)], stroke=RED, width=1); poly([(x + 42, y + 20), (x + 12, y + 50)], stroke=RED, width=1)
    seg(x + 52, y + 35, x + 68, y + 35)


def sk_bridge(x, y):
    poly([(x, y + 35), (x + 30, y + 35), (x + 30, y + 70), (x, y + 70), (x, y + 35)], fill=LR)
    poly([(x + 90, y + 35), (x + 120, y + 35), (x + 120, y + 70), (x + 90, y + 70), (x + 90, y + 35)], fill=LG)
    curve([(x + 30, y + 35), (x + 60, y + 5), (x + 90, y + 35)], color=BLUE)
    E[-1]["endArrowhead"] = None


def sk_story(x, y):
    for i in range(3):
        R(x + 2 + i * 40, y + 15, 36, 40, stroke=INK)
    E.extend(stamp("person", x + 12, y + 20, h=30)); E.extend(stamp("bulb", x + 92, y + 22, h=28))
    E.extend(stamp("person-think", x + 50, y + 20, h=30))


groups = [
    ("Engineering", [
        ("sequence", sk_sequence, "live"), ("flowchart", sk_flow, "live"),
        ("state machine", sk_state, "pic"), ("C4: zoom levels", sk_c4, "no"),
        ("layers, stack", sk_layers, "no"), ("data flow, ETL", sk_etl, "hand"),
        ("ER and classes", sk_er, "pic"), ("network, deployment", sk_net, "no"),
        ("request lifecycle", sk_waterfall, "no"),
    ]),
    ("Business", [
        ("swimlanes", sk_swim, "no"), ("2×2 matrix", sk_2x2, "no"),
        ("funnel", sk_funnel, "no"), ("pyramid", sk_pyramid, "no"),
        ("iceberg", sk_iceberg, "no"), ("customer journey", sk_journey, "pic"),
        ("roadmap, Gantt", sk_gantt, "pic"), ("org chart", sk_org, "live"),
        ("flywheel", sk_flywheel, "hand"), ("SWOT, canvas", sk_swot, "no"),
        ("Venn", sk_venn, "no"),
    ]),
    ("Quantitative and explainers", [
        ("scale, ruler", sk_scale, "hand"), ("bar chart", sk_bars, "no"),
        ("was → is", sk_beforeafter_num, "no"), ("zoom callout", sk_zoom, "no"),
        ("before / after", sk_before_after, "no"), ("bridge: problem → solution", sk_bridge, "no"),
        ("storyboard", sk_story, "no"),
    ]),
]

K = CY0 + 500
E.append(_base(type="line", x=40, y=K - 30, points=[[0, 0], [1040, 0]], width=1040, height=0,
               strokeColor=MUTED, roundness=None))
label(40, K, "Pattern catalog: what is supported and what is not", 24)
label(40, K + 36, "metaphors (fan-out, conveyor, ring…) are in the vocabulary above; here — formal notations and business diagrams", 16, MUTED)
lx = 40
for key in ("live", "pic", "hand", "no"):
    t, c = ST[key]
    dot(lx + 6, K + 82, 6, c); label(lx + 18, K + 72, t, 15, c)
    lx += text_width(t, 15) + 50

y = K + 130
for gname, items in groups:
    label(40, y, gname, 20)
    y += 40
    for i, (name, fn, st) in enumerate(items):
        col, row = i % 7, i // 7
        x0, y0 = 45 + col * 148, y + row * 150
        fn(x0, y0)
        for j, part in enumerate(wrap(name, 135, 14)):
            label(x0, y0 + 84 + j * 18, part, 14)
        t, c = ST[st]
        dot(x0 + 5, y0 + 84 + 18 * len(wrap(name, 135, 14)) + 10, 4, c)
    y += ((len(items) - 1) // 7 + 1) * 150 + 20

label(40, y, "Live shapes for 3 of 27. First helper candidates: swimlanes, 2×2, layers, roadmap, state machine.", 16, VIOLET)

save(sys.argv[1] if len(sys.argv) > 1 else "skill_map.excalidraw", E)
print(len(E), "elements")
