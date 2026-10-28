#!/usr/bin/env bash
# Install and configure the excalidraw skill. Safe to re-run.
#
# Agents: run non-interactively with flags. Humans: run with no flags for questions.
#
#   setup.sh --backend local [--dir ~/Drawings/excalidraw] [--port 3200]
#   setup.sh --backend excalidash --url https://draw.example.com   (key from $EXCALIDASH_API_KEY)
#   setup.sh --check          only report what's installed and configured
#   setup.sh --skip-browser   don't download Chromium (screenshots and push won't work)
#   setup.sh --no-open        don't open the Welcome board in the browser at the end
#
# Installs playwright-core into ~/.cache/excalidraw-skill, Chromium headless shell
# (~120 MB) into Playwright's shared browser cache (reused if already there), and
# writes ~/.config/excalidraw-skill/config. Nothing goes into the skill dir.
# Exit codes: 0 ready, 1 missing requirement, 2 bad arguments, 3 smoke test failed.
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
CACHE="${EXCALIDRAW_SKILL_CACHE:-${XDG_CACHE_HOME:-$HOME/.cache}/excalidraw-skill}"
CONF_DIR="${EXCALIDRAW_SKILL_CONFIG_DIR:-${XDG_CONFIG_HOME:-$HOME/.config}/excalidraw-skill}"
CONFIG="$CONF_DIR/config"

BACKEND="" DRAWINGS="" PORT="" URL="" CHECK=0 SKIP_BROWSER=0 NO_OPEN=0
while [ $# -gt 0 ]; do
  case "$1" in
    --backend) BACKEND="$2"; shift 2 ;;
    --dir) DRAWINGS="$2"; shift 2 ;;
    --port) PORT="$2"; shift 2 ;;
    --url) URL="$2"; shift 2 ;;
    --check) CHECK=1; shift ;;
    --skip-browser) SKIP_BROWSER=1; shift ;;
    --no-open) NO_OPEN=1; shift ;;
    -h|--help) sed -n '2,15p' "$0"; exit 0 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

ok()   { printf '  \033[32m✓\033[0m %s\n' "$*"; }
bad()  { printf '  \033[31m✗\033[0m %s\n' "$*"; }
step() { printf '\n\033[1m%s\033[0m\n' "$*"; }
ask()  { local q="$1" def="$2" ans; read -r -p "$q [$def]: " ans; echo "${ans:-$def}"; }
TTY=0; [ -t 0 ] && [ -t 1 ] && TTY=1   # agents have no tty: never prompt them

if [ $TTY -eq 1 ] && [ $CHECK -eq 0 ]; then
  printf '\n  \033[1mexcalidraw skill\033[0m  ·  your agent draws, you fix by hand, it learns\n'
  printf '  \033[2mby Alexander Bedelev · github.com/na-bal/excalidraw-skill\033[0m\n'
fi

# ── 1. Requirements ────────────────────────────────────────────────────
step "1/4 Requirements"
missing=0
if command -v python3 >/dev/null && python3 -c 'import sys; sys.exit(sys.version_info < (3, 10))'; then
  ok "python3 $(python3 -c 'import platform; print(platform.python_version())')"
else
  bad "python3 3.10+ not found (macOS ships 3.9: brew install python@3.12, or uv python install 3.12)"; missing=1
fi
if command -v node >/dev/null && [ "$(node -p 'process.versions.node.split(".")[0]')" -ge 18 ]; then
  ok "node $(node -v)"
else
  bad "node 18+ not found (22+ recommended): brew install node, or https://nodejs.org"; missing=1
fi
command -v npm >/dev/null && ok "npm $(npm -v)" || { bad "npm not found"; missing=1; }
[ $missing -eq 0 ] || { echo "Install the missing tools and re-run." >&2; exit 1; }

# ── 2. Playwright + Chromium ───────────────────────────────────────────
step "2/4 Headless browser (renders and measures text with real Excalidraw fonts)"
NODE_DIR="$CACHE/node"
if [ $CHECK -eq 1 ]; then
  [ -d "$NODE_DIR/node_modules/playwright-core" ] && ok "playwright-core in $NODE_DIR" || bad "playwright-core not installed"
else
  mkdir -p "$NODE_DIR"
  cp "$DIR/mmd/package.json" "$DIR/mmd/package-lock.json" "$NODE_DIR/"
  STAMP="$NODE_DIR/node_modules/.skill-lock.json"
  if cmp -s "$NODE_DIR/package-lock.json" "$STAMP" 2>/dev/null \
     || { (cd "$NODE_DIR" && npm ci --silent --no-audit --no-fund --ignore-scripts) && cp "$NODE_DIR/package-lock.json" "$STAMP"; }; then
    ok "playwright-core in $NODE_DIR"
  else
    bad "npm ci failed"; exit 1
  fi
  if [ $SKIP_BROWSER -eq 0 ]; then
    node "$NODE_DIR/node_modules/playwright-core/cli.js" install chromium-headless-shell >/dev/null \
      && ok "Chromium headless shell" || { bad "Chromium download failed (network?)"; exit 1; }
  fi
fi

# ── 3. Where boards live ───────────────────────────────────────────────
step "3/4 Boards"
if [ $CHECK -eq 1 ]; then
  [ -f "$CONFIG" ] && { ok "config: $CONFIG"; grep -v '^EXCALIDASH_API_KEY' "$CONFIG" | sed 's/^/      /'; } \
    || bad "no config — run setup.sh --backend local"
else
  if [ -z "$BACKEND" ] && [ -f "$CONFIG" ]; then
    ok "keeping existing config $CONFIG (pass --backend to change it)"
  else
    if [ -z "$BACKEND" ]; then
      if [ $TTY -eq 1 ]; then
        echo "  local       — boards are files on this computer, opened in a local board (no server)"
        echo "  excalidash  — your own ExcaliDash server, or a hosted board someone gave you"
        BACKEND="$(ask "  Backend" local)"
      else
        BACKEND=local
      fi
    fi
    mkdir -p "$CONF_DIR"
    case "$BACKEND" in
      local)
        if [ -z "$DRAWINGS" ]; then
          DRAWINGS="$HOME/Drawings/excalidraw"
          [ $TTY -eq 1 ] && DRAWINGS="$(ask "  Folder for drawings" "$DRAWINGS")"
        fi
        DRAWINGS="${DRAWINGS/#\~/$HOME}"
        mkdir -p "$DRAWINGS"
        printf 'BACKEND=local\nDRAWINGS_DIR=%s\nLOCAL_PORT=%s\n' "$DRAWINGS" "${PORT:-3200}" > "$CONFIG"
        ok "local boards in $DRAWINGS" ;;
      excalidash)
        if [ -z "$URL" ]; then
          [ $TTY -eq 1 ] || { bad "pass --url"; exit 2; }
          URL="$(ask "  ExcaliDash URL" "https://")"
        fi
        KEY="${EXCALIDASH_API_KEY:-}"
        if [ -z "$KEY" ]; then
          [ $TTY -eq 1 ] || { bad "set EXCALIDASH_API_KEY in the environment"; exit 2; }
          read -r -s -p "  API key (Settings → API keys in ExcaliDash): " KEY; echo
        fi
        # new file each time: an existing config may have been created world-readable
        TMPC="$(umask 077; mktemp "$CONF_DIR/.config.XXXXXX")"
        printf 'BACKEND=excalidash\nEXCALIDASH_URL=%s\nEXCALIDASH_API_KEY=%s\n' "${URL%/}" "$KEY" > "$TMPC"
        mv -f "$TMPC" "$CONFIG"
        ok "ExcaliDash at ${URL%/}" ;;
      *) bad "backend must be local or excalidash"; exit 2 ;;
    esac
  fi
  touch "$CONF_DIR/learned.md"
  mkdir -p "$CONF_DIR/library"
  # a fresh install has nothing "new" to announce
  [ -f "$CONF_DIR/.seen-version" ] || sed -n 's/^  version: "\(.*\)"/\1/p' "$DIR/../SKILL.md" > "$CONF_DIR/.seen-version"
fi

# ── 4. Smoke test ──────────────────────────────────────────────────────
step "4/4 Smoke test"
[ $CHECK -eq 1 ] && { [ -f "$CACHE/.ready" ] && ok "ready since $(cat "$CACHE/.ready")" || bad "not ready"; exit 0; }
SMOKE="$CACHE/smoke.excalidraw"
python3 "$DIR/smoke.py" "$SMOKE" >/dev/null && ok "scene generated" || { bad "scene.py failed"; exit 3; }
if [ $SKIP_BROWSER -eq 0 ]; then
  node "$DIR/mmd/fittext.mjs" "$SMOKE" >/dev/null && ok "text fitted with Excalidraw fonts" || { bad "fittext failed"; exit 3; }
  node "$DIR/mmd/shot.mjs" "$SMOKE" "$CACHE/smoke.png" >/dev/null && ok "screenshot: $CACHE/smoke.png" || { bad "screenshot failed"; exit 3; }
fi
B="$(grep '^BACKEND=' "$CONFIG" | cut -d= -f2)"
if [ "$B" = excalidash ]; then
  python3 "$DIR/board.py" list >/dev/null && ok "server reachable, key accepted" || { bad "server check failed"; exit 3; }
elif [ $SKIP_BROWSER -eq 0 ] && [ -z "$(python3 "$DIR/board.py" list)" ]; then
  WELCOME="$CACHE/welcome.excalidraw"
  STAMPS_NO_USAGE=1 python3 "$DIR/welcome.py" "$WELCOME" >/dev/null
  WELCOME_URL="$(python3 "$DIR/board.py" push "$WELCOME" --name "Welcome" | grep -o 'http[^ ]*' | head -1)"
  [ -n "$WELCOME_URL" ] && ok "first board created: $WELCOME_URL"
fi
date '+%Y-%m-%d %H:%M' > "$CACHE/.ready"
python3 "$DIR/update.py" baseline   # lets an update tell local edits from the author's files

echo
echo "Ready. Boards: $(python3 "$DIR/board.py" where | sed -n 's/^board: *//p')"
if [ "$B" = local ]; then
  # Show the board right away: a bare "Ready." made agents end the install there.
  W_ID="${WELCOME_URL:+${WELCOME_URL##*#}}"
  if [ $NO_OPEN -eq 0 ] && [ ! -f "$CONF_DIR/.onboarded" ]; then
    python3 "$DIR/board.py" open $W_ID >/dev/null && ok "opened in the browser: ${WELCOME_URL:-local board}"
  else
    echo "Open the local board: python3 $DIR/board.py open $W_ID"
  fi
fi
if [ ! -f "$CONF_DIR/.onboarded" ] && [ $TTY -eq 0 ]; then
  cat <<EOF

AGENT: the install is not finished until you do this, in this conversation
(full text: "Right after install" in $(cd "$DIR/.." && pwd)/SKILL.md):
  1. Tell the user, in their language, that the Welcome board is open and what
     the skill does (four short points from that section).
  2. Ask where boards should live: this computer / their own server / help with
     hosting from the author. Then touch $CONF_DIR/.onboarded
  3. Offer a first drawing right now — don't send them to a new session.
EOF
fi
