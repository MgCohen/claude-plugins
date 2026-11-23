---
name: orch-reply
description: The fixed formats for the replies of an orchestrator session to the user, with a template for each kind of reply - status block, question, reminder, closed question, short status. Use it for each reply of a root session, and for a question that a child writes in its own chat.
---

# Reply formats

Use these templates for each reply to the user. Copy the structure, then put in the values. Do not add other sections. Keep the order of the sections. If a section has no items, do not show it. "Waits for you" is always the first section.

| Reply | When | Template |
|---|---|---|
| Status block | After a report, an answer or a new child, when one or more items wait for the user | [Status block](#status-block) |
| Short status | After a change, when nothing waits for the user | [Short status](#short-status) |
| Question | A message "Question from child" arrives, or a child asks the user in its own chat | [Question](#question) |
| Reminder | A message "Reminder:" arrives | [Status block](#status-block), with the question again under "Waits for you" |
| Closed question | A message "Question closed:" arrives | [Short status](#short-status) or [Status block](#status-block), with the item under "Done" |

## Words

| Word | Meaning |
|---|---|
| ⏳ Waits for you | The user must act: a question with no answer |
| 🔄 Working | A child runs, and nobody must act |
| ✅ Done | A child reported done, or a question has an answer |
| ⛔ Blocked | A child cannot continue. The user or the root must act |

Write how each value came: `auto`, `your answer`, `default after <time>`, or `docs`.

## Status block

```markdown
**⏳ Waits for you (2)**

1. **Child 2 (ask)** - Which number does child 2 give to the sum?
   - Options: any whole number
   - Recommendation: 7
   - Default: none. It waits for you.
2. **Child 4 (approve)** - May I do step 2?
   - Options: yes; no
   - Recommendation: yes
   - Default: "yes" in 80 s

**🔄 Working (1)**

- Child 3 (chat): waits for your numbers in its chat

**✅ Done (1)**

| Child | Result | How |
|---|---|---|
| 1 (auto) | 47 | auto |

**Total:** 47
```

Rules:

- Number the questions. The user answers by number or by child, for example "2: yes".
- Show the time until the default only if the question has a default.
- The last line is the result of the run so far, if the run has one.

## Short status

```markdown
✅ Child 2 reported 7. Nothing waits for you. 🔄 2 working, ✅ 3 done. **Total:** 54
```

One line. Use it only when nothing waits for the user.

## Question

```markdown
**⏳ Question from child 2 (ask)**

Which number does child 2 give to the sum?

- Context: the child adds this number to the total.
- Options: any whole number
- Recommendation: 7
- Default: none. It waits for you.

Answer here. I send your words to the child.
```

A child that asks in its own chat uses the same template, with the title "⏳ Question" and the last line "In the chat, start the answer with `answer:`. You can also answer in the root session."

In a child chat, only a message that starts with `answer:` closes the question. A message without `answer:` is a normal message: the question stays open.

## Answers of the user

1. If the user answers a question, call `mcp__orch__answer` with the question id and the words of the user.
2. If `mcp__orch__answer` says that the question already has an answer, tell the user who answered it and the answer. Then move it to "Done".
3. If the user asks which questions are open, call `mcp__orch__questions`, then reply with the status block.
