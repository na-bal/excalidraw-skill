#!/usr/bin/env python3
"""Boards: publish, read and edit Excalidraw scenes.

Two backends, picked in ~/.config/excalidraw-skill/config (written by setup.sh):
  local       boards are .excalidraw files in DRAWINGS_DIR, viewed and edited
              in the local board at http://127.0.0.1:3200 (`board.py serve`)
  excalidash  a self-hosted ExcaliDash server (EXCALIDASH_URL, EXCALIDASH_API_KEY)

  board.py list
  board.py get <id> [-o file.excalidraw]
  board.py push file.excalidraw --name "Name" [--frame "Part"]   create a board
  board.py push file.excalidraw --id <id> [--frame "Part"]       update a board
  board.py diff <id> --frame "Part"   what the user changed by hand since the last push
  board.py rm <id>
  board.py open [id]          start the local board if needed and open it
  board.py serve [--port N]   run the local board in the foreground
  board.py where              print backend, drawings dir and board URL
"""
import argparse, hashlib, json, os, re, secrets, subprocess, sys, tempfile, time
import urllib.error, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
# The viewer page may load code only from the two pinned CDNs and talk only to this
# server, so even a tampered CDN file can't send boards anywhere else.
CDN = "https://esm.sh https://cdn.jsdelivr.net"
CSP = (f"default-src 'self'; script-src 'self' 'unsafe-inline' {CDN}; style-src 'self' 'unsafe-inline' {CDN}; "
       f"font-src 'self' data: {CDN}; img-src 'self' data: blob:; connect-src 'self' {CDN}; "
       "worker-src 'self' blob:; frame-ancestors 'none'; form-action 'none'; base-uri 'none'")
CONF_DIR = os.environ.get("EXCALIDRAW_SKILL_CONFIG_DIR") or os.path.join(
    os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config"), "excalidraw-skill")
CACHE = os.environ.get("EXCALIDRAW_SKILL_CACHE") or os.path.join(
    os.environ.get("XDG_CACHE_HOME") or os.path.expanduser("~/.cache"), "excalidraw-skill")
CONFIG = os.path.join(CONF_DIR, "config")
LEGACY = os.path.expanduser("~/.config/excalidash/credentials")   # pre-config installs
SNAP = os.path.join(CACHE, "snapshots")
PAD = 40


def read_kv(path):
    d = {}
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            d[k.strip()] = os.path.expanduser(v.strip())
    return d


def config():
    if os.path.exists(CONFIG):
        return read_kv(CONFIG)
    if os.path.exists(LEGACY):
        return {"BACKEND": "excalidash", **read_kv(LEGACY)}
    print(f"not configured: no {CONFIG} — run scripts/setup.sh", file=sys.stderr)
    sys.exit(6)


def as_elements(obj):
    """Scenes arrive both as files and as API responses; elements may be a JSON string."""
    els = obj.get("elements", obj) if isinstance(obj, dict) else obj
    return json.loads(els) if isinstance(els, str) else els


def as_obj(v, default):
    return json.loads(v) if isinstance(v, str) else (v or default)


# ── Backends ───────────────────────────────────────────────────────────
# Both speak the same shape: list() -> [{id, name, version, updatedAt}],
# get(id) -> {name, elements, appState, files}, create/update/delete, link(id).

class ExcaliDash:
    def __init__(self, c):
        self.url, self.key = c["EXCALIDASH_URL"].rstrip("/"), c["EXCALIDASH_API_KEY"]

    def call(self, method, path, payload=None):
        body = json.dumps(payload).encode() if payload is not None else None
        req = urllib.request.Request(
            self.url + path, data=body, method=method,
            headers={"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                raw = r.read()
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as e:
            sys.exit(f"{method} {path} -> HTTP {e.code}: {e.read()[:300].decode(errors='replace')}")
        except urllib.error.URLError as e:
            sys.exit(f"{method} {self.url}{path}: {e.reason}")

    def list(self):
        return self.call("GET", "/api/drawings").get("drawings", [])

    def get(self, id):
        d = self.call("GET", f"/api/drawings/{check_id(id)}")
        return {"name": d.get("name"), "elements": as_elements(d),
                "appState": as_obj(d.get("appState"), {}), "files": as_obj(d.get("files"), {})}

    def create(self, payload):
        return self.call("POST", "/api/drawings", payload)["id"]

    def update(self, id, payload):
        self.call("PUT", f"/api/drawings/{check_id(id)}", payload)

    def delete(self, id):
        self.call("DELETE", f"/api/drawings/{check_id(id)}")

    def link(self, id):
        return f"{self.url}/editor/{id}"


SAFE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,120}")   # use with fullmatch


def check_id(id):
    if not SAFE_ID.fullmatch(id or "") or ".." in id:
        sys.exit(f"bad board id: {id!r}")
    return id


class Local:
    """Boards as files: DRAWINGS_DIR/<id>.excalidraw, plain Excalidraw JSON plus a name."""

    def __init__(self, c):
        self.dir = c.get("DRAWINGS_DIR") or os.path.expanduser("~/Drawings/excalidraw")
        self.port = int(c.get("LOCAL_PORT") or 3200)
        os.makedirs(self.dir, exist_ok=True)

    def path(self, id):
        return os.path.join(self.dir, check_id(id) + ".excalidraw")

    def read(self, id):
        p = self.path(id)
        if not os.path.exists(p):
            sys.exit(f"no board {id} in {self.dir}")
        return json.load(open(p, encoding="utf-8"))

    def write(self, id, scene):
        tmp = self.path(id) + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(scene, f, ensure_ascii=False)
        os.replace(tmp, self.path(id))

    def list(self):
        out = []
        for fn in os.listdir(self.dir):
            if not fn.endswith(".excalidraw") or not SAFE_ID.fullmatch(fn[:-11]):
                continue
            p = os.path.join(self.dir, fn)
            try:
                d = json.load(open(p, encoding="utf-8"))
            except (OSError, ValueError):
                continue
            out.append({"id": fn[:-11], "name": d.get("name") or fn[:-11],
                        "version": d.get("boardVersion", 1),
                        "updatedAt": time.strftime("%Y-%m-%dT%H:%M", time.localtime(os.path.getmtime(p))),
                        "mtime": str(os.stat(p).st_mtime_ns)})
        return sorted(out, key=lambda d: d["updatedAt"], reverse=True)

    def get(self, id):
        d = self.read(id)
        return {"name": d.get("name") or id, "elements": as_elements(d),
                "appState": d.get("appState") or {}, "files": d.get("files") or {}}

    def save(self, id, payload, version):
        self.write(id, {"type": "excalidraw", "version": 2, "source": "excalidraw-skill",
                        "name": payload["name"], "boardVersion": version,
                        "elements": payload["elements"], "appState": payload.get("appState") or {},
                        "files": payload.get("files") or {}})

    def create(self, payload):
        slug = re.sub(r"[^a-z0-9]+", "-", payload["name"].lower()).strip("-")[:40] or "board"
        id = f"{slug}-{secrets.token_hex(2)}"
        self.save(id, payload, 1)
        return id

    def update(self, id, payload):
        self.save(id, payload, self.read(id).get("boardVersion", 1) + 1)

    def delete(self, id):
        os.remove(self.path(id))

    def link(self, id=None):
        return f"http://127.0.0.1:{self.port}/" + (f"#{id}" if id else "")


def backend():
    c = config()
    kind = c.get("BACKEND", "local")
    if kind == "excalidash":
        return ExcaliDash(c)
    if kind == "local":
        return Local(c)
    sys.exit(f"unknown BACKEND={kind} in {CONFIG}")


# ── Commands ───────────────────────────────────────────────────────────

def cmd_list(_):
    for d in backend().list():
        print(f"{d['id']}  v{d['version']:<4} {d['updatedAt'][:16].replace('T', ' ')}  {d['name']}")


def cmd_get(a):
    d = backend().get(a.id)
    scene = {"type": "excalidraw", "version": 2, "source": a.id, "elements": d["elements"],
             "appState": d["appState"], "files": d["files"]}
    out = json.dumps(scene, ensure_ascii=False, indent=2)
    if a.out:
        open(a.out, "w", encoding="utf-8").write(out)
        print(f"{a.out}: {len(scene['elements'])} elements")
    else:
        print(out)


def fit_text(path):
    """Recompute text dimensions with the real Excalidraw fonts (scripts/mmd/fittext.mjs).

    Without this the editor clips the outer letters: the stored text width was an
    estimate or measured with a fallback font, and the editor draws exactly into it.
    """
    out = tempfile.NamedTemporaryFile(suffix=".excalidraw", delete=False).name
    r = subprocess.run(["node", os.path.join(HERE, "mmd", "fittext.mjs"), path, "-o", out])
    if r.returncode != 0:
        sys.exit("fittext failed — not publishing, labels would be clipped (--no-fit if deliberate)")
    return out


# ── A frame is the unit of ownership ───────────────────────────────────
# push --frame "Name" puts the generator's whole scene into a frame and replaces
# only that frame on the board. Everything else — the user's edits, other
# frames — stays.

def _bbox(els):
    xs, ys = [], []
    for e in els:
        pts = e.get("points") or [[0, 0], [e["width"], e["height"]]]
        xs += [e["x"] + p[0] for p in pts]
        ys += [e["y"] + p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def _snap_path(board, frame):
    return os.path.join(SNAP, f"{check_id(board)}-{hashlib.sha1(frame.encode()).hexdigest()[:10]}.json")


def _snap_entry(e):
    """What push remembers about each element: enough to tell the user's edits apart and describe them."""
    return {"v": e.get("version", 1), "t": e["type"], "x": round(e["x"]), "y": round(e["y"]),
            "w": round(e.get("width", 0)), "h": round(e.get("height", 0)), "text": e.get("text"),
            "stroke": e.get("strokeColor"), "bg": e.get("backgroundColor")}


def _snap_version(s):
    return s.get("v") if isinstance(s, dict) else s   # old snapshots stored the bare version


def wrap_frame(els, name):
    """Wrap all scene elements into one padded frame. Returns (frame, elements)."""
    x0, y0, x1, y1 = _bbox(els)
    fr = {"id": secrets.token_hex(8), "type": "frame", "name": name,
          "x": x0 - PAD, "y": y0 - PAD, "width": x1 - x0 + 2 * PAD, "height": y1 - y0 + 2 * PAD,
          "angle": 0, "strokeColor": "#bbb", "backgroundColor": "transparent", "fillStyle": "solid",
          "strokeWidth": 2, "strokeStyle": "solid", "roughness": 0, "opacity": 100, "groupIds": [],
          "frameId": None, "roundness": None, "seed": 1, "version": 1, "versionNonce": 1,
          "isDeleted": False, "boundElements": None, "updated": 1, "link": None, "locked": False}
    for e in els:
        e["frameId"] = fr["id"]
    return fr, els


def merge_frame(board_id, old, new, name, force=False):
    old = [e for e in old if not e.get("isDeleted")]
    fr, new = wrap_frame(new, name)
    prev = next((e for e in old if e["type"] == "frame" and e.get("name") == name), None)
    if prev:
        owned = {prev["id"]} | {e["id"] for e in old if e.get("frameId") == prev["id"]}
        owned |= {e["id"] for e in old if e.get("containerId") in owned}
        snap = {}
        if os.path.exists(_snap_path(board_id, name)):
            snap = json.load(open(_snap_path(board_id, name)))
        touched = [e for e in old if e["id"] in owned and e["id"] != prev["id"]
                   and _snap_version(snap.get(e["id"])) != e.get("version")]
        if touched and not force:
            sys.exit(f"frame «{name}» was edited by hand: {len(touched)} elements changed or added "
                     f"since the last push. Redrawing would wipe them. Tell the user; "
                     f"--force only if they agree.")
        dx, dy = prev["x"] - fr["x"], prev["y"] - fr["y"]   # the user may have moved the frame
        rest = [e for e in old if e["id"] not in owned]
    else:
        owned = set()
        if old:
            x0, _, _, y1 = _bbox(old)
            dx, dy = x0 - fr["x"], y1 + 150 - fr["y"]         # a new frame goes below everything
        else:
            dx = dy = 0
        rest = old
    for e in [fr] + new:
        e["x"] += dx
        e["y"] += dy
    for e in rest:   # detach bindings to removed elements, or they dangle
        for side in ("startBinding", "endBinding"):
            if (e.get(side) or {}).get("elementId") in owned:
                e[side] = None
        if e.get("boundElements"):
            e["boundElements"] = [b for b in e["boundElements"] if b["id"] not in owned]
    return rest + [fr] + new, {e["id"]: _snap_entry(e) for e in [fr] + new}


def cmd_push(a):
    b = backend()
    src = a.file if a.no_fit else fit_text(a.file)
    scene = json.load(open(src, encoding="utf-8"))
    if src != a.file:
        os.unlink(src)
    payload = {
        "elements": as_elements(scene),
        "appState": scene.get("appState", {"viewBackgroundColor": "#ffffff", "gridSize": None}),
        "files": scene.get("files", {}),
    }
    cur = b.get(a.id) if a.id else None
    snap = None
    if a.frame:
        payload["elements"], snap = merge_frame(a.id or "new", cur["elements"] if cur else [],
                                                payload["elements"], a.frame, a.force)
        if cur:
            payload["files"] = {**cur["files"], **payload["files"]}
            payload["appState"] = cur["appState"] or payload["appState"]
    if a.id:
        payload["name"] = a.name or cur["name"]
        b.update(a.id, payload)
        print(f"updated: {b.link(a.id)}" + (f"  (frame «{a.frame}»)" if a.frame else ""))
    else:
        if not a.name:
            sys.exit("a new board needs --name")
        payload["name"] = a.name
        a.id = b.create(payload)
        print(f"created: {b.link(a.id)}\nid: {a.id}")
    if isinstance(b, Local):
        print(f"file: {b.path(a.id)}")
    if snap:
        os.makedirs(SNAP, exist_ok=True)
        json.dump(snap, open(_snap_path(a.id, a.frame), "w"))


def cmd_diff(a):
    """What the user changed by hand in a frame since the last push — the raw material for a lesson."""
    path = _snap_path(a.id, a.frame)
    if not os.path.exists(path):
        sys.exit(f"no snapshot for frame «{a.frame}» on {a.id}: it was never pushed from this machine")
    snap = json.load(open(path))
    els = [e for e in backend().get(a.id)["elements"] if not e.get("isDeleted")]
    fr = next((e for e in els if e["type"] == "frame" and e.get("name") == a.frame), None)
    if not fr:
        sys.exit(f"frame «{a.frame}» is gone from the board — the user deleted it")
    cur = {e["id"]: e for e in els if e.get("frameId") == fr["id"] or e["id"] == fr["id"]}
    cur.update({e["id"]: e for e in els if e.get("containerId") in cur})
    label = {e["containerId"]: e.get("text", "") for e in cur.values() if e.get("containerId")}

    def name(id, e):
        t = (e or {}).get("text") or label.get(id) or (snap.get(id) or {}).get("text") or ""
        kind = (e or {}).get("type") or (snap.get(id) or {}).get("t", "element")
        return f"{kind} «{t[:40]}»" if t else kind

    out = []
    for id, e in cur.items():
        s = snap.get(id)
        if s is None:
            out.append(f"added    {name(id, e)} at {round(e['x'])},{round(e['y'])}")
            continue
        if _snap_version(s) == e.get("version") or not isinstance(s, dict):
            continue
        what = []
        if e.get("text") != s["text"] and s["text"] is not None:
            what.append(f"text «{s['text'][:40]}» → «{(e.get('text') or '')[:40]}»")
        dx, dy = round(e["x"]) - s["x"], round(e["y"]) - s["y"]
        if (dx or dy) and id != fr["id"]:
            what.append(f"moved {dx:+},{dy:+}")
        if (round(e.get("width", 0)), round(e.get("height", 0))) != (s["w"], s["h"]) and e["type"] != "text":
            what.append(f"resized {s['w']}×{s['h']} → {round(e['width'])}×{round(e['height'])}")
        for k, sk in (("strokeColor", "stroke"), ("backgroundColor", "bg")):
            if e.get(k) != s[sk]:
                what.append(f"{sk} {s[sk]} → {e.get(k)}")
        if what:
            out.append(f"changed  {name(id, e)}: " + "; ".join(what))
    for id, s in snap.items():
        if id not in cur:
            out.append(f"deleted  {name(id, None)}")
    print("\n".join(out) if out else f"frame «{a.frame}»: no hand edits since the last push")


def cmd_rm(a):
    backend().delete(a.id)
    print(f"deleted: {a.id}")


def cmd_rename(a):
    b = backend()
    name = a.name.strip()[:120]
    if not name:
        sys.exit("the name is empty")
    b.update(a.id, {**b.get(a.id), "name": name})
    print(f"renamed: {name}  {b.link(a.id)}")

def cmd_where(_):
    c, b = config(), backend()
    print(f"backend: {c.get('BACKEND', 'local')}\nconfig:  {CONFIG if os.path.exists(CONFIG) else LEGACY}")
    print(f"drawings: {b.dir}" if isinstance(b, Local) else f"server:  {b.url}")
    print(f"board:   {b.link(None) if isinstance(b, Local) else b.url}")


# ── Local board server ─────────────────────────────────────────────────

def _alive(port):
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{port}/api/ping", timeout=0.5)
        return True
    except (OSError, urllib.error.URLError):
        return False


def cmd_open(a):
    b = backend()
    if isinstance(b, Local) and not _alive(b.port):
        os.makedirs(CACHE, exist_ok=True)
        log = open(os.path.join(CACHE, "serve.log"), "a")
        subprocess.Popen([sys.executable, os.path.abspath(__file__), "serve"], stdout=log, stderr=log,
                         stdin=subprocess.DEVNULL, start_new_session=True)
        for _ in range(30):
            if _alive(b.port):
                break
            time.sleep(0.1)
        else:
            sys.exit(f"local board didn't start, see {os.path.join(CACHE, 'serve.log')}")
    url = b.link(a.id)
    print(url)
    if not a.no_browser:
        import webbrowser
        webbrowser.open(url)


def cmd_serve(a):
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    b = backend()
    if not isinstance(b, Local):
        sys.exit("serve is for the local backend; with excalidash open the server URL")
    port = a.port or b.port
    page = os.path.join(HERE, "viewer", "index.html")
    hosts = {f"127.0.0.1:{port}", f"localhost:{port}"}
    origins = {f"http://{h}" for h in hosts}

    class H(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def send(self, code, obj=None, body=None, ctype="application/json"):
            body = body if body is not None else json.dumps(obj, ensure_ascii=False).encode()
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "DENY")
            if ctype.startswith("text/html"):
                self.send_header("Content-Security-Policy", CSP)
            self.end_headers()
            self.wfile.write(body)

        def guard(self, write=False):
            # Host: no DNS rebinding. Origin / Sec-Fetch-Site: no requests from other sites
            # (a page the user visits can still send "simple" POSTs to 127.0.0.1).
            h = self.headers
            ok = (h.get("Host") in hosts
                  and h.get("Origin") in (None, *origins)
                  and h.get("Sec-Fetch-Site") in (None, "same-origin", "none"))
            if ok and write:
                ok = (h.get("Origin") in origins
                      and (h.get("Content-Type") or "").startswith("application/json"))
            if not ok:
                self.send(403, {"error": "forbidden"})
            return ok

        def board_id(self):
            m = re.fullmatch(r"/api/drawings/([^/?]+)", self.path)
            return m.group(1) if m and SAFE_ID.fullmatch(m.group(1)) and ".." not in m.group(1) else None

        def body(self):
            n = int(self.headers.get("Content-Length") or 0)
            if not 0 <= n <= 200_000_000:
                raise ValueError("bad length")
            return json.loads(self.rfile.read(n) or b"{}")

        def mtime(self, id):
            return str(os.stat(b.path(id)).st_mtime_ns)

        def do_GET(self):
            if not self.guard():
                return
            if self.path in ("/", "/index.html"):
                return self.send(200, body=open(page, "rb").read(), ctype="text/html; charset=utf-8")
            if self.path == "/api/ping":
                return self.send(200, {"ok": True})
            if self.path == "/api/drawings":
                return self.send(200, {"drawings": b.list()})
            id = self.board_id()
            if id and os.path.exists(b.path(id)):
                return self.send(200, {**b.get(id), "id": id, "mtime": self.mtime(id)})
            self.send(404, {"error": "not found"})

        def do_PUT(self):   # save from the browser; refuse if the file changed under it
            if not self.guard(write=True):
                return
            id = self.board_id()
            if not id or not os.path.exists(b.path(id)):
                return self.send(404, {"error": "not found"})
            d = self.body()
            if d.get("baseMtime") != self.mtime(id):
                return self.send(409, {"error": "changed on disk"})
            cur = b.read(id)
            b.save(id, {"name": d.get("name") or cur.get("name") or id, "elements": d["elements"],
                        "appState": d.get("appState"), "files": d.get("files")},
                   cur.get("boardVersion", 1) + 1)
            self.send(200, {"mtime": self.mtime(id)})

        def do_POST(self):
            if not self.guard(write=True):
                return
            if self.path != "/api/drawings":
                return self.send(404, {"error": "not found"})
            name = (self.body().get("name") or "Untitled").strip()[:120]
            id = b.create({"name": name, "elements": [],
                           "appState": {"viewBackgroundColor": "#ffffff", "gridSize": None}})
            self.send(200, {"id": id})

        def do_PATCH(self):   # rename from the board list
            if not self.guard(write=True):
                return
            id = self.board_id()
            if not id or not os.path.exists(b.path(id)):
                return self.send(404, {"error": "not found"})
            name = str(self.body().get("name") or "").strip()[:120]
            if not name:
                return self.send(400, {"error": "empty name"})
            cur = b.read(id)
            b.save(id, {**b.get(id), "name": name}, cur.get("boardVersion", 1) + 1)
            self.send(200, {"mtime": self.mtime(id)})

        def do_DELETE(self):
            if not self.guard(write=True):
                return
            id = self.board_id()
            if not id or not os.path.exists(b.path(id)):
                return self.send(404, {"error": "not found"})
            b.delete(id)
            self.send(200, {"ok": True})

    srv = ThreadingHTTPServer(("127.0.0.1", port), H)
    print(f"local board: http://127.0.0.1:{port}/  ({b.dir})", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
sub = p.add_subparsers(dest="cmd", required=True)
sub.add_parser("list").set_defaults(fn=cmd_list)
sub.add_parser("where").set_defaults(fn=cmd_where)
g = sub.add_parser("get"); g.add_argument("id"); g.add_argument("-o", "--out"); g.set_defaults(fn=cmd_get)
u = sub.add_parser("push"); u.add_argument("file"); u.add_argument("--name"); u.add_argument("--id")
u.add_argument("--no-fit", action="store_true", help="skip font fitting (labels may be clipped)")
u.add_argument("--frame", help="put the scene into a frame with this name and replace only that frame")
u.add_argument("--force", action="store_true", help="redraw the frame even if it was edited by hand")
u.set_defaults(fn=cmd_push)
d = sub.add_parser("diff", help="what the user changed by hand in a frame since the last push")
d.add_argument("id"); d.add_argument("--frame", required=True); d.set_defaults(fn=cmd_diff)
n = sub.add_parser("rename"); n.add_argument("id"); n.add_argument("name"); n.set_defaults(fn=cmd_rename)
r = sub.add_parser("rm"); r.add_argument("id"); r.set_defaults(fn=cmd_rm)
o = sub.add_parser("open"); o.add_argument("id", nargs="?"); o.add_argument("--no-browser", action="store_true")
o.set_defaults(fn=cmd_open)
s = sub.add_parser("serve"); s.add_argument("--port", type=int); s.set_defaults(fn=cmd_serve)

if __name__ == "__main__":
    a = p.parse_args()
    a.fn(a)
