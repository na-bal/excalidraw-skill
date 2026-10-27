"""Builder for .excalidraw scenes. Imported by the generator of a specific diagram.

The main reason it exists: Excalidraw does not wrap text, so you have to
compute box widths yourself. The formula is checked against measureText on
Excalidraw fonts — see references/recipe.md.
"""
import json, math, secrets, time, unicodedata

FONT = 5                      # Excalidraw 0.18: 1 Virgil, 5 Excalifont, 6 Nunito, 8 Comic Shanns
LINE_HEIGHT = 1.25
BOUND_TEXT_PADDING = 5        # Excalidraw's own inset of container text, on each side
# Old class ratios (uppercase / Cyrillic / Latin / wide). No longer used by
# text_width(): they were averages, not ceilings — digits, "n", "$", "%" overflowed.
UPPER_RATIO, CYR_RATIO, LAT_RATIO, WIDE_RATIO = 0.68, 0.58, 0.52, 0.80
WIDE = set("mwMWжшщюыфЖШЩЮЫФ")
# Per-character width as a fraction of font size, Excalifont, measureText on the
# loaded Excalidraw 0.18.1 fonts (2026-10-28). Each character sits in the
# smallest bucket >= its real width (max of a single glyph and a repeated run, so
# kerning around "/", "f" is covered). Scales linearly with font size.
_RATIO_BUCKETS = {
    0.28: "·'li,:.‘",
    0.32: ";|!’",
    0.42: "\" )-rjг°›“",
    0.47: "1(?”„",
    0.52: "[тf]cс{цчзь^в",
    0.56: "*nкyийуkepерqэнsL}Iuл−+=<>ёпvtдяbg7Г×÷±≈≠≤≥•‹■□é",
    0.60: "/YhJzHбНaаУ4П\\xхЧVмъoо✗",
    0.64: "фdЦ3KК5ИЙSXХ9CСNЗ8БЬ6Я●",
    0.68: "↑↓ж«ЭшFm0Л»~_щAА",
    0.72: "ЪФPРы2–EЕЁ…&w€£",
    0.76: "$URюД",
    0.80: "BВMМOОQDGШ#WЫЩ✓✕Ω",
    0.84: "@ZЖ",
    0.88: "TТЮ✔▶",
    0.94: "%—⇒",
    1.00: "→←↗↘★☆⚠▲▼◀♥",
    1.07: "№⟶",
}
_RATIO = {c: r for r, chars in _RATIO_BUCKETS.items() for c in chars}


def _char_ratio(c):
    if c in _RATIO:
        return _RATIO[c]
    base = unicodedata.normalize("NFD", c)[0]   # é → e, Й → И
    if base in _RATIO:
        return _RATIO[base] + 0.02
    if ord(c) >= 0x2000:                         # emoji, CJK, other symbols: measured 1.0–1.1
        return 1.1
    return 0.88 if c.isupper() else 0.72


def text_width(s, font_size=20):
    """String width in pixels, Excalifont. An upper bound, not an average.

    Computed per character from measured glyph widths, so mixed strings like
    "POST /api/drawings — create" or "−62%" are not underestimated. Checked
    against fittext on ~500 real labels: never narrower than the real width,
    about 6% wider on average. Unknown characters get a generous fallback.
    """
    return font_size * sum(_char_ratio(c) for c in s)


def _base(**kw):
    e = dict(
        id=secrets.token_hex(8), type="rectangle", x=0, y=0, width=100, height=100,
        angle=0, strokeColor="#1e1e1e", backgroundColor="transparent", fillStyle="solid",
        strokeWidth=2, strokeStyle="solid", roughness=1, opacity=100, groupIds=[],
        frameId=None, roundness={"type": 3}, seed=secrets.randbelow(2**31), version=1,
        versionNonce=secrets.randbelow(2**31), isDeleted=False, boundElements=None,
        updated=int(time.time() * 1000), link=None, locked=False,
    )
    e.update(kw)
    return e


def _el(kw, **defaults):
    """_base() where the caller's **kw override the helper's defaults.

    Plain _base(groupIds=..., **kw) raised "multiple values for keyword
    argument" as soon as a generator passed groupIds=, roundness= and so on.
    """
    return _base(**{**defaults, **kw})


def rect(x, y, w, h, fill="transparent", stroke="#1e1e1e", groups=None, **kw):
    return _el(kw, type="rectangle", x=x, y=y, width=w, height=h,
               backgroundColor=fill, strokeColor=stroke, groupIds=groups or [])


MONO = 3                      # Cascadia: every char is ~0.64 of font size


def text(x, y, s, font_size=20, color="#1e1e1e", align="left", groups=None, family=FONT, **kw):
    """A single line. The caller does the wrapping — the engine doesn't.
    family=MONO is monospace, for code and data; width is computed differently."""
    assert "\n" not in s, "line break: put each line in its own text element"
    width = len(s) * font_size * 0.64 if family == MONO else text_width(s, font_size)
    return _el(kw, type="text", x=x, y=y,
               width=width, height=font_size * LINE_HEIGHT,
               text=s, originalText=s, fontSize=font_size, fontFamily=family,
               textAlign=align, verticalAlign="top", containerId=None,
               lineHeight=LINE_HEIGHT, roundness=None, strokeColor=color,
               groupIds=groups or [])


def wrap(s, max_width, font_size=20):
    """Split a string into lines that fit max_width. Wraps on words.

    You have to wrap yourself: Excalidraw wraps neither container text nor
    standalone text — checked visually on the canvas.
    """
    words, lines, cur = s.split(), [], ""
    for w in words:
        probe = f"{cur} {w}".strip()
        if cur and text_width(probe, font_size) > max_width:
            lines.append(cur)
            cur = w
        else:
            cur = probe
    if cur:
        lines.append(cur)
    return lines or [""]


def _bound_text(shape, lines, font_size, color, text_w):
    """Text bound to a container, centered like Excalidraw does it. Links both ways."""
    text_h = len(lines) * font_size * LINE_HEIGHT
    shown = "\n".join(lines)
    cx, cy = _center(shape)
    t = _base(
        type="text", x=cx - text_w / 2, y=cy - text_h / 2, width=text_w, height=text_h,
        text=shown, originalText=shown, fontSize=font_size, fontFamily=FONT,
        textAlign="center", verticalAlign="middle", containerId=shape["id"],
        lineHeight=LINE_HEIGHT, roundness=None, strokeColor=color,
        groupIds=list(shape.get("groupIds") or []),
    )
    shape["boundElements"] = (shape.get("boundElements") or []) + [{"id": t["id"], "type": "text"}]
    return t


def box(x, y, w, label, h=None, fill="#a5d8ff", fill_style="solid", font_size=20,
        pad=12, stroke="#1e1e1e", stroke_style="solid", color="#1e1e1e", **kw):
    """Rectangle with text INSIDE it, bound as a container.

    Better than a separate text element on top: Excalidraw centers the label on
    both axes, double-click edits it, and it moves with the box without
    groupIds. Links are needed both ways: containerId on the text and
    boundElements on the rectangle.

    label is a string (wrapped to width) or a ready list of lines.
    color is the text color, stroke is the frame. Without h the height fits
    the text plus pad on each side (at least 60).
    """
    lines = label if isinstance(label, list) else wrap(label, w - 2 * pad, font_size)
    line_h = font_size * LINE_HEIGHT
    text_h = len(lines) * line_h
    height = h if h is not None else max(text_h + 2 * pad, 60)
    if height < text_h + 2 * pad:
        fit_pad = math.floor((height - text_h) / 2)
        hint = (f", or lower pad to {fit_pad}" if fit_pad >= BOUND_TEXT_PADDING
                else f" (even pad={BOUND_TEXT_PADDING}, Excalidraw's minimum, needs "
                     f"h={math.ceil(text_h + 2 * BOUND_TEXT_PADDING)})")
        raise AssertionError(
            f"box {lines[0][:30]!r}: {len(lines)} line(s) at font {font_size} need "
            f"h >= {math.ceil(text_h + 2 * pad)} with pad={pad}, got h={height:.0f}. "
            f"Raise h{hint}. Omit h to size it automatically."
        )
    rect_el = rect(x, y, w, height, fill=fill, stroke=stroke,
                   fillStyle=fill_style, strokeStyle=stroke_style, **kw)
    # A ready line may be wider than w - 2·pad: store its estimate (up to
    # Excalidraw's own limit), or the editor clips the outer letters.
    text_w = max(w - 2 * pad, max(text_width(l, font_size) for l in lines))
    text_el = _bound_text(rect_el, lines, font_size, color,
                          min(text_w, w - 2 * BOUND_TEXT_PADDING))
    return [rect_el, text_el]


def card(x, y, lines, w=None, font_size=20, pad=16, fill="#ffec99", title_size=None):
    """Deprecated name. Kept so old generators don't break: now it's just
    box() with text inside the container."""
    text_lines = lines if isinstance(lines, list) else [lines]
    width = w or max(text_width(s, font_size) for s in text_lines) + 2 * pad
    return box(x, y, width, text_lines, fill=fill, font_size=font_size, pad=pad)


def arrow(x1, y1, x2, y2, color="#1e1e1e", groups=None, **kw):
    return _el(kw, type="arrow", x=x1, y=y1, width=x2 - x1, height=y2 - y1,
               points=[[0, 0], [x2 - x1, y2 - y1]], strokeColor=color,
               roundness={"type": 2}, groupIds=groups or [],
               startBinding=None, endBinding=None,
               startArrowhead=None, endArrowhead="arrow")


# Text area inside a container, exactly as Excalidraw 0.18 computes it
# (getBoundTextMaxWidth / getBoundTextMaxHeight): the inscribed rectangle minus
# BOUND_TEXT_PADDING on each side. Ellipse: side/√2, diamond: side/2.
_INNER = {
    "ellipse": lambda side: round(side / 2 * math.sqrt(2)) - 2 * BOUND_TEXT_PADDING,
    "diamond": lambda side: round(side / 2) - 2 * BOUND_TEXT_PADDING,
}
# Inverse: the smallest side whose inner size is >= need.
_OUTER = {
    "ellipse": lambda need: math.ceil((need + 2 * BOUND_TEXT_PADDING + 0.5) * math.sqrt(2)),
    "diamond": lambda need: math.ceil((need + 2 * BOUND_TEXT_PADDING) * 2),
}


def _labeled(shape, label, font_size, color):
    """Bind a label to an ellipse/diamond: wrap to the real inner width, assert it fits."""
    kind, w, h = shape["type"], shape["width"], shape["height"]
    inner_w, inner_h = _INNER[kind](w), _INNER[kind](h)
    lines = label if isinstance(label, list) else wrap(label, inner_w, font_size)
    text_w = max(text_width(l, font_size) for l in lines)
    text_h = len(lines) * font_size * LINE_HEIGHT
    # Excalidraw re-wraps the text to inner_w on load: a line wider than that
    # gets broken mid-word and grows downward. fittext's overflow check uses
    # rectangle geometry, so for these shapes this assert is the only guard.
    if text_w > inner_w:
        raise AssertionError(
            f"{kind} {lines[0][:30]!r}: widest line needs w >= {_OUTER[kind](text_w)} "
            f"at font {font_size} (text area is ~{'0.71' if kind == 'ellipse' else '0.5'} of w), "
            f"got w={w:.0f}. Widen it, lower font_size, or pass lines as a list."
        )
    if text_h > inner_h:
        raise AssertionError(
            f"{kind} {lines[0][:30]!r}: {len(lines)} line(s) at font {font_size} need "
            f"h >= {_OUTER[kind](text_h)}, got h={h:.0f}. Raise h, widen w so it "
            f"wraps into fewer lines, or lower font_size."
        )
    return [shape, _bound_text(shape, lines, font_size, color, text_w)]


def ellipse(x, y, w, h, fill="transparent", stroke="#1e1e1e", label=None, font_size=20,
            color="#1e1e1e", **kw):
    """Ellipse. Without label returns the element; with label — [ellipse, text],
    the text bound inside like box() and wrapped to the inscribed width (~0.71·w)."""
    e = _el(kw, type="ellipse", x=x, y=y, width=w, height=h, backgroundColor=fill,
            strokeColor=stroke, roundness=None)
    return e if label is None else _labeled(e, label, font_size, color)


def diamond(x, y, w, h, fill="transparent", stroke="#1e1e1e", label=None, font_size=20,
            color="#1e1e1e", **kw):
    """Diamond. Without label returns the element; with label — [diamond, text],
    the text bound inside and wrapped to the inscribed width (~w/2): a diamond
    needs about twice the width and height of its text."""
    e = _el(kw, type="diamond", x=x, y=y, width=w, height=h, backgroundColor=fill,
            strokeColor=stroke, roundness={"type": 2})
    return e if label is None else _labeled(e, label, font_size, color)


def poly(pts, stroke="#1e1e1e", fill="transparent", closed=False, **kw):
    """Polyline through points. closed=True closes it so fill works:
    funnels, pyramids, icebergs are drawn this way, no extra primitives."""
    pts = list(pts) + ([pts[0]] if closed and pts[0] != pts[-1] else [])
    x0, y0 = pts[0]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return _el(kw, type="line", x=x0, y=y0, points=[[px - x0, py - y0] for px, py in pts],
               width=max(xs) - min(xs), height=max(ys) - min(ys), strokeColor=stroke,
               backgroundColor=fill, startBinding=None, endBinding=None,
               startArrowhead=None, endArrowhead=None, roundness=None)


def curve(pts, color="#1e1e1e", dashed=False, head="arrow", src=None, dst=None, **kw):
    """Arrow through several points — Excalidraw smooths it into a curve.

    src/dst are the shapes to bind the ends to. Without binding the curve stays
    hanging in the editor when the shape is moved. The caller picks points on the
    shape borders: unlike connect(), curve doesn't find the edge itself.
    roundness=None gives sharp elbows instead of smoothing.
    """
    x0, y0 = pts[0]
    a = _el(kw, type="arrow", x=x0, y=y0, points=[[px - x0, py - y0] for px, py in pts],
            width=max(p[0] for p in pts) - min(p[0] for p in pts),
            height=max(p[1] for p in pts) - min(p[1] for p in pts),
            strokeColor=color, strokeStyle="dashed" if dashed else "solid",
            roundness={"type": 2}, startArrowhead=None, endArrowhead=head,
            startBinding=None, endBinding=None)
    for side, shape in (("startBinding", src), ("endBinding", dst)):
        if shape:
            a[side] = {"elementId": shape["id"], "focus": 0, "gap": 4}
            shape["boundElements"] = (shape.get("boundElements") or []) + [{"id": a["id"], "type": "arrow"}]
    return a


def code_card(x, y, lines, w=None, font_size=16, accent=None):
    """Dark card with real data — instead of a box labeled "API response".
    accent: {line index: color}. Returns a list of elements, the first is the background."""
    step = font_size * 1.5
    w = w or max(len(s) for s in lines) * font_size * 0.64 + 32
    bg = rect(x, y, w, 24 + len(lines) * step, fill="#1e293b", stroke="#1e293b")
    out = [bg]
    for i, s in enumerate(lines):
        out.append(text(x + 16, y + 12 + i * step, s, font_size=font_size,
                        color=(accent or {}).get(i, "#e9ecef"), family=MONO))
    return out


def scene(elements, background="#ffffff"):
    """Scene in .excalidraw file format. No theme in the file — that's up to the viewer."""
    return {
        "type": "excalidraw", "version": 2, "source": "claude-code/skills/excalidraw",
        "elements": elements,
        "appState": {"viewBackgroundColor": background, "gridSize": None},
        "files": {},
    }


def save(path, elements, background="#ffffff"):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(scene(elements, background), f, ensure_ascii=False, indent=2)
    return path


def _center(e):
    return e["x"] + e["width"] / 2, e["y"] + e["height"] / 2


def _edge_point(e, tx, ty, gap=4):
    """Point on the shape border toward (tx, ty), with a gap.

    Shape-aware: a rectangle's bounding box left visible gaps at ellipses and
    diamonds. Ellipse — ray/ellipse intersection; diamond — ray/rhombus, and
    since Excalidraw rounds diamond corners (the drawn tip sits 1/16 of the
    half-size inside the vertex), the tips are cut off at that line.
    """
    cx, cy = _center(e)
    dx, dy = tx - cx, ty - cy
    if dx == 0 and dy == 0:
        return cx, cy
    a, b = e["width"] / 2, e["height"] / 2
    kind = e.get("type")
    if kind not in ("ellipse", "diamond") or a <= 0 or b <= 0:
        hw, hh = a + gap, b + gap
        sx = hw / abs(dx) if dx else float("inf")
        sy = hh / abs(dy) if dy else float("inf")
        s = min(sx, sy)
        return cx + dx * s, cy + dy * s
    if kind == "ellipse":
        s = 1 / math.hypot(dx / a, dy / b)
    else:
        s = 1 / (abs(dx) / a + abs(dy) / b)
        if e.get("roundness"):
            ia, ib = a * 15 / 16, b * 15 / 16
            s = min(s, ia / abs(dx) if dx else s, ib / abs(dy) if dy else s)
    n = math.hypot(dx, dy)
    return cx + dx * s + dx / n * gap, cy + dy * s + dy / n * gap


def connect(src, dst, color="#1e1e1e", dashed=False, gap=4, **kw):
    """A real connection: an arrow bound to both shapes.

    Without startBinding/endBinding and the matching boundElements the arrow is
    just a stick nearby: move the card in the editor and the link hangs in the air.
    Binding is set both ways, otherwise Excalidraw won't pick it up.
    The ends land on the real outline of rectangles, ellipses and diamonds.
    """
    sc, dc = _center(src), _center(dst)
    x1, y1 = _edge_point(src, *dc, gap=gap)
    x2, y2 = _edge_point(dst, *sc, gap=gap)
    a = _el(
        kw,
        type="arrow", x=x1, y=y1, width=x2 - x1, height=y2 - y1,
        points=[[0, 0], [x2 - x1, y2 - y1]], strokeColor=color,
        strokeStyle="dashed" if dashed else "solid", roundness={"type": 2},
        backgroundColor="transparent", fillStyle="solid",
        startArrowhead=None, endArrowhead="arrow",
        startBinding={"elementId": src["id"], "focus": 0, "gap": gap},
        endBinding={"elementId": dst["id"], "focus": 0, "gap": gap},
    )
    for shape in (src, dst):
        shape["boundElements"] = (shape.get("boundElements") or []) + [
            {"id": a["id"], "type": "arrow"}
        ]
    return a
