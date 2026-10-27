# Excalidraw skill for AI agents

[Русская версия](README.ru.md)

Your agent draws diagrams in Excalidraw: it plans the picture, generates the
scene in code, looks at the result through the real editor renderer, fixes what
looks wrong and hands you a link to a board you can keep editing by hand.

![Example: a diagram drawn by the skill](docs/example.png)

- **Hand-drawn, editable diagrams**, not images: every box and arrow stays an
  Excalidraw object you can move and edit.
- **It looks before it shows you.** Every diagram is rendered in headless Chromium
  with Excalidraw's own fonts, so clipped labels and overlaps get caught.
- **One board per conversation.** Each part of the board is a frame. Redrawing a
  part replaces only that frame, so your manual edits stay.
- **Mermaid too.** "Make it a mermaid sequence diagram" turns into an editable
  board, with no copy-pasting into dialogs.
- **450+ icons** from the Excalidraw libraries (people, databases, clouds,
  devices), stamped in instead of drawn from circles.
- **It learns your taste.** Corrections like "less color" or "database on the
  right" go into a small notes file and apply next time.

Works with any agent that supports [Agent Skills](https://agentskills.io): Claude
Code, OpenAI Codex, Gemini CLI, Cursor, GitHub Copilot, OpenCode, Amp, Goose,
Devin/Windsurf.

## Pick where your boards live

| | What you get | What you need |
|---|---|---|
| **Local** (default) | Boards are `.excalidraw` files in a folder on your computer. You view and edit them in a local board at `http://127.0.0.1:3200`. | Nothing extra |
| **Your own server** | A self-hosted [ExcaliDash](https://github.com/ZimengXiong/ExcaliDash): boards with links, history, login, sharing with your team | A small VPS with Docker, a domain |
| **Hosted board** | Same as your own server, without running one | Message the author (see below) |

You can switch later by re-running setup.

## Install

**Fastest, for any agent** (needs Node 22+):

```sh
npx skills add na-bal/excalidraw-skill
```

Or just give your agent this repo's link and say "install this skill". The
section below tells it what to do.

Per agent, by hand:

| Agent | Command or folder |
|---|---|
| Claude Code | `claude plugin marketplace add na-bal/excalidraw-skill` then `claude plugin install excalidraw@excalidraw-skill`, or copy `skills/excalidraw` into `~/.claude/skills/` |
| Codex, Cursor, Copilot, OpenCode, Amp, Goose, Devin | copy `skills/excalidraw` into `~/.agents/skills/` |
| Gemini CLI | `gemini skills install https://github.com/na-bal/excalidraw-skill --path skills/excalidraw` |
| Antigravity | copy `skills/excalidraw` into `~/.gemini/config/skills/` |

Then run setup once. Your agent will do it on first use if you don't:

```sh
bash ~/.agents/skills/excalidraw/scripts/setup.sh      # asks a couple of questions
```

Setup checks Python 3.10+ and Node 18+. It downloads a headless Chromium (~120 MB) into
Playwright's shared cache (reused if you already have it), writes `~/.config/excalidraw-skill/config` and
draws a test diagram. Nothing goes into the skill folder, so updating the skill
never breaks the install.

## For AI agents: how to install this skill

1. Pick the target folder: Claude Code → `~/.claude/skills/`; Antigravity →
   `~/.gemini/config/skills/`; any other agent → `~/.agents/skills/`.
   If `npx` is available, `npx skills add na-bal/excalidraw-skill -g -y -a <your-agent-id>`
   does steps 1–2 for you.
2. `git clone --depth 1 https://github.com/na-bal/excalidraw-skill /tmp/excalidraw-skill && cp -R /tmp/excalidraw-skill/skills/excalidraw <target>/`
3. Ask the user one question: local boards (default) or their own ExcaliDash
   server? Then run one of:
   - `bash <target>/excalidraw/scripts/setup.sh --backend local`
   - for ExcaliDash, ask the user to run it in their own terminal, so the key never
     passes through the chat: `bash <target>/excalidraw/scripts/setup.sh --backend excalidash --url <url>`
     (it asks for the key without showing it)
4. Success means setup printed `Ready.` and `~/.cache/excalidraw-skill/.ready` exists.
   Exit codes: 1 is a missing requirement (tell the user what to install), 3 is a
   failed smoke test (show the output).
5. Reload skills or restart: Claude Code `/reload-skills`, Gemini `/skills reload`,
   others need a restart.
6. Check: "draw a diagram of three boxes". You should get a board link.

Heads-up: setup downloads Chromium, so cloud sandboxes without network access
won't work.

## Running your own board server

The `excalidash` backend talks to [ExcaliDash](https://github.com/ZimengXiong/ExcaliDash).
It's a self-hosted Excalidraw with named boards, collections, version history,
login and API keys. Install it with Docker following its README, then create an
API key in its settings and run `setup.sh --backend excalidash`.

Tested with ExcaliDash 0.6.0. Things that cost time on a real install:

- **Behind a reverse proxy, set `TRUST_PROXY=2`**, not 1. That's two hops: your
  proxy (Caddy/nginx) plus nginx inside the frontend container. With 1, the
  backend sees the Docker gateway as every client, and the login rate limiter
  locks everyone out at once.
- **Several people on one server:** API keys are isolated (a key sees only its owner's
  boards and what was shared with them), but any logged-in user can look up other
  users by part of their email in the share dialog. Keep registration closed and
  create accounts yourself; for strangers, run one instance per person.
- **Set `API_KEY_HASH_PEPPER` before creating the first API key.** Changing it
  later invalidates every key.
- **Google login:** set `OIDC_JIT_PROVISIONING=false`. Otherwise any Google
  account gets an auto-created user with access to the boards.
- **New subdomain:** check the whole DNS zone, not just your record. Some
  registrar panels add extra A/AAAA records by themselves, and a stray AAAA
  breaks the Let's Encrypt http-01 check.
- **Small VPS:** 1 CPU and 1 GB RAM is enough. Set `mem_limit` on the containers
  if the machine runs anything else.

Two known rough edges in the editor:
- Trackpad two-finger pan zooms instead of panning (upstream PR #266, not merged
  yet).
- Shortcuts don't work on non-Latin keyboard layouts (fixed in ExcaliDash `dev`,
  not yet released).

The local board in this skill already has the keyboard fix.

## Hosted board

Don't want to run a server? I can host a board for you, with your own login and a
link to share with your team. Message me: Telegram [@Ohio_blue_tip](https://t.me/Ohio_blue_tip) or [bdlv@bdlv.me](mailto:bdlv@bdlv.me).

## Reporting problems

If something in the skill breaks, your agent offers to send a report to the
author. It shows you the full text first: the error and versions. Home paths,
keys, emails and IPs are stripped automatically. Nothing is sent without your
explicit yes, and no account is needed. The receiving end is in
[`server/report-relay`](server/report-relay), so you can see exactly where it goes.

You can also write to me directly: Telegram [@Ohio_blue_tip](https://t.me/Ohio_blue_tip) or
[bdlv@bdlv.me](mailto:bdlv@bdlv.me).

## Privacy

- **Local mode:** your drawings never leave your computer. The local board and
  the renderer load Excalidraw's code from public CDNs (esm.sh, jsdelivr), so
  first use needs internet. Your scenes are not sent anywhere.
- **Server mode:** scenes go only to the server you configured.
- The skill never uses excalidraw.com sharing unless you explicitly ask.

## What's inside

```
skills/excalidraw/
  SKILL.md            instructions for the agent
  scripts/setup.sh    install + configure + smoke test
  scripts/board.py    boards: push/get/list/open, local board server, frames
  scripts/scene.py    scene building blocks (box, connect, curve, code_card…)
  scripts/stamps.py   450+ icons from Excalidraw libraries
  scripts/mmd/        headless Excalidraw: Mermaid → scene, font fitting, screenshots
  scripts/viewer/     the local board page
  scripts/report.py   bug reports to the author, shown to you first
  scripts/welcome.py  your first board: a note from the author
server/report-relay/  the service that receives reports
  references/         patterns, recipes, Mermaid notes for the agent
```

Your data lives outside the skill: `~/.config/excalidraw-skill/` holds config,
`learned.md` and `usage.json`; `~/.cache/excalidraw-skill/` holds Playwright and
snapshots; the drawings folder is whatever you picked.

## License

MIT. Icon libraries come from [libraries.excalidraw.com](https://libraries.excalidraw.com)
(MIT); their authors are in the file names.
