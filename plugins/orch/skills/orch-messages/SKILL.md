---
name: orch-messages
description: Which orch tool to use for each message to the user, the parent or another session (the message types). Use it before you send anything with an mcp__orch__ tool, and when you are not sure which type fits.
---

# Message types

Each message has a type. Each type has one tool. Free text in your reply is not a message: nobody gets a card for it.

| Type | Use it when | Tool | The reader must | The reply arrives as |
|---|---|---|---|---|
| question | You need an answer: a choice with options and a default, or facts with no default | `mcp__orch__ask_user` | answer | "Answer to question" |
| plan | You propose steps before you do them | `mcp__orch__plan` | review | "Review of plan" |
| report | Your work is done, blocked, or ready for review | `mcp__orch__report` | ack (done, blocked) | A message, if any |
| update | A step starts or ends | `mcp__orch__update` | nothing | Nothing |
| message | None of the other types fits | `mcp__orch__send` | nothing | "Message from" |
| brief | You start a child session | `mcp__orch__spawn_child` | nothing | "Report from child" |
| answer | You relay the words of the user to a child question | `mcp__orch__answer` | nothing | Nothing |

## Rules

1. Pick the type first. Then fill the fields of its tool. The tool refuses fields that do not match the template.
2. A question needs only its text. For a choice, add options, a recommendation, a risk and a default. A default needs a risk. For facts, add only the context: with no default, nobody answers for the user.
3. Use `mcp__orch__send` only when no other type fits.
4. After a question or a plan, end your turn. The reply arrives as a new message.
5. The text of each new message starts with a fixed prefix: "Answer to question", "Review of decision" (a default decision), "Review of plan", "Question from child", "Plan from child", "Report from child", "Message from". The supervisor notices start with "Question closed", "Reminder", or a fixed sentence.
