---
name: orch-ask
description: How a session under the orchestrator asks the user a question with mcp__orch__ask_user (the question template). Use it before each question to the user, and when you must decide if a question is necessary.
---

# Ask the user

The user answers in free text or by voice, often from the phone. A good question gets an answer in one read.

## When to ask

| Case | Do |
|---|---|
| The brief, `AGENTS.md`, `CLAUDE.md`, `README.md` or `docs/` answer it | Do not ask. Follow the docs |
| Easy to undo and local to the task | Decide yourself and say it in the report |
| A design, an API, a file layout or a convention | Ask, with a default option |
| Hard to undo, or an effect outside the repository | Ask, risk at the strictest level, and no default if a wrong default is dangerous |

## Fill the question template

`orch template question` shows the fields. Each call asks one question. Only `question` is required. A `defaultOption` needs a `risk`.

| Field | Content |
|---|---|
| `question` | One question, one sentence |
| `context` | Why the question comes up now, and what the user must know |
| `snippet` | Optional: the code or text that shows the problem |
| `options` | Optional: two to four suggestions. The user can answer something else |
| `recommendation` | Optional: your pick and its reason |
| `risk` | A policy level. Required with a `defaultOption`. The tool description gives the definition of each level |
| `defaultOption` | Optional: the option that applies if the user does not answer in time. With no default, the session waits for the answer |
| `waitSeconds` | 0 for most questions: the tool returns PENDING and you end your turn |

## After the call

1. If the result is PENDING, write the question in your reply. End the reply with "In the chat, start the answer with `answer:`." Then end your turn. Do not continue with a guess.
2. If the user writes a chat message that starts with `answer:`, that message is the answer. The plugin records it, and no other message comes.
3. If the user writes a chat message without `answer:`, it is not an answer. The question stays open. Reply to the message, and remind the user of the prefix.
4. An answer from the parent session or from the policy arrives as a new message: "Answer to question <id> (<question>): <text>".
5. If the answer has more instructions (a default decision), do each step in order. The skill `orch:orch-stack` explains the steps.
6. If the answer is not one of the options, follow the answer and say so in your next report.
