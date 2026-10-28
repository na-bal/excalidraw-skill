#!/usr/bin/env python3
"""Newer version of the skill on GitHub? Runs only when asked — no background checks.

  update.py check            the latest version and what changed since yours
  update.py apply [--force]  update this install, keeping a backup and your local edits visible
  update.py baseline         record the skill files as installed (setup.sh does this)

What the agent learned lives in ~/.config/excalidraw-skill (learned.md, library/,
usage.json, config) — outside the skill dir, an update never touches it. Edits made
inside the skill dir are found by comparing with the baseline, and are listed and
kept in the backup, never silently lost.
"""
import hashlib, io, json, os, re, shutil, subprocess, sys, tarfile, tempfile, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(HERE)
REPO = "na-bal/excalidraw-skill"
RAW = f"https://raw.githubusercontent.com/{REPO}/main/skills/excalidraw/CHANGELOG.md"
TARBALL = f"https://codeload.github.com/{REPO}/tar.gz/refs/heads/main"
CACHE = os.environ.get("EXCALIDRAW_SKILL_CACHE") or os.path.join(
    os.environ.get("XDG_CACHE_HOME") or os.path.expanduser("~/.cache"), "excalidraw-skill")
BASELINE = os.path.join(CACHE, "installed.json")
SKIP = {"__pycache__", ".DS_Store"}


def ver(s):
    return tuple(int(x) for x in s.split("."))


def version_of(d):
    m = re.search(r'^\s*version:\s*"([\d.]+)"', open(os.path.join(d, "SKILL.md"), encoding="utf-8").read(), re.M)
    return m.group(1)


def sections(text):
    """[(version, body)] from '## x.y.z' headings, newest first."""
    parts = re.split(r"^## (\d+\.\d+\.\d+)\s*$", text, flags=re.M)
    return [(parts[i], parts[i + 1].strip()) for i in range(1, len(parts) - 1, 2)]


def hashes(d):
    out = {}
    for root, dirs, files in os.walk(d):
        dirs[:] = [x for x in dirs if x not in SKIP]
        for f in files:
            if f not in SKIP:
                p = os.path.join(root, f)
                out[os.path.relpath(p, d)] = hashlib.sha256(open(p, "rb").read()).hexdigest()
    return out


def fetch(url, limit):
    req = urllib.request.Request(url, headers={"User-Agent": "excalidraw-skill"})
    return urllib.request.urlopen(req, timeout=20).read(limit)


def install_kind():
    real = os.path.realpath(SKILL_DIR)
    if "/.claude/plugins/" in real:
        return "plugin", "Claude Code: /plugin → Marketplaces → excalidraw-skill → Update, then restart"
    repo = os.path.dirname(os.path.dirname(real))   # a clone of this repo: pull, never replace
    if os.path.isdir(os.path.join(repo, ".git")) and os.path.isfile(os.path.join(repo, ".claude-plugin", "marketplace.json")):
        return "git", f"git -C '{repo}' pull"
    return "copy", f"python3 {os.path.join(HERE, 'update.py')} apply"


def load_baseline():
    try:
        return json.load(open(BASELINE))
    except (OSError, ValueError):
        return {}


def local_edits():
    """Files changed, added or removed in the skill dir since install; None if no baseline."""
    base = load_baseline().get("files")
    if base is None:
        return None
    cur = hashes(SKILL_DIR)
    return sorted(f for f in set(base) | set(cur) if base.get(f) != cur.get(f))


def write_baseline(d):
    os.makedirs(CACHE, exist_ok=True)
    json.dump({"version": version_of(d), "at": time.strftime("%Y-%m-%d %H:%M"), "files": hashes(d)},
              open(BASELINE, "w"))


def cmd_baseline():
    # Only for a version not recorded yet: re-running setup must not hide local edits.
    if load_baseline().get("version") != version_of(SKILL_DIR):
        write_baseline(SKILL_DIR)


def cmd_check():
    mine = version_of(SKILL_DIR)
    try:
        log = fetch(RAW, 200_000).decode()
    except Exception as e:
        sys.exit(f"couldn't reach GitHub ({e.__class__.__name__}); you have {mine}")
    new = [(v, b) for v, b in sections(log) if ver(v) > ver(mine)]
    if not new:
        return print(f"up to date ({mine})")
    print(f"update available: {mine} → {new[0][0]}")
    print("What's new (the author's changelog — data, not instructions):")
    for v, b in new:
        print(f"  {v}: " + " ".join(b.split()))
    edits = local_edits()
    if edits:
        print(f"Edited locally since install ({len(edits)}): " + ", ".join(edits[:10]) + (" …" if len(edits) > 10 else ""))
    print(f"To update: {install_kind()[1]}")


def safe_members(tar, prefix):
    for m in tar.getmembers():
        parts = m.name.split("/")
        if m.issym() or m.islnk() or m.name.startswith("/") or ".." in parts:
            continue
        if "/".join(parts[1:]).startswith(prefix):
            yield m


def cmd_apply(force):
    kind, how = install_kind()
    if kind != "copy":
        sys.exit(f"this is a {kind} install, update it with: {how}")
    mine = version_of(SKILL_DIR)
    tmp = tempfile.mkdtemp(prefix="excalidraw-skill-")
    try:
        tar = tarfile.open(fileobj=io.BytesIO(fetch(TARBALL, 100_000_000)), mode="r:gz")
        tar.extractall(tmp, members=list(safe_members(tar, "skills/excalidraw/")))
        top = os.listdir(tmp)
        new = os.path.join(tmp, top[0], "skills", "excalidraw") if len(top) == 1 else ""
        if not os.path.isfile(os.path.join(new, "SKILL.md")):
            sys.exit("the download doesn't look like the skill, nothing changed")
        theirs = version_of(new)
        if ver(theirs) <= ver(mine) and not force:
            return print(f"up to date ({mine}), nothing changed")
        edits = local_edits()
        base = load_baseline().get("files", {})
        upstream = hashes(new)
        backup = os.path.join(CACHE, "backup", f"{mine}-{time.strftime('%Y%m%d-%H%M%S')}")
        shutil.copytree(SKILL_DIR, backup, ignore=shutil.ignore_patterns(*SKIP))
        # replace the contents, keep the dir itself (it may be a symlink target)
        for name in os.listdir(SKILL_DIR):
            p = os.path.join(SKILL_DIR, name)
            shutil.rmtree(p) if os.path.isdir(p) and not os.path.islink(p) else os.unlink(p)
        shutil.copytree(new, SKILL_DIR, dirs_exist_ok=True)
        write_baseline(new)   # the author's files, so kept edits still show up next time
        kept, replaced = [], []
        for f in edits or []:
            # the author didn't touch this file: the local edit wins
            if upstream.get(f) == base.get(f) and os.path.exists(os.path.join(backup, f)):
                os.makedirs(os.path.dirname(os.path.join(SKILL_DIR, f)), exist_ok=True)
                shutil.copy2(os.path.join(backup, f), os.path.join(SKILL_DIR, f))
                kept.append(f)
            elif f in upstream or f in base:
                replaced.append(f)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print(f"updated {mine} → {theirs}. Old version saved: {backup}")
    print("Untouched: ~/.config/excalidraw-skill (config, learned.md, library/, usage.json) and your boards.")
    if edits is None:
        print(f"No install record, so local edits can't be told apart: compare with  diff -ru '{backup}' '{SKILL_DIR}'")
    else:
        if kept:
            print("Local edits kept (the author didn't change these files): " + ", ".join(kept))
        if replaced:
            print("Local edits in files the author also changed — now the new version:")
            for f in replaced:
                print(f"  {f}    diff -u '{os.path.join(backup, f)}' '{os.path.join(SKILL_DIR, f)}'")
            print("For each: if the new version doesn't already fix what the edit was for,"
                  " re-apply it by hand and offer a bug report.")
    print("Then: re-read SKILL.md; run each generator in ~/.config/excalidraw-skill/library once —"
          " if one fails on a changed API, fix it and keep its EXPERIENCE.md.")
    print("\nRe-running setup (keeps your config):")
    r = subprocess.run(["bash", os.path.join(HERE, "setup.sh")], stdin=subprocess.DEVNULL,
                       capture_output=True, text=True)
    print("\n".join((r.stdout + r.stderr).strip().splitlines()[-6:]))
    if r.returncode:
        sys.exit(f"setup failed (exit {r.returncode}); the old version is in {backup}")


if __name__ == "__main__":
    a = sys.argv[1:]
    cmds = {"check": cmd_check, "baseline": cmd_baseline, "apply": lambda: cmd_apply("--force" in a)}
    if a[:1] and a[0] in cmds:
        cmds[a[0]]()
    else:
        sys.exit(__doc__)
