# Icons (stamps)

24 libraries from libraries.excalidraw.com are bundled whole in `assets/libraries/`
(~6.6 MB, 475 icons). Don't read them yourself — `scripts/stamps.py` reads them
during generation. Each inserted icon adds ~4 KB to the scene; heavy ones (maps,
storyboards — up to 250 KB) only on purpose.

```python
from stamps import stamp
E += stamp("db", x, y, w=60)                                  # quick — by name
E += stamp("moochin_simple-characters:Dragon", x, y, h=80)    # any — by key
E += stamp("server", x, y, w=40, color="#1971c2", bare=True)  # recolor, drop labels
```

An icon lands as one group. `bare=True` drops the English labels inside the
icon ("Code", "Search"); for quick icons this is already set in `assets/quick.json`.

## Quick icons

`python3 scripts/stamps.py list` — 56 names with descriptions. To see them, render
a sheet: `STAMPS_NO_USAGE=1 python3 scripts/quick_sheet.py quick.excalidraw`, then
snapshot it with `node scripts/mmd/shot.mjs quick.excalidraw quick.png`.

People and emotions: `person person-talk person-think woman shrug happy sad hand-up
not-sure presenting whiteboard person-laptop idea annoyed confused look
making-point wave kanban group user face-smile face-sad speech thought`.
Data and tech: `db cloud server doc files folder model robot laptop phone
internet key settings mic comment`. Process and status: `start finish target filter
lightning magic clock check cross warning question mail send bar-chart line-chart bulb`.

## What else is there — where to look

`stamps.py find <word>` searches all keys, `stamps.py libs` counts icons per library.

| Library | What's in it | When to use |
| --- | --- | --- |
| `moochin_simple-characters` | 49 characters in situations: juggling, dragon, collapsing tower, toolbox, time travel, gift, superhero | illustration, metaphor, the emotion of a process — **check first** |
| `mateuszbaransanok_it-icons` | 48 thin IT icons: host, network, firewall, BPMN gateways, event, error, camera, printer, timer, video | architecture, BPMN, infrastructure |
| `youritjang_stick-figures`, `dhtoran_stick-people` | stick figures: child, grandma, guy, girl, with a hat, with a mustache | roles and people |
| `anumithaapollo12_emojis` | 48 faces, yellow and outlined | customer journey, mood of stages |
| `xxxdeveloper_icons` | 65 file icons with colored tags: pdf, sql, js, python… | when the data format matters |
| `xxxdeveloper_system-icons` | 24 bold icons: tree, star, 3D cube, app, cleanup | processes, product |
| `artem-anufrij-live-de_artem-s-icons` | 22: organization, process, devices, statuses | general |
| `office-items`, `clocks`, `robots`, `bubbles`, `banners` | microphone, headset, parcel; alarm clock, clocks; 7 robots; 4 bubbles; 7 header ribbons | by name |
| `aocgame_domainstorytelling` | 7 bold black ones: person, group, system, mail | domain storytelling; stylistically stands out |
| `arach_systems-design-components` | cloud, stream, servers, DB | system design |
| `kwirke_some-handdrawn-signs` | hand-drawn check mark and cross | statuses |

**Interfaces — a separate set**, for wireframes rather than diagrams:
`spfr_lo-fi-wireframing-kit` (buttons, fields, cards, tables, tabs, hero, sidebar,
alerts, forms), `manuelernestog_universal-ui-kit` (calendar, charts, progress,
avatar), `gabrielamacakova_basic-ux-wireframing-elements` (69: toggles,
dropdowns, tooltips, modal), `dhaval_godwani_webpage-frames`, `excacomp_mobile-kit`,
`excacomp_web-kit`, `franky47_apple-devices-frames`, `marwinburesch_html-input-elements`.

## The quick list evolves

`stamp()` remembers which icons were used in which diagrams (`assets/usage.json`;
diagram = generator script, so re-running it doesn't inflate the count).

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
