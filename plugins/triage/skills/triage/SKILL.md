---
name: triage
description: Runs the triage of the Asks database in Notion for MgCohen's projects. Use when the user writes "idea:", "new request", "add to triage", "triage", "next in triage", "work the queue", or skips, answers or approves an ask. It captures new asks, selects the next ask from a stalest-first queue, classifies it into a kind and template, fills one section at a time with small proposal questions, splits hard sections into sub-asks, reviews, and converts the ask to a Notion project, feature, plan, bug, task, decision or doc.
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

Find each id by its pointer name. Do not use ids from memory.

| Pointer | Item |
|---|---|
| `workflow` | Workflow root page |
| `asks.source` | Asks data source |
| `templates.source` | Templates data source |
| `triage-rules` | Docs row `Triage · Rules` |
| `triage-kinds` | Docs row `Triage · Kinds` |
| `projects.source`, `features.source`, `plans.source`, `bugs.source`, `tasks.source`, `decisions.source`, `docs.source` | Exit targets |

- Resolve the names with the `notion_pointers` tool of the notion-context plugin. Its layers let a user or a project override an id.
- If `notion_pointers` is not available, search Notion for the page or database by its title.
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
- Do not make rows in Projects, Features, Plans, Bugs, Tasks, Decisions or Docs before an approved exit.
- Do not triage the Questions database. It holds blocking questions from agent sessions. A design or plan choice that does not block work is an ask of Kind Decision.
- Add one comment to the ask page for each turn: `Triage turn · <status>: <what changed>`.
