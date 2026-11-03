# Queue, skip and break down

## Queue

Use this mode when the owner writes "triage", "next in triage" or "work the queue".

1. List the open issues in project `Triage`. Do not filter by the label `Intake`: Linear does not match a label group, so the result is empty.
2. Keep the issues with no parent that have a label from the `Intake` group. The list shows label names without the group name, for example `1 · Captured`.
3. Sort them yourself by the queue rules in the project description. Do not trust the order of the list.
4. Take the first issue. Read its description, its sub-issues and its last comments.
5. Show the owner: issue link, stage, kind (if known), and the open section.
6. Do one step for the stage of the issue (see Stage steps).
7. Stop after one step. Offer "next" or "skip".

## Stage steps

| Stage | Step | Reference |
|---|---|---|
| 1 · Captured | Move to `2 · Classify` and do its step. | [fill.md](fill.md) |
| 2 · Classify | Propose one kind from the Signals table, with a one-line reason. | [fill.md](fill.md) |
| 3 · Fill | Take the first open required section. Do research, then propose an answer. | [fill.md](fill.md) |
| 4 · Review | Run the review checklist. Report the result. Ask for owner approval. | [exit.md](exit.md) |

## Skip

1. On a skip, add the comment `⏭ Skipped` to the issue. Then take the next issue.
2. Count the `⏭ Skipped` comments on the issue.
3. If the count is 2 or more, or the owner says "too much" or "not clear", break down the open section.

## Break down

The owner has ADHD. A big question can block the issue for a long time. Make the next step small enough for 1% progress.

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
