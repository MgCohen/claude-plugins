---
name: triage
description: Runs the triage of the Asks database in Notion for MgCohen's projects. Use when the user writes "idea:", "new request", "add to triage", "triage", "next in triage", "work the queue", or skips, answers or approves an ask. It captures new asks, selects the next ask from a stalest-first queue, classifies it into a kind and template, fills one section at a time with small proposal questions, splits hard sections into sub-asks, reviews, and converts the ask to a Notion project, feature, issue or doc.
---

# Triage

Triage is the Asks database in the Notion page Workflow. Each new request starts there as a row. This skill runs the process. Notion holds the rules.

## Rule 0: read the rules from Notion

Do not use rules from memory or from this plugin when Notion has them. Read these at the start of each run:

| Source | Holds |
|---|---|
| Docs row `Triage · Rules` | Stages, gates, queue order, skip and break-down rules, sub-ask prefixes, exit steps |
| Docs row `Triage · Kinds` | Kinds, signals, base sections, kind sections, exits, section mapping, review checklist |
| Templates row `Ask · <Kind>` | Form of one kind: the page body that triage adds at Classify |

| Item | Notion ID |
|---|---|
| Workflow page | `40e91e24578681b5a046c0d425a39b66` |
| Asks data source | `collection://fb8adbbb-9cc8-4c79-a2b1-ff0bc9cb71b0` |
| Templates data source | `collection://4a5c3982-9099-4e16-98ef-52864a494652` |
| `Triage · Rules` | `40e91e24578681d0b819cdec82c8613c` |
| `Triage · Kinds` | `40e91e24578681c88c47ffb3523742f1` |

- Use the Notion MCP tools: fetch, query data sources, create pages, update page, create comment.
- Fetch a data source before you write a row, to get the exact property names.
- Read a template row only when you need that kind.
- If Notion and this plugin disagree, Notion is correct.
- If a rule is missing in Notion, stop and ask the owner. Do not make up a rule.
- Relation filters need the full page URL. A bare page ID returns all rows with no error.

## Modes

Find the mode from the owner's message. Then read only the reference file for that mode.

```
"idea: …"          ─► Capture
"triage" / "next"  ─► Queue ─► one step on one ask ─► stop
answer / accept    ─► Fill (promote) ─► gate check ─► next section
"skip"             ─► Skip ─► (Skips ≥ 2) Break down
"approve"          ─► Review ─► Exit
"discard"          ─► Close
```

| Mode | Reference |
|---|---|
| Capture | [references/capture.md](references/capture.md) |
| Queue, skip, break down | [references/queue.md](references/queue.md) |
| Classify, fill, questions, promote | [references/fill.md](references/fill.md) |
| Review, exit, close | [references/exit.md](references/exit.md) |

A queue step often continues into a fill step. If so, read both files.

## Turn limits

- Each turn must move the ask one step: one section passes, or one sub-ask closes.
- Do not fill more than one section in one turn unless the owner gives all answers at once.
- Do not make rows in Projects, Features, Issues or Docs before an approved exit.
- Add one comment to the ask page for each turn: `Triage turn · <status>: <what changed>`.
