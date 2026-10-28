# Anthropic plugin directory — submission answers

Form: claude.ai/directory/manage. Submitted by the owner.

**Repository:** https://github.com/na-bal/excalidraw-skill
**Plugin name:** `agent-whiteboard` (marketplace `excalidraw-skill`). The first
try with `excalidraw` was held: the name belongs to the Excalidraw brand.
**Version:** 1.1.3 · **License:** MIT · **Homepage:** the repo
**Support contact:** bdlv@bdlv.me (also Telegram @Ohio_blue_tip)
**Privacy:** https://github.com/na-bal/excalidraw-skill#privacy

## Short description (≤ 1 line)

Your agent draws hand-drawn Excalidraw diagrams on a real board you can edit — and it learns from your edits.

## Long description

Agents are great at code and pretty bad at drawing. This skill fixes that: ask
for an architecture diagram, flowchart, sequence, swimlane, user journey,
roadmap, mind map or comparison and get a clean, hand-drawn Excalidraw scene on
a real board — not a picture. Fix it by hand; next time the agent reads the
diff of your edits and keeps your layout and style.

Boards live on your computer (a local board at 127.0.0.1, plain .excalidraw
files) or on your own self-hosted ExcaliDash server. Mermaid code turns into an
editable board too. The agent checks every diagram with the real Excalidraw
renderer before showing it, so labels don't clip and arrows meet their shapes.

## Category

Productivity / Design (whichever exists; "Developer tools" as a fallback).

## Data handling

- **Collects personal data?** No.
- **Sends data off the device?** Only in these cases:
  - Excalidraw's code is loaded from public CDNs (esm.sh, cdn.jsdelivr.net) by
    the local board and the headless renderer; setup downloads Chromium
    (Playwright) and npm packages once.
  - Server mode: scenes go only to the ExcaliDash server the user configured.
  - Updates: downloaded from GitHub only when the user asks.
  - Bug reports: only after the agent shows the user the exact text and the user
    confirms. The report is stripped of paths, hostnames and secrets and never
    contains board contents. It goes to the author's relay (report.bdlv.me),
    which forwards it to the author.
- **Retention:** reports are kept on the author's server for the author to
  read; no analytics, no tracking. *(If auto-delete is added: "deleted after
  180 days".)*
- **Third parties:** none besides the CDNs and GitHub above.
- **Intended for users under 18?** No.
- **Authentication / API keys:** none for local mode. Server mode uses the
  user's own ExcaliDash API key, entered by the user in their terminal and
  stored in `~/.config/excalidraw-skill/config` (mode 600); never sent to the
  chat.

## Requirements / compatibility

Claude Code (CLI, desktop). Needs Python 3.10+, Node 18+ and network on first
run; downloads a headless Chromium (~120 MB). Not for claude.ai web chat or
sandboxes without network access. Tested on macOS; Linux should work.

## Known review points

- Files over 256 KiB (icon libraries in `skills/excalidraw/assets/libraries/`,
  README images in `docs/`) — reviewer hold, not a rejection. All under 5 MiB.
- Network calls listed above are all from scripts in the repo; nothing runs
  on install (`npm ci --ignore-scripts`).
