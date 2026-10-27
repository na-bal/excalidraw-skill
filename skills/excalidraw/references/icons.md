# Icons (stamps)

24 libraries from libraries.excalidraw.com are bundled whole in `assets/libraries/`
(~6.6 MB, 475 icons). Don't read them yourself — `scripts/stamps.py` reads them
during generation. Each inserted icon adds ~4 KB to the scene; heavy ones (maps,
storyboards — up to 250 KB) only on purpose. Two more, `card` and `coin`, are
hand-made: their elements live right in `assets/quick.json` (there is no money icon
in the libraries).

```python
from stamps import stamp
E += stamp("db", x, y, w=60)                                  # quick — by name
E += stamp("moochin_simple-characters:Dragon", x, y, h=80)    # any — by key
E += stamp("xxxdeveloper_icons:code", x, y, w=40, bare=True)  # drop the "Code" caption
E += stamp("db", x, y, w=60, color="#1971c2", bg="#e7f5ff")    # recolor; on a colored zone
E += stamp("server", x, y, fit=(60, 60))                       # fit into a box, centered
```

An icon lands as one group.

- **Size.** `w=` sets the width, `h=` the height, the other side follows the
  aspect ratio. So `w=60` on a tall icon (`server`, stick figures,
  `it-icons:Device`) gives something twice as tall as you planned. When icons sit
  in a row or in slots, use `fit=(W, H)`: the icon fits inside the box and is
  centered in it. To know the size in advance:
  `from stamps import bbox; bx, by, bw, bh = bbox(stamp(name, 0, 0))`.
- **`bare=True`** drops the caption that repeats the icon's name: "Server" in
  `it-icons:Server`, "Code" under `xxxdeveloper_icons:code`. Glyphs that are part
  of the drawing stay (`>_`, the "PDF" tag, the kanban column titles, emoji "zZ").
  In quick stamps it's already on where the source has a caption (`server model
  internet key settings mic comment`) — check `"bare"` in `assets/quick.json` when
  adding one. Library icons by key have no default: pass `bare=True` yourself
  (most of `it-icons:*` and all `xxxdeveloper_icons:*` have one).
- **`color=`** recolors the strokes. White masks and transparent strokes keep their
  color, fills too.
- **`bg=`** — on a non-white background. Many icons hide lines behind white
  shapes: the back of `db`'s bottom ellipse, the joins of `cloud` and `thought`,
  the `speech` tail, white-filled heads of `moochin` characters, the folded corner
  of file icons. On a colored zone they show as white patches; `bg="#fff3bf"`
  (the zone's fill) paints all white and near-white strokes and fills that color. It also hits white
  drawn on purpose (the white "?" on the black disc of `Filled help`), so check the
  snapshot.

## Quick icons

`python3 scripts/stamps.py list` — 58 names with descriptions. To see them, render
a sheet: `STAMPS_NO_USAGE=1 python3 scripts/quick_sheet.py quick.excalidraw`, then
snapshot it with `node scripts/mmd/shot.mjs quick.excalidraw quick.png`.

People and emotions: `person person-talk person-think woman shrug happy sad hand-up
not-sure presenting whiteboard person-laptop idea annoyed confused look
making-point wave kanban group user face-smile face-sad speech thought`.
Data and tech: `db cloud server doc files folder model robot laptop phone
internet key settings mic comment`. Process and status: `start finish target filter
lightning magic clock check cross warning question mail send bar-chart line-chart bulb`.
Money: `card coin` (hand-made).

## What else is there — where to look

`stamps.py find <word>` searches all keys, `stamps.py libs` counts icons per library.

| Library | What's in it | When to use |
| --- | --- | --- |
| `moochin_simple-characters` | 49 characters in situations: juggling, dragon, collapsing tower, toolbox, time travel, gift, superhero | illustration, metaphor, the emotion of a process — **check first** |
| `mateuszbaransanok_it-icons` | 48 thin IT icons: host, network, firewall, BPMN gateways, event, error, camera, printer, timer, video | architecture, BPMN, infrastructure |
| `youritjang_stick-figures`, `dhtoran_stick-people` | stick figures: child, grandma, guy, girl, with a hat, with a mustache | roles and people |
| `anumithaapollo12_emojis` | 48 faces, yellow and outlined; keys are numbers — see the map below | customer journey, mood of stages |
| `xxxdeveloper_icons` | 65 file icons with colored tags: pdf, sql, js, python… | when the data format matters |
| `xxxdeveloper_system-icons` | 24 bold icons: tree, star, 3D cube, app, cleanup | processes, product |
| `artem-anufrij-live-de_artem-s-icons` | 22: organization, process, devices, statuses | general |
| `office-items`, `clocks`, `robots`, `bubbles`, `banners` | microphone, headset, parcel; alarm clock, clocks; 7 robots; 4 bubbles; 7 header ribbons | by name |
| `aocgame_domainstorytelling` | 7 bold black ones: person, group, system, mail | domain storytelling; stylistically stands out |
| `arach_systems-design-components` | cloud, stream, servers, DB | system design |
| `kwirke_some-handdrawn-signs` | hand-drawn check mark and cross | statuses |

### Emoji map

`anumithaapollo12_emojis:#N` has no names. Yellow #0–23, outlined #24–47 — the
same faces in **a different order**:

| Face | Yellow | Outlined |
| --- | --- | --- |
| smile | 0 (= `face-smile`) | 24 |
| surprised, "o" mouth | 1 | 25 |
| neutral, straight mouth | 2 | 26 |
| no mouth | 3 | 27 |
| laughing, `> <` eyes | 4 | 28 |
| expressionless, `- -` eyes | 5 | 29 |
| upset, wavy frown | 6 | 30 |
| heart eyes | 7 | 33 |
| wink | 8 | 34 |
| kiss with a heart | 9 | 35 |
| content, closed eyes, smile | 10 | 36 |
| angry, brows | 11 | 37 |
| sad, small frown | 12 (= `face-sad`) | 38 |
| disappointed, closed eyes, frown | 13 | 39 |
| top hat | 14 | 40 |
| in love, hearts around | 15 | 42 |
| star eyes | 16 | 41 |
| dizzy, `x x` eyes, "o" mouth | 17 | 43 |
| cool, sunglasses | 18 | 44 |
| sleepy, "zZ" (smaller than the rest) | 19 | 45 |
| goggle eyes, grin | 20 | 46 |
| crying, streams of tears | 21 | 47 |
| worried, nauseous | 22 | 31 |
| tired, `> <` eyes, frown | 23 | 32 |

**Interfaces — a separate set**, for wireframes rather than diagrams:
`spfr_lo-fi-wireframing-kit` (buttons, fields, cards, tables, tabs, hero, sidebar,
alerts, forms), `manuelernestog_universal-ui-kit` (calendar, charts, progress,
avatar), `gabrielamacakova_basic-ux-wireframing-elements` (69: toggles,
dropdowns, tooltips, modal), `dhaval_godwani_webpage-frames`, `excacomp_mobile-kit`,
`excacomp_web-kit`, `franky47_apple-devices-frames`, `marwinburesch_html-input-elements`.

## The quick list evolves

`stamp()` remembers which icons were used in which diagrams (`usage.json` in
`$EXCALIDRAW_SKILL_CONFIG_DIR`, by default `~/.config/excalidraw-skill`; diagram = generator script, so re-running it doesn't inflate the count).

- A non-quick icon used in **3 different diagrams** — the generator prints
  "candidate for quick". Suggest to the user adding it to `quick.json`.
- `stamps.py stats` shows the reverse too: quick icons not used in the last
  **20** diagrams are candidates for removal.
- The user decides. Review when `stats` reports something, not on a schedule.

Run catalogs and previews with `STAMPS_NO_USAGE=1`, otherwise they count everything.

## For the user

`assets/quick.excalidrawlib` — the quick icons as an Excalidraw library. Load it
once into the Library panel of your Excalidraw, and they're at hand when editing
manually. After editing `quick.json`, rebuild it:
`STAMPS_NO_USAGE=1 python3 scripts/stamps.py export assets/quick.excalidrawlib`.
