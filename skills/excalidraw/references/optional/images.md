# Images via Codex — optional, only when needed

**Optional path.** Use it only if the user's machine has the Codex CLI
(`codex`) with image generation enabled (`image_generation` feature). Check
with `command -v codex`; if it's missing, skip this file — stamps and patterns
cover almost everything.

A raster illustration inside a diagram: a "hero", a metaphor that isn't among
the stamps. It costs ~1 minute per image, so **1–2 per diagram, no more**, and
only when stamps and patterns can't do the job. Any other image model works the
same way if the user has one; Codex is just the one that needs no API key.

## How

```bash
cd <generator folder>
cat > prompt.txt <<'EOF'
Use your image generation tool to create ONE image: hand-drawn Excalidraw
style sketch, thin black marker lines only, no shading, minimal, transparent
background, no text, no letters, single centered object. Subject: <what>.
Save the resulting PNG as ./<name>.png
EOF
codex exec --skip-git-repo-check -s workspace-write "$(cat prompt.txt)" < /dev/null
sips -Z 320 <name>.png --out <name>_small.png      # put the small one in the board
```

The prompt goes through a file with a quoted `'EOF'`, so quotes, `$(…)` or backticks in
the subject are never run by the shell. `< /dev/null` is required: without it codex waits for stdin. macOS has no `timeout`.
`sips` is macOS-only; elsewhere resize with any tool (e.g. ImageMagick `magick <name>.png -resize 320x320 <name>_small.png`).

Inserting into the scene — an `image` element plus an entry in `files` (push keeps them):

```python
import base64, hashlib
png = open("robot_small.png", "rb").read()
fid = hashlib.sha1(png).hexdigest()
files = {fid: {"mimeType": "image/png", "id": fid, "created": 1,
               "dataURL": "data:image/png;base64," + base64.b64encode(png).decode()}}
E.append(_base(type="image", x=x, y=y, width=140, height=140, fileId=fid,
               status="saved", scale=[1, 1], roundness=None, strokeColor="transparent"))
sc = scene(E); sc["files"] = files          # and json.dump(sc, …) instead of save()
```

## Pitfalls

- Codex's style is softer than a marker — a children's illustration with fills.
  Keep "thin marker lines only, no shading, minimal" in the prompt. One image is
  an accent; three or four are already a collage.
- A white background becomes a white square in the viewer's dark theme. Ask for
  a transparent background; if you didn't get one, warn the user.
- An image can't be edited on the board, unlike a stamp. Another reason to look
  for a stamp first.
