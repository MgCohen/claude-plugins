---
name: triage
description: Runs the Linear Triage intake for MgCohen's projects. Use when the user writes "idea:", "new request", "add to triage", "triage", "next in triage", "work the queue", or skips, answers or approves a Triage issue. It captures new requests, selects the next issue from a stalest-first queue, classifies it into a kind and template, fills one section at a time with small proposal questions, splits hard sections into sub-issues, reviews, and routes the request on exit.
---

# Triage

Triage is a standing project in Linear. Every new request starts there as an issue. This skill runs the process. Linear holds the rules.

## Rule 0: read the rules from Linear

Do not use rules from memory or from this plugin when Linear has them. Read these at the start of each run:

| Source | Holds |
|---|---|
| Project `Triage` (`P-MAT-12`), description | Stages, gates, queue order, skip and break-down rules, sub-issue prefixes, exit steps |
| Document `Triage · Kinds` | Kind registry, signals, base sections, exit actions, review checklist |
| Document `Template · <Kind>` | Sections table (required, Claude asks, gate) and Form of one kind |

- Workspace `mgcohen`, team `MAT`. Use the Linear MCP tools.
- Read a template document only when you need that kind.
- If Linear and this plugin disagree, Linear is correct.
- If a rule is missing in Linear, stop and ask the owner. Do not make up a rule.
- Linear save responses can show old data. After a write, read the item again to verify it.

## Modes

Find the mode from the owner's message. Then read only the reference file for that mode.

```
"idea: …"          ─► Capture
"triage" / "next"  ─► Queue ─► one step on one issue ─► stop
answer / accept    ─► Fill (promote) ─► gate check ─► next section
"skip"             ─► Skip ─► (2nd skip) Break down
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

- Each turn must move the issue one step: one section passes, or one sub-issue closes.
- Do not fill more than one section in one turn unless the owner gives all answers at once.
- Do not create issues, projects or initiatives outside Triage before an approved exit.
- Add one comment to the issue for each turn: `Triage turn · <stage>: <what changed>`.
