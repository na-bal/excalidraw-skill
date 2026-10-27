"""Stamps: ready-made icons from libraries.excalidraw.com libraries.

In a generator:
    from stamps import stamp
    E += stamp("db", x, y, w=60)                     # quick stamp by short name
    E += stamp("moochin_simple-characters:Dragon", x, y, h=80)   # any icon by full key

The icon is copied whole, scaled, gets new ids and a shared groupId —
it moves as one object in the editor.

From the terminal:
    stamps.py list            quick stamps with descriptions
    stamps.py find <word>     search all libraries (names are in English)
    stamps.py libs            libraries and item counts
    stamps.py stats           candidates for promotion and removal
    stamps.py export out.excalidrawlib   quick stamps as a library for the Library panel

Usage stats live in $EXCALIDRAW_SKILL_CONFIG_DIR/usage.json
(default: $XDG_CONFIG_HOME/excalidraw-skill or ~/.config/excalidraw-skill).
"""
import atexit, copy, glob, hashlib, json, os, secrets, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "..", "assets")
LIBDIR = os.path.join(ASSETS, "libraries")
# Usage counter lives outside the skill dir so skill updates don't wipe it.
CONF = os.environ.get("EXCALIDRAW_SKILL_CONFIG_DIR") or os.path.join(
    os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config"), "excalidraw-skill")
USAGE = os.path.join(CONF, "usage.json")

PROMOTE_AT = 3      # non-quick icon used in this many diagrams becomes a quick-stamp candidate
STALE_AFTER = 20    # quick stamp unused in the last N diagrams becomes a removal candidate

QUICK = json.load(open(os.path.join(ASSETS, "quick.json"), encoding="utf-8"))
# Fields a hand-made element in quick.json may omit.
_DEFAULTS = dict(angle=0, strokeColor="#1e1e1e", backgroundColor="transparent", fillStyle="solid",
                 strokeWidth=2, strokeStyle="solid", roughness=1, opacity=100, groupIds=[],
                 frameId=None, roundness=None, version=1, versionNonce=1, isDeleted=False,
                 boundElements=None, updated=1, link=None, locked=False)


def _load():
    lib = {}
    for f in sorted(glob.glob(os.path.join(LIBDIR, "*.excalidrawlib"))):
        stem = os.path.basename(f)[: -len(".excalidrawlib")]
        d = json.load(open(f, encoding="utf-8"))
        # v2: named libraryItems, v1: plain list of element sets
        items = d.get("libraryItems") or [{"name": f"#{n}", "elements": els}
                                           for n, els in enumerate(d.get("library", []))]
        for n, it in enumerate(items):
            key = f"{stem}:{it.get('name') or f'#{n}'}"
            if key in lib:
                key = f"{key} #{n}"
            els = [e for e in it["elements"] if not e.get("isDeleted")]
            if els:
                lib[key] = els
    # Hand-made quick stamps: elements live in quick.json itself (key "skill:<name>").
    for n, v in QUICK.items():
        if "elements" in v:
            lib[v["key"]] = [{**_DEFAULTS, "id": f"{n}-{i}", "seed": i + 1, **e} for i, e in enumerate(v["elements"])]
    return lib


LIB = _load()
_used = set()


def bbox(els):
    xs, ys = [], []
    for e in els:
        if e.get("points"):  # for lines use points for bounds, width can be wrong
            xs += [e["x"] + px for px, _ in e["points"]]
            ys += [e["y"] + py for _, py in e["points"]]
        else:
            xs += [e["x"], e["x"] + abs(e["width"])]
            ys += [e["y"], e["y"] + abs(e["height"])]
    return min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)


def resolve(name):
    if name in QUICK:
        return QUICK[name]["key"], QUICK[name].get("bare", False)
    if name in LIB:
        return name, False
    hits = [k for k in LIB if name.lower() in k.lower()]
    raise KeyError(f"no stamp {name!r}. Similar: {hits[:8] or 'none'}. See: stamps.py list / find")


def _rgba(c):
    """'#rgb', '#rgba', '#rrggbb', '#rrggbbaa', 'white', 'transparent' → (r, g, b, a) or None."""
    c = str(c or "").strip().lower()
    if c in ("white",):
        return 255, 255, 255, 255
    if c in ("", "transparent", "none"):
        return 0, 0, 0, 0
    if not c.startswith("#") or len(c) not in (4, 5, 7, 9):
        return None
    h = c[1:]
    if len(h) <= 4:
        h = "".join(ch * 2 for ch in h)
    try:
        v = [int(h[i:i + 2], 16) for i in range(0, len(h), 2)]
    except ValueError:
        return None
    return tuple(v + [255] * (4 - len(v)))


def _clear(c):
    v = _rgba(c)
    return v is not None and v[3] == 0


def _whiteish(c):
    """White or near-white and visible: library icons use these as masks."""
    v = _rgba(c)
    return v is not None and v[3] > 0 and min(v[:3]) >= 0xF0


def _norm(s):
    return "".join(ch for ch in s.lower() if ch.isalnum())


def _captions(els, key):
    """Free text elements that are captions, not part of the drawing.

    A caption repeats the item name ("Server" in it-icons:Server, "Code" under
    xxxdeveloper_icons:code). File icons repeat the name twice, as a colored tag
    inside and a caption under it — then only the copy outside the drawing goes.
    Glyphs that are the drawing (">_", "｡◕‿◕｡", "zZ") don't match the name and stay."""
    name = _norm(key.split(":", 1)[1])
    free = [e for e in els if e["type"] == "text" and not e.get("containerId")]
    shapes = [e for e in els if e["type"] != "text"]

    def named(e):
        t = _norm(e.get("text", ""))
        return t and (t == name or (len(t) >= 2 and t in name))
    hits = [e for e in free if named(e)]
    if not hits or not shapes:
        return hits
    bx, by, bw, bh = bbox(shapes)

    def outside(e):
        cx, cy = e["x"] + e["width"] / 2, e["y"] + e["height"] / 2
        return not (bx <= cx <= bx + bw and by <= cy <= by + bh)
    return [e for e in hits if outside(e)] or hits


def stamp(name, x, y, w=None, h=None, color=None, bare=None, bg=None, fit=None):
    """Icon at (x, y), the top-left corner. w or h set the size keeping the
    aspect ratio; fit=(W, H) scales it to fit that box and centers it there.
    color recolors the strokes (white masks and transparent ones stay).
    bg paints the white masks and fills with the background color, for icons
    placed on a colored zone. bare=True drops the captions that repeat the
    icon's name ("Server", "Code"); for quick stamps the default comes from quick.json."""
    key, default_bare = resolve(name)
    _used.add(key)
    # opacity 0 = invisible padding frame (it-icons): it only inflates the size
    src = [e for e in copy.deepcopy(LIB[key]) if e.get("opacity", 100) > 0] or copy.deepcopy(LIB[key])
    if bare if bare is not None else default_bare:
        drop = {id(e) for e in _captions(src, key)}
        src = [e for e in src if id(e) not in drop] or src
    bx, by, bw, bh = bbox(src)
    if fit:
        k = min(fit[0] / bw, fit[1] / bh)
        x, y = x + (fit[0] - bw * k) / 2, y + (fit[1] - bh * k) / 2
    else:
        k = (w / bw) if w else (h / bh) if h else 1
    ids = {e["id"]: secrets.token_hex(8) for e in src}
    gids = {g: secrets.token_hex(8) for e in src for g in e.get("groupIds", [])}
    top = secrets.token_hex(8)
    for e in src:
        e["id"] = ids[e["id"]]
        e["x"], e["y"] = x + (e["x"] - bx) * k, y + (e["y"] - by) * k
        e["width"], e["height"] = e["width"] * k, e["height"] * k
        if "points" in e:
            e["points"] = [[px * k, py * k] for px, py in e["points"]]
        if "fontSize" in e:
            e["fontSize"] *= k
        e["strokeWidth"] = max(1, e.get("strokeWidth", 1) * min(1, k * 1.5))
        e["groupIds"] = [gids[g] for g in e.get("groupIds", [])] + [top]
        e["seed"] = secrets.randbelow(2**31)
        e["frameId"] = None
        if e.get("containerId"):
            e["containerId"] = ids.get(e["containerId"])
        if e.get("boundElements"):
            e["boundElements"] = [dict(b, id=ids[b["id"]]) for b in e["boundElements"] if b["id"] in ids]
        for side in ("startBinding", "endBinding"):
            b = e.get(side)
            e[side] = dict(b, elementId=ids[b["elementId"]]) if b and b.get("elementId") in ids else None
        if color and e.get("strokeColor") and not _clear(e["strokeColor"]) and not _whiteish(e["strokeColor"]):
            e["strokeColor"] = color
        if bg:
            for f in ("strokeColor", "backgroundColor"):
                if _whiteish(e.get(f)):
                    e[f] = bg
    return src


# ── Usage tracking: which icons appear in which diagrams ───────────────
# Diagram = generator script. Rerunning the same generator doesn't inflate the count.
# Run catalogs and previews with STAMPS_NO_USAGE=1, or they'll count everything.

def _read_usage():
    try:
        return json.load(open(USAGE, encoding="utf-8"))
    except (OSError, ValueError):
        return {"schemas": [], "icons": {}}


@atexit.register
def _record():
    if os.environ.get("STAMPS_NO_USAGE") or not _used or not sys.argv or not sys.argv[0].endswith(".py") or sys.argv[0].endswith("stamps.py"):
        return
    sid = hashlib.sha1(os.path.abspath(sys.argv[0]).encode()).hexdigest()[:12]
    u = _read_usage()
    if sid not in u["schemas"]:
        u["schemas"].append(sid)
    fresh = set()
    for key in _used:
        rec = u["icons"].setdefault(key, {"schemas": []})
        if sid not in rec["schemas"]:
            rec["schemas"].append(sid)
            fresh.add(key)
        rec["last"] = time.strftime("%Y-%m-%d")
    os.makedirs(CONF, exist_ok=True)
    json.dump(u, open(USAGE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    quick_keys = {v["key"] for v in QUICK.values()}
    hot = [k for k in fresh if k not in quick_keys and len(u["icons"][k]["schemas"]) == PROMOTE_AT]
    for k in hot:
        print(f"stamps: quick-stamp candidate: {k} (used in {PROMOTE_AT} diagrams; tell the user, see stamps.py stats)", file=sys.stderr)


def stats():
    u = _read_usage()
    order = u["schemas"]
    quick_keys = {v["key"]: n for n, v in QUICK.items()}
    print(f"diagrams tracked: {len(order)}")
    promote = sorted(((len(r["schemas"]), k) for k, r in u["icons"].items()
                      if k not in quick_keys and len(r["schemas"]) >= PROMOTE_AT), reverse=True)
    print("\nquick-stamp candidates:" if promote else "\nno quick-stamp candidates")
    for n, k in promote:
        print(f"  {n} diagrams  {k}")
    recent = set(order[-STALE_AFTER:])
    if len(order) >= STALE_AFTER:
        stale = [n for k, n in quick_keys.items()
                 if not recent & set(u["icons"].get(k, {}).get("schemas", []))]
        print(f"\nquick stamps unused in the last {STALE_AFTER} diagrams: {', '.join(stale) or 'none'}")
    else:
        print(f"\ntoo early to judge removals: need at least {STALE_AFTER} diagrams")


def export(path):
    items = [{"id": secrets.token_hex(8), "status": "published", "created": int(time.time() * 1000),
              "name": n, "elements": stamp(n, 0, 0)} for n in QUICK]
    json.dump({"type": "excalidrawlib", "version": 2, "source": "claude-code/skills/excalidraw",
               "libraryItems": items}, open(path, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"{len(items)} stamps → {path}")


if __name__ == "__main__":
    cmd, *rest = sys.argv[1:] or ["list"]
    if cmd == "list":
        for n, v in QUICK.items():
            print(f"{n:15} {v['about']}")
    elif cmd == "find":
        q = " ".join(rest).lower()
        for k in LIB:
            if q in k.lower():
                print(k)
    elif cmd == "libs":
        from collections import Counter
        for lib, c in sorted(Counter(k.split(":")[0] for k in LIB).items()):
            print(f"{c:4}  {lib}")
    elif cmd == "stats":
        stats()
    elif cmd == "export":
        export(rest[0] if rest else "quick.excalidrawlib")
    else:
        print(__doc__)
