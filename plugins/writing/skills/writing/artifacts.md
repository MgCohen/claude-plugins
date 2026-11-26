# Artifacts: house style

These rules apply to HTML artifacts for work: decisions, audits, research, plans, architecture and
reference pages. They do not apply to games, invitations or other occasion pages.

**Precedence.** For work artifacts, the house style comes before the design defaults of the
`artifact-design` guide: fonts, colors, the label line, the layout and the page picture. Keep the
page contract of that guide: title, safe areas, dark mode, phone width and allowed hosts.

## Steps

1. Copy `starter.html`. Keep its CSS and its script without changes.
2. Choose the page type in the table below. Make the tabs of that type.
3. Replace the sample content. Delete each component that the page does not use.
4. Write all visible text in STE (`language.md`). Apply `documents.md` for length and structure.
5. Examine the page with the check list at the end of this file.

Decisions and values: `house-style-decisions.md`.

## Page types

| Type | First tab | Other tabs |
|---|---|---|
| Decision | Recommendation card, questions | One tab for each option, Questions |
| Audit or research | Summary note, stat tiles, main visual | Findings, Options, Prior art |
| Plan | Scope, phase list | Details, Questions |
| Architecture or reference | Main diagram, parts table | One tab for each part |

- Use tabs when the page has more than about 1,500 words. 2 to 6 tabs.
- Tab names: 2 words maximum, no numbers.
- Put open questions on the last tab, as a question list.

## Components

| Component | Class | Use for |
|---|---|---|
| Page header | `header`, `.eyebrow`, `.lead` | Each page |
| Tabs | `nav.tabs`, `section.tab` | Long pages |
| Card | `.card` | A group with a heading |
| Recommendation card | `.card.rec` | The decision, at the top of the first tab |
| Note banner | `.note`, `.ok`, `.warn`, `.bad` | A status, an example, a risk |
| Table | `.tw` | Items with the same attributes |
| Chip | `.chip`, `.ok`, `.warn`, `.bad`, `.info` | A state in one word |
| Stat tiles | `.stats`, `.stat` | 3 or 4 key figures |
| Bar rows | `.bars`, `.bar` | 2 to 12 values to compare |
| Foldable list | `.fl` | 3 or more items of one type |
| Code block | `.cb` | Code from a file, or an API shape |
| Code in a sentence | `code` | A name in normal text |
| Inventory | `.inv`, `.fbar`, `.sbar` | 20 items or more, with filters |
| Diagram box | `.box`, `.cap`, `.legend` | A diagram |

### Page header

- The label line gives the project and the topic: "Umpire · Check system".
- The page shows no status mark (draft, done). If the reader must know the status, use a note banner
  with the reason.
- The lead gives the result or the decision in 1 to 3 sentences.

### Note banner and recommendation card

- Start a note banner with bold words that give the point: "**Risk.** …".
- Edge color: blue for information, green for done, amber for a draft or a risk, red for a failure.
- A recommendation card has one line for each decision, with the decision key in bold. The rejected
  option comes last, as "**Not recommended:** …".

### Table

- Put each table in `.tw`. Put the unit in the header: "Time (s)".
- Cell text never wraps. Write short cells.
- On a narrow screen, the script shrinks the table to fit. If the table must shrink below 70%, the
  script shows one card for each row.
- If a cell needs a sentence, the content is too much for a table. Use a foldable list.

### Chip

- A chip gives a state ("decided", "open", "risk") or a reference to a decision or a phase ("K4", "P7").
- One fixed word for each state on a page.
- Green: done or good. Amber: open or partial. Red: failure. Blue: information or default.
- Up to 3 chips on one row. No chips for decoration.

### Foldable list

One component for all lists of items: findings, decisions, proposals, questions and plan phases.

| Part | Rule |
|---|---|
| Box | One box for each item, with a gap between |
| Title | 6 words maximum, one line, cut with "…" when closed |
| Key fact | Optional second line, 13px grey |
| ID | Only when readers refer to items by ID: K1, Q1, P3 |
| Chips | Only for a state or a reference. Up to 3, at the right |
| Open content | Full width, under a line |
| Sizes | Title 15 bold, key fact 13, ID 12 code font, chip 11 code font |

- Put a table or a diagram of all items before the list.
- Keep the items closed. Do not put the main message or a warning in an item.
- **Nested items:** an open item can hold a child list (`.fl` in `.body`). The children show as
  boxes on a grey area. 3 levels maximum.
- **Groups:** split a long list into one parent item for each group, for example "Gaps". The key
  fact gives the count: "9 items".
- **Sections:** split a long item into parts, each with a `.lbl` label above it: "Where",
  "Why it matters", "Fix". All items of one list use the same labels, in the same order.
- **Rich content:** text, tables, code blocks and notes use the full width of the item.
- **Length:** about 300 words in one item. If an item is longer, split it into child items, or
  give it its own tab.
- **Question:** ID `Q1`, key fact "Default: …", chip `info` "default" or `ok` "answered".
- **Plan phase:** ID = phase number, key fact = decisions and issue, chip = PR number or "open".
  The open content gives the changes, then the tests to run.

### Inventory

A long list of items of one type, for example events, components or concepts.

| Part | Rule |
|---|---|
| Groups | One table with group rows (`tr.band`). Use parent foldables instead above about 40 rows |
| Share bar | `.sbar` and `.tally` above the bar: the share of each state, with its count |
| Filter bar | `.fbar`: a search box and one dropdown (`.dd`) for each category |
| Dropdown | Check boxes, several values. The button shows the values and turns blue |
| Count | "13 items", or "4 of 13" with a filter. A Clear button with a filter |
| Sort | `th[data-sort]`: click a header to sort. Rows sort inside their group |
| Row details | When rows need more than one line of facts, use the foldable list, not a table |

- Each item has `data-item` and one `data-<category>` attribute for each dropdown.
- The bar stays one row while it fits. If not, the search box goes to its own row.
- If the page needs only search or only one category, use the same bar with fewer controls.

### Code block

- Add the top bar with the file name and the language when the code comes from a file.
- Set `data-lang` on the `pre`. The script adds the syntax colors.
- Show only the lines that make the point. No line numbers.
- On a narrow screen, the script shrinks the code down to 50%. Below that, the block scrolls.

### Diagrams

The diagram rules are not decided. Until then:

- Use Mermaid in a `.box`, with a `.cap` caption above: "Title · message".
- Add a `.legend` when the diagram has 2 or more node types or edge types.
- 3 to 10 nodes. Node labels: 4 words maximum.

## Phone

- Each component fits the screen width. Nothing makes the page scroll sideways.
- Content shrinks before it wraps. Text does not wrap in table cells or in closed foldable titles.
- If content is too much for the screen, put it in a foldable list.

## Check list

- The page starts from `starter.html`, and its CSS and script have no changes.
- The page type matches the tabs and the first tab.
- No font, color or size outside the house tokens.
- Each table, foldable, chip and banner follows its rules above.
- No status mark in the header.
- At 390px width, there is no side scroll, in light and in dark mode.
