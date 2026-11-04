# Queue, skip and break down

## Queue

Use this mode when the owner writes "triage", "next in triage" or "work the queue".

1. Query Asks for Status New, Classify, Fill or Review, with Parent empty.
2. Sort them by the queue rules in `Triage · Rules`: Priority first, then the oldest Updated.
3. Take the first ask. Fetch its page, its sub-asks and its last comments.
4. Show the owner: page link, Status, Kind (if set), and the open section.
5. Do one step for the Status of the ask (see Stage steps).
6. Stop after one step. Offer "next" or "skip".

## Stage steps

| Status | Step | Reference |
|---|---|---|
| New | Set Status to Classify and do its step. | [fill.md](fill.md) |
| Classify | Propose one kind from the Kinds table, with a one-line reason. | [fill.md](fill.md) |
| Fill | Take the first open required section. Do research, then propose an answer. | [fill.md](fill.md) |
| Review | Run the review checklist. Report the result. Ask for owner approval. | [exit.md](exit.md) |

## Skip

1. On a skip, add 1 to Skips. Comment `⏭ Skipped`. Then take the next ask.
2. If Skips is 2 or more, or the owner says "too much" or "not clear", break down the open section.

## Break down

The owner has ADHD. A big question can block the ask for a long time. Make the next step small enough for 1% progress.

1. Do research for the section. Write the result in a `Ctx:` sub-ask.
2. Make one `Q:` sub-ask: one small question, the proposed answer, and the options.
3. Ask that question now.
4. If the owner cannot answer a `Q:`, split it into smaller `Q:` sub-asks.

Each sub-ask is a row in Asks: Parent set to the ask, Status Fill, no Kind. The prefixes are in `Triage · Rules`.
