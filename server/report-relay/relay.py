#!/usr/bin/env python3
"""Report relay: takes a bug report from a skill's report.py and forwards it to the
author's Telegram. No accounts needed on the sender's side.

  POST /<skill>   JSON {kind, title, body, version, env}   -> 200 {"ok": true, "id": ...}

Every report is also stored in $STATE_DIRECTORY/reports/. Without TG_TOKEN/TG_CHAT
it only stores. Limits: body size, schema, per-IP and global rate. Touch
$STATE_DIRECTORY/muted to stop Telegram messages (reports are still stored).

Env: TG_TOKEN, TG_CHAT, SKILLS (comma list, default excalidraw-skill), PORT (8797).
"""
import json, os, threading, time, urllib.parse, urllib.request
from collections import defaultdict, deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

STATE = os.environ.get("STATE_DIRECTORY") or "/var/lib/skill-reports"
SKILLS = set(filter(None, os.environ.get("SKILLS", "excalidraw-skill").split(",")))
PORT = int(os.environ.get("PORT", "8797"))
MAX_BYTES = 20_000
PER_IP = ((5, 3600), (10, 86400))   # one sender can't eat the global quota
GLOBAL, GLOBAL_WINDOW = 100, 86400
MAX_THREADS = 20
KINDS = {"bug", "install", "docs", "lesson", "other"}
LIMITS = {"title": 140, "body": 15_000, "version": 40}

hits = defaultdict(deque)   # ip -> timestamps of accepted reports
all_hits = deque()
lock = threading.Lock()


def load_hits():
    """The global quota survives restarts: count today's stored reports."""
    d = os.path.join(STATE, "reports")
    if os.path.isdir(d):
        since = time.time() - GLOBAL_WINDOW
        all_hits.extend(sorted(m for m in (os.path.getmtime(os.path.join(d, f)) for f in os.listdir(d))
                               if m > since))


def limited(ip):
    now = time.time()
    with lock:
        while all_hits and all_hits[0] < now - GLOBAL_WINDOW:
            all_hits.popleft()
        q = hits.get(ip, deque())
        while q and q[0] < now - PER_IP[-1][1]:
            q.popleft()
        if not q:
            hits.pop(ip, None)
        if len(all_hits) >= GLOBAL or any(sum(t > now - w for t in q) >= n for n, w in PER_IP):
            return True
        hits[ip] = q
        q.append(now)
        all_hits.append(now)
        return False


def clean(d):
    """Strict schema: known keys, strings only, capped lengths."""
    if not isinstance(d, dict) or d.get("kind") not in KINDS:
        return None
    out = {"kind": d["kind"]}
    for k, n in LIMITS.items():
        v = d.get(k, "")
        if not isinstance(v, str) or (k != "version" and not v.strip()):
            return None
        out[k] = v[:n]
    env = d.get("env") or {}
    if not isinstance(env, dict):
        return None
    out["env"] = {str(k)[:30]: str(v)[:120] for k, v in list(env.items())[:12]}
    return out


def telegram(text):
    token, chat = os.environ.get("TG_TOKEN"), os.environ.get("TG_CHAT")
    if not token or not chat or os.path.exists(os.path.join(STATE, "muted")):
        return False
    data = urllib.parse.urlencode({"chat_id": chat, "text": text[:3500],
                                   "disable_web_page_preview": "true"}).encode()
    try:
        urllib.request.urlopen(f"https://api.telegram.org/bot{token}/sendMessage", data, timeout=15)
        return True
    except OSError as e:
        print("telegram failed:", e, flush=True)
        return False


class H(BaseHTTPRequestHandler):
    timeout = 10   # slow senders don't hold a thread forever

    def log_message(self, *_):
        pass

    def reply(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        self.reply(200, {"ok": True, "accepts": sorted(SKILLS)})

    def do_POST(self):
        skill = self.path.strip("/")
        if skill not in SKILLS:
            return self.reply(404, {"error": "unknown skill"})
        try:
            n = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            n = 0
        if n <= 0 or n > MAX_BYTES:
            return self.reply(413, {"error": f"report must be 1..{MAX_BYTES} bytes"})
        # Caddy (no trusted_proxies) overwrites X-Forwarded-For with the real client IP,
        # so its last entry can't be forged. Behind a CDN this would be the CDN's IP.
        ip = (self.headers.get("X-Forwarded-For") or self.client_address[0]).split(",")[-1].strip()
        if limited(ip):
            return self.reply(429, {"error": "too many reports, try later"})
        try:
            r = clean(json.loads(self.rfile.read(n)))
        except (ValueError, OSError):
            r = None
        if not r:
            return self.reply(400, {"error": "bad report"})
        rid = time.strftime("%Y%m%d-%H%M%S") + "-" + os.urandom(2).hex()
        os.makedirs(os.path.join(STATE, "reports"), exist_ok=True)
        with open(os.path.join(STATE, "reports", f"{skill}-{rid}.json"), "w") as f:
            json.dump({**r, "skill": skill, "id": rid, "received": time.time()}, f, ensure_ascii=False, indent=1)
        env = " · ".join(f"{k}: {v}" for k, v in r["env"].items())
        sent = telegram(f"📮 {skill} {r['version']} · {r['kind']}\n{r['title']}\n\n{r['body']}\n\n{env}\nid {rid}")
        print(f"report {rid} {skill} {r['kind']} telegram={sent}", flush=True)
        self.reply(200, {"ok": True, "id": rid})


class Server(ThreadingHTTPServer):
    slots = threading.BoundedSemaphore(MAX_THREADS)

    def process_request(self, request, client_address):
        if not self.slots.acquire(blocking=False):
            return self.shutdown_request(request)   # busy: drop instead of piling up threads
        super().process_request(request, client_address)

    def process_request_thread(self, request, client_address):
        try:
            super().process_request_thread(request, client_address)
        finally:
            self.slots.release()


if __name__ == "__main__":
    load_hits()
    print(f"report relay on 127.0.0.1:{PORT}, skills: {', '.join(sorted(SKILLS))}, "
          f"{len(all_hits)} reports today", flush=True)
    Server(("127.0.0.1", PORT), H).serve_forever()
