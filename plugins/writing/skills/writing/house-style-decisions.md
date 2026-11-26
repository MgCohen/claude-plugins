# House style decisions

The approved house style for artifacts, from four review rounds. The `artifacts.md` rules and the
starter page come from this file.

## Foundations

| ID | Decision | Value |
|---|---|---|
| F1 | Body font | IBM Plex Sans |
| F2 | Heading font | Space Grotesk |
| F3 | Code and label font | IBM Plex Mono |
| F4 | Accent | Blue `#2a5bd7`, tint `#e6edfc` |
| F5 | Status colors | ok `#1f7a4d`, warn `#9a5b00`, bad `#b4232c`, each with a tint |
| F6 | Page background | Light grey `#e9ecf1`. Cards and tables are white |
| F7 | Text sizes | Title 26, heading 19, body 15, table 14, label 11 |
| F8 | Dark mode | One dark token set for each page |

## Page frame

| ID | Decision | Value |
|---|---|---|
| P1 | Page header | Label line (project · topic), title, summary |
| P2 | Tab style | Blue underline on the open tab |
| P3 | Tab numbers | No numbers |
| P4 | Page status | No status mark |
| P5 | Note banner | Left edge in a status color, bold first words |
| P6 | Recommendation card | Green left edge, one line for each decision, rejected option last |

## Data

| ID | Decision | Value |
|---|---|---|
| D1 | Table header | Body font, bold, normal case |
| D2 | Table box | White box with outline |
| D3 | Chip style | Filled tint |
| D4 | Table on a phone | Shrink to fit, or one card for each row, chosen by table size. Cell text never wraps. Too much content: use foldables |
| D5 | Stat tiles | Keep |
| D6 | Bar rows | Keep |

## Foldable

One component for all lists: findings, decisions, questions and plan phases.

| ID | Decision | Value |
|---|---|---|
| FL1 | Box style | Separate boxes |
| FL2 | Title row | Title, and a key fact line under it only when necessary |
| FL3 | Long titles | One line, cut with "…" |
| FL4 | Open marker | Triangle at the left |
| FL5 | Item ID | Only when readers refer to items by ID |
| FL6 | State chip | Only when items have a state |
| FL7 | Open content | Full width, line above |
| FL8 | Text sizes | Title 15 bold, key fact 13 grey, ID 12 code font, chip 11 code font |
| FL9 | Open all and Close all | Not used |
| FL10 | Question form | ID Q1…, key fact "Default: …", chip "default" or "answered" |
| FL11 | Phase form | ID = phase number, key fact = decisions and issue, chip = PR or "open" |

Question lists (R2) and phase lists (R3) use the foldable.

## Other components

| ID | Component | Value |
|---|---|---|
| R5 | Legend | Keep |
| R8 | Code block | To change: shrink to fit on a phone, syntax colors, dark background |

## Open questions

- Diagrams (R4, R6, R7): which types, when to use each, Mermaid or drawn, and the style. This needs
  its own review.
- Code block (R8): review the changed version.
