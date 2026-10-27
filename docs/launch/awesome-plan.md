> Статус на 2026-10-28: PR в BehiSecc отправлен (#1073); ComposioHQ закрыл приём PR от новых участников; hesreallyhim и heilcheng — не раньше 2026-11-11 (возраст репо ≥14 дней) и при нужном числе звёзд. Номера строк ниже — на 28 октября, перед подачей перепроверить.

# na-bal/excalidraw-skill — подача в awesome-списки

Дата исследования: 2026-10-28. Ничего не отправлено, только чтение.
Локальные копии README/CONTRIBUTING всех списков лежат рядом, в папках `<owner>_<repo>/`.

## Сводка

| # | Список | Как подают | Вердикт | Когда |
|---|---|---|---|---|
| 1 | ComposioHQ/awesome-claude-skills | PR (только README.md) | PR можно, но шансов мало | сейчас, без ожиданий |
| 2 | hesreallyhim/awesome-claude-code | только issue-форма в веб-UI, руками | ждать | не раньше 2026-11-11 |
| 3 | VoltAgent/awesome-agent-skills | PR | ждать traction | когда будет ~50+ звёзд и пара месяцев |
| 4 | travisvn/awesome-claude-skills | PR | skip | — |
| 5 | BehiSecc/awesome-claude-skills | PR | PR можно, дёшево | сейчас |
| 6 | heilcheng/awesome-agent-skills | PR (issue не принимают) | ждать | не раньше 2026-11-11 и ≥20 звёзд |

## Общее — сделать до подачи

1. **Возраст репо — главный блокер.** Первый коммит 2026-10-27T19:32Z, `created_at` 2026-10-27T21:35Z, 0 звёзд, 8 коммитов — все в один день.
   - hesreallyhim: бот берёт дату самого старого коммита ветки, при < 14 дней и < 100 звёзд автоматически закрывает issue. Плюс CONTRIBUTING (не бот) хочет «признаки активной разработки — коммиты после первого дня».
   - heilcheng: бот смотрит `created_at`, AGENTS.md прямо запрещает открывать PR для репо моложе 14 дней.
   - Самая ранняя безопасная дата для обоих: **2026-11-11**. И имеет смысл коммитить в эти две недели, а не просто ждать.
2. **Лицензия не распознаётся GitHub.** `gh api repos/na-bal/excalidraw-skill/license` → `NOASSERTION` (в `gh repo view` — «Other»). Причина: в конце LICENSE дописан абзац про иконки с libraries.excalidraw.com, и licensee уже не матчит MIT. hesreallyhim-бот репортит лицензию и прямо просит разобраться, если не находит; бейдж license в их README покажет not specified/other. Фикс: оставить в LICENSE дословный текст MIT, абзац про иконки перенести в README (там он уже есть) или в `NOTICE`. Проверить тем же `gh api`, должно стать `MIT`.
3. **Конкуренты в нише.** Уже в списках: `muthuishere/hand-drawn-diagrams` (VoltAgent, heilcheng) — генерит Excalidraw, отдаёт animated SVG, hosted edit link, PNG. Висят открытые PR: Composio #2230 «Add Excalidraw Whiteboard skill», travisvn #440 «Add excalidraw-skill» — **другой репо с тем же именем**. Поэтому везде, где можно, имя с префиксом `na-bal/`, а в описании — то, чем отличается: настоящая редактируемая доска (локально или свой ExcaliDash), правки руками сохраняются (фреймы), проверка реальным рендером, Mermaid → доска.
4. **Что честно раскрыть ревьюерам.** Есть опциональная отправка баг-репортов автору (`scripts/report.py` → `server/report-relay`), только после явного «да», текст показывается заранее. Есть строчка «Need help with hosting? — напишите автору» — без цены, но строгие к «commercial segue» мейнтейнеры (travisvn, частично Composio) могут придраться. Setup качает headless Chromium (~120 MB), рендерер грузит Excalidraw с esm.sh/jsdelivr.
5. **Про AI.** Черновики ниже написаны агентом. heilcheng требует это раскрыть (и это нормально). hesreallyhim требует, чтобы подачу сделал человек руками через веб-форму. travisvn прямо запрещает AI-assisted PR. Поэтому для hesreallyhim — переписать описание своими словами или хотя бы самому прочитать и подать.
6. Слово `token` в добавленных строках Composio бот блокирует (антикрипто-фильтр) — в черновиках его нет, не добавлять.

---

## 1. ComposioHQ/awesome-claude-skills

**Вердикт: PR можно, но я бы не ждал мержа.** Звёзд/возраста бот не проверяет. Но последний merge — 2026-05-22, последний коммит — 2026-07-24, открытых PR 500+, и из них 300+ уже с лейблом `ready-to-merge` (его ставит бот, а не человек) — лейбл ничего не значит. Если и подавать, то как «пусть лежит».

**Правила (CONTRIBUTING + `.github/workflows/label-ready-skill.yml`):**
- Менять только `README.md` (бот валит PR с любым другим файлом — несмотря на то, что CONTRIBUTING говорит «добавьте папку со SKILL.md»; актуален бот, все свежие мержи — внешние ссылки).
- Правки только между `## Skills` и `## Getting Started`.
- Ссылка внешняя (https, не composio.dev/anthropic.com).
- Алфавит без учёта регистра относительно соседей сверху и снизу (по тексту ссылки).
- Без эмодзи, «consistent punctuation». Внешние записи заканчиваются `*By [@user](https://github.com/user)*`.
- Требование «Be tested — Verify the skill works across Claude.ai, Claude Code, and/or API»: правда только про Claude Code (Claude.ai — нет, там нет локального Python/Chromium). Формулировка «and/or» это допускает, но в теле PR честно написать «tested in Claude Code (and Codex/Gemini CLI)».

**Файл/секция/позиция:** `README.md`, `### Creative & Media`, между строкой 183 `- [Canvas Design](./canvas-design/) - ...` и строкой 184 `- [imagen](https://github.com/sanjay3290/...) - ...`.
Запасной вариант: `### Development & Code Tools`, между строкой 127 `- [D3.js Visualization](...)` и 128 `- [FFUF Web Fuzzing](...)`. Я бы взял Creative & Media.

**Строка:**
```markdown
- [Excalidraw Skill](https://github.com/na-bal/excalidraw-skill) - Draws hand-drawn Excalidraw diagrams as editable boards (local `.excalidraw` files with a local viewer, or a self-hosted ExcaliDash server), checks each one with the real Excalidraw renderer in headless Chromium, keeps manual edits by redrawing only its own frames, and turns Mermaid into editable boards. Works with Claude Code, Codex, Gemini CLI, Cursor and other Agent Skills agents. *By [@na-bal](https://github.com/na-bal)*
```

**Заголовок PR:** `Add Excalidraw Skill to Creative & Media` (CONTRIBUTING предлагает `Add [Skill Name] skill`, но свежие мержи используют «Add X to <Category>» — оба нормальны).

**Тело PR:**
```markdown
Adds [Excalidraw Skill](https://github.com/na-bal/excalidraw-skill) to Creative & Media, in alphabetical order between Canvas Design and imagen. README.md only.

**What problem it solves.** Agents explain architecture and flows with ASCII art or Mermaid code blocks. This skill has the agent draw a real Excalidraw board instead: every box and arrow is an editable Excalidraw element, stored as a local `.excalidraw` file (opened in a bundled local viewer) or on a self-hosted ExcaliDash server.

**Who uses this workflow.** Developers and product people who sketch architecture, flows, sequence diagrams, roadmaps and journeys while working with a coding agent, then keep editing the board by hand or share it with a team.

**How it works / what's notable.**
- Each diagram is rendered with Excalidraw's own fonts in headless Chromium before it is shown, so clipped labels and overlaps are caught.
- Each part of a board is a frame; the agent redraws only its own frame, so manual edits survive. It records what the user changed by hand as preferences for later diagrams.
- Mermaid → editable board; 450+ icons from libraries.excalidraw.com (MIT).

**Example.** "Draw how our signup works" → the agent builds the scene, checks the render, saves it to the board and returns a link. Gallery of 10 diagrams in the README.

**Install:** `npx skills add na-bal/excalidraw-skill`, or as a Claude Code plugin: `claude plugin marketplace add na-bal/excalidraw-skill`.

**Tested** in Claude Code (also Codex and Gemini CLI); it needs local Python 3.10+, Node 18+ and a headless Chromium, so it does not run in Claude.ai.

**Attribution.** Original work by the author (I wrote this skill). MIT licensed. Optional bug reports to the author are sent only after explicit confirmation and show the full text first; the receiving service is in `server/report-relay`.
```

**Gotchas:** висящий PR #2230 «Excalidraw Whiteboard skill» — конкурент в той же секции; если его когда-то смержат, проверь алфавит заново. Секция и так не идеально отсортирована (swiftui, Pixelbin в конце) — бот проверяет только соседей.

---

## 2. hesreallyhim/awesome-claude-code

**Вердикт: ждать до 2026-11-11, потом подать руками через веб-форму.** Сейчас бот закроет issue автоматически (14 дней от первого коммита ИЛИ 100 звёзд). Список живой: мержи 10-15…10-22, бот сам генерит PR после одобрения мейнтейнером. Но отбор строгий («awesome list is to be selective», «если попадание в список — часть промо-стратегии, имейте план Б»).

**Правила:**
- Только веб-форма: https://github.com/hesreallyhim/awesome-claude-code/issues/new?template=recommend-resource.yml . **Не PR, не `gh issue create`** — за это грозят временным ограничением.
- Подача должна быть сделана человеком.
- Одна открытая заявка на автора.
- Описание — описание, а не реклама; не обращаться к читателю; одна строка; без эмодзи; 10–500 символов.
- Желательно, чтобы ресурс был про специфику Claude Code.
- Лицензию бот определяет сам — см. «Общее», п. 2, починить заранее.

**Поля формы:**
- **Display Name:** `excalidraw-skill` (или `Excalidraw Skill`)
- **Category:** `Design & UI/UX` — там Diagram Design, Snip, visual-explainer. Альтернатива: `Documentation, Knowledge & Learning > Data Visualization` (там Archify, всего одна запись). Я бы выбрал Design & UI/UX.
- **Link:** `https://github.com/na-bal/excalidraw-skill`
- **Author Name:** `Alexander Bedelev`
- **Author Link:** `https://github.com/na-bal`
- **Description** (470 символов):
  ```
  An Agent Skill, also packaged as a Claude Code plugin, that draws hand-drawn Excalidraw diagrams as editable boards (local .excalidraw files with a local viewer, or a self-hosted ExcaliDash server). Each scene is rendered with Excalidraw's own fonts in headless Chromium before it is shown, and each part of a board is a frame, so redraws keep manual edits, which are noted as preferences for later diagrams. Also turns Mermaid into editable boards; 450+ icons included.
  ```
- **Checklist:**
  - [x] I have visited this repo before with my own eyes, and I have confirmed that this resource is sufficiently distinct from any existing resource — **тикает сам человек, только если реально посмотрел.** Ближайшие соседи: Diagram Design (HTML+SVG), Snip (whiteboard для ревью), Archify (интерактивный HTML), Nimbalyst (клиент, умеет Excalidraw). Excalidraw-скилла как такового в списке нет.
  - [x] All links are working and publicly accessible — правда.
  - [ ] This resource is specific to Claude Code — **спорно, решать самому.** Скилл кросс-агентный (Codex, Gemini CLI, Cursor…), но ставится как Claude Code plugin через `.claude-plugin/marketplace.json`. Чекбокс обязательный: без него форму не отправить. Если тикаешь — опереться на плагин и `/reload-skills`.
  - [x] I have read the CONTRIBUTING.md — тикать после прочтения.
  - [x] I promise I actually did these things… — то же.
  - [ ] «Do not check the following box» — **оставить пустым** (ловушка).

**Gotchas:** до подачи — пара коммитов в следующие дни (активная разработка), починенная лицензия. Если бот закрыл — повторно не спамить, CONTRIBUTING это не любит.

---

## 3. VoltAgent/awesome-agent-skills

**Вердикт: подождать traction.** Список активный (мержи 10-19…10-25, 55 открытых PR), но CONTRIBUTING прямо: «Brand new skills that were just created are not accepted», README: «Please don't submit skills you created 3 hours ago». Свежие мержи: slide-wright (создан 2026-06-15, 59–65 звёзд), cc-tree (2026-05-25, 94–101 звезда). Ориентир — пара месяцев и ~50+ звёзд. Подавать сейчас = почти наверняка закроют.

**Правила:** только README.md; дописать в **конец** подходящей подкатегории в Community Skills; имя с префиксом `author/`; описание ≤ 10 слов; заголовок `Add skill: author/skill-name`.

**Файл/секция/позиция:** `README.md`, `<summary>…Development and Testing</summary>` (там же лежит `muthuishere/hand-drawn-diagrams` и UI/дизайн-скиллы). Вставить после строки 1719:
`- **[finom/vovk](https://github.com/finom/vovk/tree/main/skills)** - Next.js API routes as MCP tools and typed clients`
и перед `</details>`. (К моменту подачи конец секции сдвинется — вставлять перед `</details>` этой секции.)

**Строка** (9 слов):
```markdown
- **[na-bal/excalidraw-skill](https://github.com/na-bal/excalidraw-skill)** - Hand-drawn Excalidraw diagrams on a local or self-hosted board
```

**Заголовок PR:** `Add skill: na-bal/excalidraw-skill`

**Тело PR** (по образцу смерженных #1233/#1240; дату/звёзды подставить на день подачи):
```markdown
Adds na-bal/excalidraw-skill to Community Skills > Development and Testing, at the end of the section.

- Public repo with `skills/excalidraw/SKILL.md` and README: https://github.com/na-bal/excalidraw-skill
- Created 2026-10-27; <N> stars at the time of this PR; MIT licensed
- Draws editable Excalidraw boards (local files + local viewer, or self-hosted ExcaliDash), checks each diagram with the real Excalidraw renderer, keeps manual edits (frames), Mermaid → editable board
- Install: `npx skills add na-bal/excalidraw-skill`; also a Claude Code plugin
- Author/org prefix included; description is 9 words
- I am the skill's author. This PR was prepared with Claude Code on my behalf.
```

**Gotchas:** их Quality Criteria: «No absolute paths» — SKILL.md пишет «All paths below are relative to SKILL_DIR», ок; «Skill body below 500 lines» — SKILL.md 243 строки, ок.

---

## 4. travisvn/awesome-claude-skills

**Вердикт: skip.** Причины, каждая сама по себе достаточна:
- PR с < 10 звёзд «will be closed automatically».
- Явный запрет на PR, сгенерированные/поданные с AI-помощью («closed without comment»).
- Список фактически заморожен: через PR смержен один раз (#29, 2026-01-07), последний коммит 2026-04-28, открытых PR 500+.
- Уже висит #440 «Add excalidraw-skill» от другого автора — коллизия имён.
- Пункт «no requests going through your server»: у нас опциональный report-relay — формально ок (opt-in), но лишний повод.

Если когда-нибудь подавать — **самому, руками**, при заметном числе звёзд. Формат там — строка таблицы в `### Individual Skills`, в конец после строки 130 (`| **[get-shit-done](...)** | ... |`):
```markdown
| **[excalidraw-skill](https://github.com/na-bal/excalidraw-skill)** | Hand-drawn Excalidraw diagrams on a local or self-hosted board, checked with the real renderer; keeps manual edits and converts Mermaid |
```
Заголовок: `Add Excalidraw diagram skill`. В теле: описание 1–2 предложения, prerequisites (Python 3.10+, Node 18+, headless Chromium), лицензия MIT.

---

## 5. BehiSecc/awesome-claude-skills

**Вердикт: PR можно сейчас, стоит дёшево.** CONTRIBUTING нет, в README: «Fork → change → PR», никаких порогов. Мейнтейнер не мержит PR по одному, а периодически пачкой забирает из открытых прямыми коммитами («Add 25 curated Claude skills from open PRs», 2026-08-02; последняя активность 2026-09-21; последний PR-мерж 2026-06-03). 500+ открытых PR. То есть шанс есть, сроков нет.

**Формат:** `- [name](url) - Description.` — обычный дефис ` - ` (одна запись в секции с `—`, не копировать). Порядок — дописывают в конец, не алфавит.

**Файл/секция/позиция:** `README.md`, `## 🎬 Media & Content` (там же Dashmotion — диаграммный скилл, строка 164). Вставить после строки 171:
`- [bria-ai](https://github.com/Bria-AI/bria-skill/tree/main/skills/bria-ai) - Generate, edit, and remove image backgrounds ...`
(за ней две пустые строки и `## 🛠 Development & Code Tools` — их не трогать).

**Строка:**
```markdown
- [excalidraw-skill](https://github.com/na-bal/excalidraw-skill) - Draw hand-drawn Excalidraw diagrams as editable boards (local files or self-hosted ExcaliDash), checked with the real renderer; keeps manual edits and turns Mermaid into boards.
```

**Заголовок PR:** `Add excalidraw-skill to Media & Content`

**Тело PR:**
```markdown
Adds [excalidraw-skill](https://github.com/na-bal/excalidraw-skill) to the Media & Content section (appended at the end).

An Agent Skill that has Claude Code (or Codex, Gemini CLI, Cursor, etc.) draw hand-drawn Excalidraw diagrams as editable boards: local `.excalidraw` files with a bundled local viewer, or a self-hosted ExcaliDash server. Each diagram is checked with Excalidraw's own renderer in headless Chromium before it is shown; manual edits survive redraws because each part of a board is a frame. Mermaid → editable board, 450+ icons.

- Install: `npx skills add na-bal/excalidraw-skill` (also a Claude Code plugin)
- MIT licensed. I'm the author.
```

---

## 6. heilcheng/awesome-agent-skills

**Вердикт: ждать до 2026-11-11 и ≥ 20 звёзд, потом PR.** Список активный (батч-триаж 2026-10-15 и 2026-10-27), правила жёсткие и автоматизированы (`.github/scripts/check_submission.py`):
- < 20 звёзд → лейбл `on hold`, не мержат (PR не закрывают, но висеть будет).
- репо < 14 дней (по `created_at`) → AGENTS.md: «Do not open a PR».
- Issue для предложения скилла не принимают (issue-формы для этого нет вообще).
- Только `README.md`, только добавление строк (никаких правок пробелов/переводов строк, без BOM), ≤ 5 строк, одна открытая PR на репо, не трогать переводы README.*.md.
- Формат строго по regex: `- [owner/repo](https://github.com/owner/repo) - Description`, описание < 100 символов, без маркетинга.
- В репо должен быть SKILL.md с `name` и `description` во frontmatter — есть (`skills/excalidraw/SKILL.md`).

**Файл/секция/позиция:** `README.md`, `<summary><strong>Development and Testing</strong></summary>` (там уже `muthuishere/hand-drawn-diagrams`), в конец — после строки 626:
`- [Grit-77/checking-delivery](https://github.com/Grit-77/done-is-a-claim/tree/main/skills/checking-delivery) - Check delivery at its destination ...`
и перед `</details>`.
Альтернатива: `Creative and Media`, после строки 669 `- [NoizAI/skills](https://github.com/NoizAI/skills) - ...`. Я бы взял Development and Testing — прецедент с соседним Excalidraw-скиллом.

**Строка** (91 символ в описании):
```markdown
- [na-bal/excalidraw-skill](https://github.com/na-bal/excalidraw-skill) - Editable hand-drawn Excalidraw diagrams on a local or self-hosted board; keeps manual edits
```

**Заголовок PR:** `Add na-bal/excalidraw-skill to Development and Testing`

**Тело PR** (их шаблон, отмечено только то, что правда; пункт про звёзды/возраст — тикать только когда станет правдой):
```markdown
**Skill repository:** https://github.com/na-bal/excalidraw-skill

**Category:** Development and Testing

### Checklist

- [x] The link is a public GitHub repository (or folder) that contains a `SKILL.md` with `name` and `description` frontmatter
- [ ] The repository has at least 20 stars and is older than 14 days
- [x] I searched `README.md` and this repository is not already listed or in another open PR
- [x] I only edited `README.md`, adding at most 5 lines to the end of an existing category
- [x] Each line uses the format `- [owner/repo](https://github.com/...) - Description under 100 characters`
- [x] This is not a directory, marketplace, badge, or promotional link

### Disclosure

- [x] I am the author or a maintainer of this skill
- [x] This PR was written by an AI agent (name it: Claude Code)
```
Второй пункт: не подавать, пока он не станет `[x]`. Проверка «не в другой открытой PR» — на 2026-10-28 поиск `excalidraw` по открытым PR heilcheng пустой; перепроверить перед подачей.

**Gotchas:** в описании не писать «your» / «beautiful» — «no marketing language». Если правишь PR после бота — пушить в ту же ветку, новый PR не открывать.
