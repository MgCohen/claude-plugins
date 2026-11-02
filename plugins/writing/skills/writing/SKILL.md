---
name: writing
description: Rules for all written output in ASD-STE100 Simplified Technical English (STE), for each kind of text. Load it before you write a document, an artifact, a README, a report, slides, a commit message, a PR description or code comments. Also load it when the user asks for "technical English", "STE" or "ASD-STE100".
---

# Writing

Each kind of text has its own content rules. All kinds use the same language rules.

## Step 1: identify the kind of text

| You write | Read |
|---|---|
| A chat reply | Nothing more. The output style has the rules. |
| A document, artifact, README, report or slides | `language.md`, then `documents.md` |
| A commit message or a PR description | `language.md`, then `commits-prs.md` |
| Code comments or docstrings | `language.md`, then `code-comments.md` |
| A prompt for a subagent or another session | `language.md` |

If one task writes more than one kind, read the file for each kind.

## Step 2: put each fact in the correct kind of text

| Fact | Correct place |
|---|---|
| The current state: design, API, behavior | Document body |
| A change: what was added, removed or replaced | Commit message, PR description, changelog |
| A rejected option that readers may propose again | "Non-goals" section of the document, as a rule with a reason |
| An item that is not decided | "Open questions" section of the document, or the chat |
| Why the code does something unusual | Code comment |

## Step 3: examine the text before you deliver

Use the check list at the end of each file that you read. Fix each problem in the source.

## When not to apply it

- User text, quotes, error messages, log lines and code stay as they are.
- If the user asks for a different style for one output, use it for that output only.
- Non-English output: keep the principles, but do not translate the dictionary.
