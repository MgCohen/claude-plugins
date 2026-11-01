---
name: triage
description: Runs the Linear Triage intake for MgCohen's projects. Use when the user writes "idea:", "new request", "add to triage", "triage", "next in triage", "work the queue", or skips, answers or approves a Triage issue. It captures new requests, selects the next issue from a stalest-first queue, classifies it into a kind and template, fills one section at a time with small proposal questions, splits hard sections into sub-issues, reviews, and routes the request on exit.
---

# Triage

Triage is a standing project in Linear. Every new request starts there as an issue. This skill runs the process. Linear holds the rules.

## Rule 0: read the rules from Linear

Do not use rules from memory or from this file when Linear has them. Read these at the start of each run:

| Source | Holds |
|---|---|
| Project `Triage` (`P-MAT-12`), description | Stages, gates, queue order, skip and break-down rules, sub-issue prefixes, exit steps |
| Document `Triage · Kinds` | Kind registry, signals, base sections, exit actions, review checklist |
| Document `Template · <Kind>` | Sections table (required, Claude asks, gate) and Form of one kind |

- Workspace `mgcohen`, team `MAT`. Use the Linear MCP tools.
- Read a template document only when you need that kind.
- If Linear and this file disagree, Linear is correct.
- If a rule is missing in Linear, stop and ask the owner. Do not make up a rule.
- Linear save responses can show old data. After a write, read the item again to verify it.

## Modes

```
"idea: …"          ─► Capture
"triage" / "next"  ─► Queue ─► one step on one issue ─► stop
answer / accept    ─► Promote ─► gate check ─► next stage
"skip"             ─► Skip ─► (2nd skip) Break down
"approve"          ─► Review ─► Exit
```

### Capture

1. Create an issue in team `MAT`, project `Triage`.
2. Write a short imperative title and one sentence from the owner's words.
3. Add the label `Intake/1 · Captured`. Set status Backlog.
4. Reply with the issue link. Do not start the interview unless the owner asks.

### Queue

1. List the open issues in project `Triage`. Do not filter by the label `Intake`: Linear does not match a label group, so the result is empty.
2. Keep the issues with no parent that have a label from the `Intake` group. The list shows label names without the group name, for example `1 · Captured`.
3. Sort them yourself by the queue rules in the project description. Do not trust the order of the list.
3. Take the first issue. Read its description, its sub-issues and its last comments.
4. Show the owner: issue link, stage, kind (if known), and the open section.
5. Do one step for the stage of the issue (see Stage steps).
6. Stop after one step. Offer "next" or "skip".

### Stage steps

| Stage | Step |
|---|---|
| 1 · Captured | Move to `2 · Classify` and do its step. |
| 2 · Classify | Propose one kind from the Signals table, with a one-line reason. |
| 3 · Fill | Take the first open required section. Do research, then propose an answer. |
| 4 · Review | Run the review checklist. Report the result. Ask for owner approval. |

When the owner accepts a kind:

1. Read `Template · <Kind>`.
2. Put its Form into the description. Keep the text that is already there under Intent.
3. Move the label to `3 · Fill`.

### Ask a question

Each question follows these rules:

1. Do research first: the target repo, Linear docs and specs, and related issues.
2. Propose an answer. Do not ask an open question if a proposal is possible.
3. Use a yes/no question, or a choice of 2 to 3 options.
4. Ask one question at a time.
5. Give the gate of the section, so the owner knows what "done" is.

### Promote

When the owner accepts or edits an answer:

1. Write the accepted text into the section of the parent description.
2. If the answer came from a sub-issue, set that sub-issue to Done.
3. Check the gate of the section. If it passes, take the next open section.
4. If all required sections pass, move the label to `4 · Review`.
5. Add one comment to the parent: `Triage turn · <stage>: <what changed>`.

The parent description holds only accepted content. Put proposals, research and drafts in sub-issues or in chat.

### Skip and break down

1. On a skip, add the comment `⏭ Skipped` to the parent. Then take the next issue.
2. Count the `⏭ Skipped` comments on the issue.
3. If the count is 2 or more, or the owner says "too much" or "not clear", break down the open section.

To break down a section:

1. Do research for the section. Write the result in a `Ctx:` sub-issue.
2. Make one `Q:` sub-issue: one small question, the proposed answer, and the options.
3. Ask that question now.
4. If the owner cannot answer a `Q:`, split it into smaller `Q:` sub-issues.

Each sub-issue: team `MAT`, project `Triage`, parent set to the request, no `Intake` label.

| Prefix | Holds |
|---|---|
| `Q:` | One question, the proposed answer, the options |
| `Ctx:` | Research notes with links |
| `Draft:` | Proposed text for one section |

### Review

1. Run each item of the review checklist in `Triage · Kinds`.
2. If all items pass, tick `AI review passed`.
3. If an item fails, comment with the failed items. Move the label back to `3 · Fill`.
4. Tick `Owner approved` only after the owner approves in chat. Quote the approval in a comment.

Do not tick `Owner approved` on your own decision.

### Exit

Do the exit only when both review boxes are ticked.

1. Find the row of the kind in `Triage · Kinds`.
2. Do its exit action (Task exit, Detail exit, Project exit or Initiative exit).
3. Set the labels on exit from that row.
4. Do the exit steps in the Triage project description.
5. Verify each created or changed item with a read.
6. Reply with the links.

### Close

If the owner discards a request, set it to Canceled. Add a comment with the reason. If it repeats an existing issue, set Duplicate of that issue.

## Turn limits

- Each turn must move the issue one step: one section passes, or one sub-issue closes.
- Do not fill more than one section in one turn unless the owner gives all answers at once.
- Do not create issues, projects or initiatives outside Triage before an approved exit.
