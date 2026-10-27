#!/usr/bin/env python3
"""Report a problem with this skill to its author — only with the user's consent.

  report.py draft --kind bug --title "push fails on …" --body-file what.txt [--agent "Claude Code"]
      builds the report, strips secrets and personal paths, saves it and prints
      EXACTLY what will be sent. Show that to the user.
  report.py send <draft.json>
      sends it after the user said yes. No account needed on their side.

kind: bug (a script failed or misbehaved), install (had to install or fix something
to make it work), docs (the instructions were wrong or missing), lesson (a general
drawing lesson the user wants to share), other.
Never put board contents, keys or private data into --body.
"""
import argparse, getpass, hashlib, json, os, platform, re, socket, subprocess, sys, time, urllib.error, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from board import CACHE, CONFIG, LEGACY, read_kv   # noqa: E402

URL = os.environ.get("EXCALIDRAW_SKILL_REPORT_URL") or "https://report.bdlv.me/excalidraw-skill"
DRAFTS = os.path.join(CACHE, "reports")
HOME = os.path.expanduser("~")


def version():
    m = re.search(r'^\s*version:\s*"?([\w.\-]+)', open(os.path.join(HERE, "..", "SKILL.md")).read(), re.M)
    return m.group(1) if m else "?"


def private_strings():
    """Things that identify this user or their setup, longest first: server host, boards
    folder, user and machine names."""
    out = set()
    for path in (CONFIG, LEGACY):
        if os.path.exists(path):
            c = read_kv(path)
            for v in (c.get("EXCALIDASH_URL"), c.get("DRAWINGS_DIR")):
                if v:
                    out.add(v.rstrip("/"))
                    host = urllib.parse.urlparse(v if "://" in v else "//" + v).hostname
                    if host and "." in host:
                        out.add(host)
    for v in (os.path.realpath(HOME), HOME, os.path.basename(HOME), getpass.getuser(), socket.gethostname(),
              socket.gethostname().split(".")[0]):
        if v and len(v) >= 3:
            out.add(v)
    return sorted(out, key=len, reverse=True)


def redact(s):
    for v in private_strings():
        s = re.sub(r"(?<![\w.\-])" + re.escape(v) + r"(?![\w\-])", "<private>", s)
    s = re.sub(r"(?i)(api[_-]?key|token|secret|password|passwd|bearer|authorization)(\s*[=:]\s*|\s+)\S+",
               r"\1\2<redacted>", s)
    s = re.sub(r"\bexd_[A-Za-z0-9_\-]+", "<redacted>", s)
    s = re.sub(r"\b(AKIA|ghp_|gho_|github_pat_|sk-|xox[bp]-)[A-Za-z0-9_\-]+", "<redacted>", s)
    s = re.sub(r"\beyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-.]+", "<redacted>", s)          # JWT
    s = re.sub(r"\b[A-Za-z0-9_\-]{24,}\b", "<redacted>", s)
    s = re.sub(r"://[^/\s:@]+:[^/\s@]+@", "://<redacted>@", s)                      # user:pass@host
    s = re.sub(r"(/Users/|/home/|/Volumes/)[^/\s]+", r"\1<private>", s)
    s = re.sub(r"[^\s/]+\.excalidraw\b", "<board>.excalidraw", s)
    s = re.sub(r"[\w.+\-]+@[\w\-]+\.[\w.\-]+", "<email>", s)
    s = re.sub(r"\b\d{1,3}(\.\d{1,3}){3}\b", "<ip>", s)
    s = re.sub(r"\b(?:[0-9a-fA-F]{1,4}:){3,7}[0-9a-fA-F]{1,4}\b", "<ip>", s)        # IPv6, MAC
    s = re.sub(r"\b[\w\-]+\.local\b", "<host>", s)
    return s


def clean(r):
    """Redact every field — run on draft and again on send."""
    return {"kind": r["kind"], "title": redact(r["title"])[:140], "body": redact(r["body"])[:15000],
            "version": r["version"], "env": {k: redact(str(v))[:80] for k, v in r["env"].items()}}


def digest(r):
    return hashlib.sha256(json.dumps(r, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:12]


def show(r):
    return (f"[{r['kind']}] {r['title']}\nskill {r['version']} · " +
            " · ".join(f"{k}: {v}" for k, v in r["env"].items()) + f"\n\n{r['body']}")


def tool_version(cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=10).stdout.strip().splitlines()[0]
    except (OSError, IndexError, subprocess.TimeoutExpired):
        return "missing"


def cmd_draft(a):
    conf = read_kv(CONFIG) if os.path.exists(CONFIG) else {}
    body = open(a.body_file, encoding="utf-8").read() if a.body_file else (a.body or "")
    if not body.strip():
        sys.exit("empty report: pass --body or --body-file")
    check = subprocess.run(["bash", os.path.join(HERE, "setup.sh"), "--check"], capture_output=True,
                           text=True, stdin=subprocess.DEVNULL, timeout=60)
    check = re.sub(r"\x1b\[[0-9;]*m", "", check.stdout + check.stderr).strip()
    body = f"{body.strip()}\n\n--- setup.sh --check ---\n{check}"
    r = clean({"kind": a.kind, "title": a.title, "body": body, "version": version(),
         "env": {"os": f"{platform.system()} {platform.release()} {platform.machine()}",
                 "python": platform.python_version(), "node": tool_version(["node", "-v"]),
                 "backend": conf.get("BACKEND", "none"), "agent": a.agent or "unknown"}})
    os.makedirs(DRAFTS, exist_ok=True)
    path = os.path.join(DRAFTS, f"draft-{time.strftime('%Y%m%d-%H%M%S')}.json")
    json.dump(r, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    open(path[:-5] + ".md", "w", encoding="utf-8").write(r["body"])   # for gh / sending by hand
    print(f"=== This is everything that will be sent to the skill's author ===\n{show(r)}\n=== end ===\n"
          f"draft: {path}\nSend only after the user says yes: report.py send {path} --confirm {digest(r)}")


def cmd_send(a):
    r = clean(json.load(open(a.draft, encoding="utf-8")))
    if a.confirm != digest(r):
        print(show(r))
        sys.exit(f"\nThe draft is not what was shown (or --confirm is missing). Show the text above to the "
                 f"user; if they agree: report.py send {a.draft} --confirm {digest(r)}")
    req = urllib.request.Request(URL, data=json.dumps(r).encode(), method="POST",
                                 headers={"Content-Type": "application/json",
                                          "User-Agent": f"excalidraw-skill/{r.get('version')}"})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            rid = json.loads(resp.read()).get("id")
        for ext in (".json", ".md"):
            src = a.draft[:-5] + ext
            if os.path.exists(src):
                os.replace(src, src.replace("draft-", "sent-"))
        print(f"sent, report id {rid}. Thank you!")
        return
    except urllib.error.HTTPError as e:
        err = f"HTTP {e.code}: {e.read()[:200].decode(errors='replace')}"
    except OSError as e:
        err = str(e)
    print(f"could not send ({err}).")
    if tool_version(["gh", "auth", "status"]) != "missing":
        print("GitHub CLI is available: with the user's ok, file it as an issue —\n"
              f"  gh issue create -R na-bal/excalidraw-skill --title {json.dumps(r['title'])} --body-file {a.draft[:-5]}.md")
    print(f"Or the user can send the draft file by hand: {a.draft} — Telegram @Ohio_blue_tip or bdlv@bdlv.me.")
    sys.exit(1)


p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
sub = p.add_subparsers(dest="cmd", required=True)
d = sub.add_parser("draft")
d.add_argument("--kind", required=True, choices=["bug", "install", "docs", "lesson", "other"])
d.add_argument("--title", required=True)
d.add_argument("--body"); d.add_argument("--body-file"); d.add_argument("--agent")
d.set_defaults(fn=cmd_draft)
s = sub.add_parser("send"); s.add_argument("draft"); s.add_argument("--confirm", help="code printed by draft")
s.set_defaults(fn=cmd_send)

if __name__ == "__main__":
    a = p.parse_args()
    a.fn(a)
