"""Builder for .excalidraw scenes. Imported by the generator of a specific diagram.

The main reason it exists: Excalidraw does not wrap text, so you have to
compute box widths yourself. The formula is checked against measureText on
Excalidraw fonts — see references/recipe.md.
"""
import json, secrets, time

FONT = 5                      # Excalidraw 0.18: 1 Virgil, 5 Excalifont, 6 Nunito, 8 Comic Shanns
LINE_HEIGHT = 1.25
# Per-character width as a fraction of font size, rounded up. measureText on Excalifont, 2026-09-25:
# lowercase Cyrillic 0.52–0.56, capitals 0.63, Latin 0.48, "m"/"w" up to 0.67.
# The old 0.55/0.48 were averages, not ceilings: capitals and Ж/Ш/Щ/Ю overflowed.
UPPER_RATIO, CYR_RATIO, LAT_RATIO, WIDE_RATIO = 0.68, 0.58, 0.52, 0.80
WIDE = set("mwMWжшщюыфЖШЩЮЫФ")


def text_width(s, font_size=20):
    """String width in pixels.

    Computed per character, not by the "dominant" alphabet: mixed strings like
    "POST /api/drawings — create" are common, and one ratio for the whole string
    underestimated the width, so the assert in card() stayed silent while the
    text overflowed the rectangle.
    """
    def ratio(c):
        if c in WIDE:
            return WIDE_RATIO
        if c.isupper():
            return UPPER_RATIO
        return CYR_RATIO if "\u0400" <= c <= "\u04ff" else LAT_RATIO
    return font_size * sum(ratio(c) for c in s)


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


def rect(x, y, w, h, fill="transparent", stroke="#1e1e1e", groups=None, **kw):
    return _base(type="rectangle", x=x, y=y, width=w, height=h,
                 backgroundColor=fill, strokeColor=stroke, groupIds=groups or [], **kw)


MONO = 3                      # Cascadia: every char is ~0.64 of font size


def text(x, y, s, font_size=20, color="#1e1e1e", align="left", groups=None, family=FONT, **kw):
    """A single line. The caller does the wrapping — the engine doesn't.
    family=MONO is monospace, for code and data; width is computed differently."""
    assert "\n" not in s, "line break: put each line in its own text element"
    width = len(s) * font_size * 0.64 if family == MONO else text_width(s, font_size)
    return _base(type="text", x=x, y=y,
                 width=width, height=font_size * LINE_HEIGHT,
                 text=s, originalText=s, fontSize=font_size, fontFamily=family,
                 textAlign=align, verticalAlign="top", containerId=None,
                 lineHeight=LINE_HEIGHT, roundness=None, strokeColor=color,
                 groupIds=groups or [], **kw)


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


def box(x, y, w, label, h=None, fill="#a5d8ff", fill_style="solid", font_size=20,
        pad=12, stroke="#1e1e1e", stroke_style="solid", **kw):
    """Rectangle with text INSIDE it, bound as a container.

    Better than a separate text element on top: Excalidraw centers the label on
    both axes, double-click edits it, and it moves with the box without
    groupIds. Links are needed both ways: containerId on the text and
    boundElements on the rectangle.

    label is a string (wrapped to width) or a ready list of lines.
    """
    lines = label if isinstance(label, list) else wrap(label, w - 2 * pad, font_size)
    line_h = font_size * LINE_HEIGHT
    text_h = len(lines) * line_h
    height = h if h is not None else max(text_h + 2 * pad, 60)
    assert height >= text_h + 2 * pad, (
        f"text does not fit vertically: need {text_h + 2 * pad:.0f}px, got {height:.0f}px"
    )
    shown = "\n".join(lines)
    rect_el = rect(x, y, w, height, fill=fill, stroke=stroke,
                   fillStyle=fill_style, strokeStyle=stroke_style, **kw)
    text_el = _base(
        type="text", x=x + pad, y=y + (height - text_h) / 2,
        width=w - 2 * pad, height=text_h,
        text=shown, originalText=shown, fontSize=font_size, fontFamily=FONT,
        textAlign="center", verticalAlign="middle", containerId=rect_el["id"],
        lineHeight=LINE_HEIGHT, roundness=None, strokeColor="#1e1e1e",
    )
    rect_el["boundElements"] = [{"id": text_el["id"], "type": "text"}]
    return [rect_el, text_el]


def card(x, y, lines, w=None, font_size=20, pad=16, fill="#ffec99", title_size=None):
    """Deprecated name. Kept so old generators don't break: now it's just
    box() with text inside the container."""
    text_lines = lines if isinstance(lines, list) else [lines]
    width = w or max(text_width(s, font_size) for s in text_lines) + 2 * pad
    return box(x, y, width, text_lines, fill=fill, font_size=font_size, pad=pad)


def arrow(x1, y1, x2, y2, color="#1e1e1e", groups=None, **kw):
    return _base(type="arrow", x=x1, y=y1, width=x2 - x1, height=y2 - y1,
                 points=[[0, 0], [x2 - x1, y2 - y1]], strokeColor=color,
                 roundness={"type": 2}, groupIds=groups or [],
                 startBinding=None, endBinding=None,
                 startArrowhead=None, endArrowhead="arrow", **kw)


def ellipse(x, y, w, h, fill="transparent", stroke="#1e1e1e", **kw):
    return _base(type="ellipse", x=x, y=y, width=w, height=h, backgroundColor=fill,
                 strokeColor=stroke, roundness=None, **kw)


def diamond(x, y, w, h, fill="transparent", stroke="#1e1e1e", **kw):
    return _base(type="diamond", x=x, y=y, width=w, height=h, backgroundColor=fill,
                 strokeColor=stroke, roundness={"type": 2}, **kw)


def poly(pts, stroke="#1e1e1e", fill="transparent", closed=False, **kw):
    """Polyline through points. closed=True closes it so fill works:
    funnels, pyramids, icebergs are drawn this way, no extra primitives."""
    pts = list(pts) + ([pts[0]] if closed and pts[0] != pts[-1] else [])
    x0, y0 = pts[0]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    kw.setdefault("roundness", None)
    return _base(type="line", x=x0, y=y0, points=[[px - x0, py - y0] for px, py in pts],
                 width=max(xs) - min(xs), height=max(ys) - min(ys), strokeColor=stroke,
                 backgroundColor=fill, startBinding=None, endBinding=None,
                 startArrowhead=None, endArrowhead=None, **kw)


def curve(pts, color="#1e1e1e", dashed=False, head="arrow", src=None, dst=None, **kw):
    """Arrow through several points — Excalidraw smooths it into a curve.

    src/dst are the shapes to bind the ends to. Without binding the curve stays
    hanging in the editor when the shape is moved. The caller picks points on the
    shape borders: unlike connect(), curve doesn't find the edge itself.
    """
    x0, y0 = pts[0]
    a = _base(type="arrow", x=x0, y=y0, points=[[px - x0, py - y0] for px, py in pts],
              width=max(p[0] for p in pts) - min(p[0] for p in pts),
              height=max(p[1] for p in pts) - min(p[1] for p in pts),
              strokeColor=color, strokeStyle="dashed" if dashed else "solid",
              roundness={"type": 2}, startArrowhead=None, endArrowhead=head,
              startBinding=None, endBinding=None, **kw)
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
    """Point on the rectangle border toward (tx, ty), with a gap."""
    cx, cy = _center(e)
    dx, dy = tx - cx, ty - cy
    if dx == 0 and dy == 0:
        return cx, cy
    hw, hh = e["width"] / 2 + gap, e["height"] / 2 + gap
    sx = hw / abs(dx) if dx else float("inf")
    sy = hh / abs(dy) if dy else float("inf")
    s = min(sx, sy)
    return cx + dx * s, cy + dy * s


def connect(src, dst, color="#1e1e1e", dashed=False, gap=4, **kw):
    """A real connection: an arrow bound to both shapes.

    Without startBinding/endBinding and the matching boundElements the arrow is
    just a stick nearby: move the card in the editor and the link hangs in the air.
    Binding is set both ways, otherwise Excalidraw won't pick it up.
    """
    sc, dc = _center(src), _center(dst)
    x1, y1 = _edge_point(src, *dc, gap=gap)
    x2, y2 = _edge_point(dst, *sc, gap=gap)
    a = _base(
        type="arrow", x=x1, y=y1, width=x2 - x1, height=y2 - y1,
        points=[[0, 0], [x2 - x1, y2 - y1]], strokeColor=color,
        strokeStyle="dashed" if dashed else "solid", roundness={"type": 2},
        backgroundColor="transparent", fillStyle="solid",
        startArrowhead=None, endArrowhead="arrow",
        startBinding={"elementId": src["id"], "focus": 0, "gap": gap},
        endBinding={"elementId": dst["id"], "focus": 0, "gap": gap},
        **kw,
    )
    for shape in (src, dst):
        shape["boundElements"] = (shape.get("boundElements") or []) + [
            {"id": a["id"], "type": "arrow"}
        ]
    return a
