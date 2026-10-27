"""Running summary: how a long meeting turns into a full summary, chunk by chunk.

Main point: the summary grows from chunk to chunk.
Three zones, each with its own pattern:
  1. slicing — timeline strip of the meeting with overlapping tails;
  2. one step — convergence → model → real answer → filter → log;
  3. growth — growing summary circles and a growing log.

Run: python3 meeting_summary.py [out.excalidraw]
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))
from scene import _base, rect, text, arrow, box, connect, text_width, save

INK, MUTED = "#1e1e1e", "#868e96"
VIOLET, VIOLET_BG = "#6741d9", "#d0bfff"
ORANGE, ORANGE_BG = "#e8590c", "#ffd8a8"
YELLOW_BG, GREEN, GREEN_BG, PINK_BG = "#ffec99", "#2f9e44", "#b2f2bb", "#fcc2d7"
E = []


def ellipse(x, y, w, h, fill="transparent", stroke=INK, **kw):
    return _base(type="ellipse", x=x, y=y, width=w, height=h, backgroundColor=fill,
                 strokeColor=stroke, roundness=None, **kw)


def diamond(x, y, w, h, fill="transparent", stroke=INK, **kw):
    return _base(type="diamond", x=x, y=y, width=w, height=h, backgroundColor=fill,
                 strokeColor=stroke, roundness={"type": 2}, **kw)


def line(pts, color=INK, **kw):
    x0, y0 = pts[0]
    return _base(type="line", x=x0, y=y0, points=[[px - x0, py - y0] for px, py in pts],
                 width=max(p[0] for p in pts) - x0, height=max(p[1] for p in pts) - y0,
                 strokeColor=color, roundness={"type": 2}, startBinding=None,
                 endBinding=None, startArrowhead=None, endArrowhead=None, **kw)


def curve(pts, color=INK, dashed=False, **kw):
    """Arrow through several points — Excalidraw smooths it into a curve."""
    x0, y0 = pts[0]
    head = kw.pop("endArrowhead", "arrow")
    a = arrow(x0, y0, *pts[-1], color=color, **kw)
    a["endArrowhead"] = head
    a["points"] = [[px - x0, py - y0] for px, py in pts]
    a["strokeStyle"] = "dashed" if dashed else "solid"
    return a


def label(x, y, s, size=16, color=INK, **kw):
    E.append(text(x, y, s, font_size=size, color=color, **kw))


def center_text(cx, y, s, size=16, color=INK):
    label(cx - text_width(s, size) / 2, y, s, size, color, align="center")


def section(y, num, title):
    label(40, y, f"{num}", 36, MUTED)
    label(80, y + 8, title, 22)


# ── Title ───────────────────────────────────────────────────────────────
label(40, 20, "How a meeting becomes the \"Full summary\"", 28)
label(40, 60, "the model reads one chunk at a time, the summary grows step by step", 16, MUTED)

# ── 1. Slicing: the meeting as a time strip ───────────────────────────────
section(110, 1, "Slicing: a 3 h 32 min meeting, 550 paragraphs, 149k characters")
X0, X1, BY, BH = 60, 1040, 170, 44
seg = (X1 - X0) / 8
times = ["0:00", "0:27", "0:54", "1:21", "1:48", "2:15", "2:41", "3:05", "3:32"]
for i in range(8):
    x = X0 + i * seg
    E.append(rect(x, BY, seg, BH, fill=YELLOW_BG, fillStyle="solid", roundness=None))
    center_text(x + seg / 2, BY + 12, f"chunk {i + 1}", 16)
    if i:  # tail of the previous chunk — hatched overlap
        E.append(rect(x - 22, BY - 8, 22, BH + 16, fill=ORANGE, stroke=ORANGE,
                      fillStyle="hachure", roundness=None))
for i, t in enumerate(times):
    x = X0 + i * seg
    E.append(line([(x, BY + BH), (x, BY + BH + 8)], color=MUTED))
    center_text(x, BY + BH + 12, t, 14, MUTED)
# annotation for the tail
label(X0 + seg + 60, BY + BH + 44, "overlap: last ~200 words of the previous chunk", 16, ORANGE)
E.append(curve([(X0 + seg + 56, BY + BH + 54), (X0 + seg + 10, BY + BH + 40), (X0 + seg - 8, BY + BH + 10)],
               color=ORANGE, strokeWidth=1))
label(X0, BY + BH + 84, "cut at paragraph boundaries, chunks of roughly equal length", 14, MUTED)

# ── 2. One step: assembling the package────────────────────────────────────
S2 = 370
section(S2, 2, "Step k: what goes into the package and what happens to it")
inputs = [  # (text, dot color, constant?)
    ("instructions and rules", MUTED, True),
    ("meeting card", MUTED, True),
    ("where we are: chunk k of 8, time", INK, False),
    ("summary after chunk k−1", VIOLET, False),
    ("open items from the log", ORANGE, False),
    ("tail of chunk k−1", ORANGE, False),
    ("text of chunk k with timecodes", "#f08c00", False),
]
IY = S2 + 60
label(60, IY - 6, "same every time", 14, MUTED)
dots, rows = [], []
for i, (s, c, const) in enumerate(inputs):
    y = IY + 22 + i * 34 + (0 if const else 26)
    if i == 2:
        label(60, y - 30, "changes from step to step", 14, MUTED)
    d = ellipse(60, y + 3, 14, 14, fill=c, stroke=c)
    E.append(d)
    label(84, y, s, 16, MUTED if const else INK)
    dots.append((84 + text_width(s, 16) + 8, y + 10))
    rows.append(y + 10)

# package — a stack of sheets
PX, PY, PW, PH = 400, S2 + 140, 120, 150
for k in (2, 1):
    E.append(rect(PX + 8 * k, PY - 8 * k, PW, PH, fill="#ffffff", roundness=None))
pack = box(PX, PY, PW, ["package", "for chunk k"], h=PH, fill=YELLOW_BG, font_size=18)
E += pack
for (x, y) in dots:
    E.append(curve([(x, y), ((x + PX) / 2 + 20, (y + PY + PH / 2) / 2), (PX - 6, PY + PH / 2)],
                   color=MUTED, strokeWidth=1, endArrowhead=None))

model = ellipse(570, PY + 30, 120, 90, fill=PINK_BG)
E.append(model)
center_text(630, PY + 62, "model", 20)
E.append(connect(pack[0], model))

# a real answer instead of a "model answer" box
CX, CY, CW = 740, S2 + 90, 310
code = ["[07:12] decision | …",
        "[15:40] task | who | due",
        "[12:30] question closed: …",
        "summary: what the meeting",
        "      is about so far"]
ch = 24 + len(code) * 24
card = rect(CX, CY, CW, ch, fill="#1e293b", stroke="#1e293b", roundness={"type": 3})
E.append(card)
for i, s in enumerate(code):
    c = "#d0bfff" if s.strip().startswith(("summary", "is about")) else "#e9ecef"
    t = text(CX + 16, CY + 12 + i * 24, s, font_size=16, color=c)
    t["fontFamily"] = 3
    t["width"] = len(s) * 16 * 0.64
    E.append(t)
label(CX, CY - 26, "model answer", 14, MUTED)
E.append(connect(model, card))

# code filter
flt = diamond(CX + 95, CY + ch + 50, 120, 90, fill="#e9ecef")
E.append(flt)
center_text(CX + 155, CY + ch + 84, "code", 18)
E.append(connect(card, flt))
label(CX + 225, CY + ch + 64, "duplicates by time — out", 14, MUTED)
label(CX + 225, CY + ch + 84, "time outside chunk — out", 14, MUTED)

# log — a storage cylinder
JX, JY = 560, CY + ch + 60
E.append(rect(JX, JY + 12, 120, 60, fill=ORANGE_BG, stroke=ORANGE_BG, roundness=None, strokeWidth=0))
E.append(ellipse(JX, JY + 60, 120, 24, fill=ORANGE_BG, stroke=ORANGE))
E.append(line([(JX, JY + 12), (JX, JY + 72)], color=ORANGE))
E.append(line([(JX + 120, JY + 12), (JX + 120, JY + 72)], color=ORANGE))
jtop = ellipse(JX, JY, 120, 24, fill="#fff4e6", stroke=ORANGE)
E.append(jtop)
center_text(JX + 60, JY + 34, "log", 18, ORANGE)
E.append(arrow(CX + 93, CY + ch + 95, JX + 126, JY + 45, color=ORANGE))

# ── 3. Growth ──────────────────────────────────────────────────────────
S3 = JY + 150
section(S3, 3, "Growth: the summary grows, the log accumulates")
LY = S3 + 150
E.append(line([(60, LY), (860, LY)], color=MUTED, strokeStyle="dotted"))
centers = []
for i in range(8):
    d = 26 + i * 9
    cx = 90 + i * 100
    E.append(ellipse(cx - d / 2, LY - d / 2, d, d, fill=VIOLET_BG, stroke=VIOLET))
    center_text(cx, LY + 50, f"summary {i + 1}", 14, VIOLET)
    # log under each circle — a bar that grows with the steps
    jh = 8 + i * 7
    E.append(rect(cx - 10, LY + 76, 20, jh, fill=ORANGE_BG, stroke=ORANGE, roundness=None))
    centers.append(cx)
for a, b in zip(centers, centers[1:]):
    E.append(arrow(a + 14, LY - 40, b - 14, LY - 40, color=VIOLET, strokeWidth=1))
label(60, LY - 78, "each summary = previous summary + new chunk", 16, VIOLET)

hero = ellipse(890, LY - 75, 170, 150, fill=GREEN_BG, stroke=GREEN, strokeWidth=3)
E.append(hero)
center_text(975, LY - 24, "Full", 22, INK)
center_text(975, LY + 4, "summary", 22, INK)
E.append(arrow(862, LY, 886, LY, color=GREEN, strokeWidth=3))
label(60, LY + 150, "log: decisions, tasks, questions with timecodes", 14, ORANGE)

# ── Feedback: along the left margin, into their list rows ────────────────
E.append(curve([(90, LY - 20), (30, LY - 120), (24, rows[3] + 40), (54, rows[3])],
               color=VIOLET, dashed=True, strokeWidth=2))
label(34, S3 + 40, "summary k → package k+1", 16, VIOLET)
E.append(curve([(JX - 4, JY + 50), (300, JY + 110), (40, JY + 40), (54, rows[4])],
               color=ORANGE, dashed=True, strokeWidth=2))
label(300, JY + 118, "open items → package k+1", 14, ORANGE)

out = save(sys.argv[1] if len(sys.argv) > 1 else "meeting_summary.excalidraw", E)
print(out, len(E), "elements")
