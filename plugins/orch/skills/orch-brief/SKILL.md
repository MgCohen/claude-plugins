---
name: orch-brief
description: How to start a child session with mcp__orch__spawn_child (the brief template), and the rules for child sessions. Use it before you split work into child sessions.
---

# Start a child session

A child knows only its brief. A short brief that names skills works better than a long brief that repeats them.

## Fill the brief template

`orch template brief` shows the fields.

| Field | Content |
|---|---|
| `title` | A short title that names all of the scope of the child |
| `goal` | What the child must make, and why. Put the steps here if the order matters |
| `scope` | What is in scope and what is not |
| `doneWhen` | The check that shows that the work is done |
| `skills` | The skills to load first, for example `orch-ask`, `orch-report`, `orch-stack` |
| `type` | The custom agent of the child, for example `decider`. Default: the agent of its role, `worker` or `orchestrator`. The old field `agent` stays valid |
| `stream` | The stream id, for example `C`. Default: your stream |
| `workflow` | The workflow that the child runs or works in, for example `planning` |
| `cwd` | The working folder. Default: your folder |
| `worktree` | `true` if two children change one repository at the same time |
| `background` | `true` only for a session that the user does not need to see on the phone. Default: Remote Control is on |

## The spawn path

`mcp__orch__spawn_child` is the only way to start a child. Never use `core:spawn`, and never call `start_session` with a prompt of your own. The orch path gives the child its store entry, its brief, its Remote Control and its archive steps.

| Your turn | Do |
|---|---|
| A desktop app turn | Call `spawn_child`. The result gives one `start_session` call. Make that call exactly as given |
| A Remote Control turn (the message came from the phone or claude.ai) | Call `spawn_child` with `inApp: false`. The app refuses `start_session` in this turn |
| The `start_session` call is refused, or the tool is missing | Do not try again. Call `spawn_child` again with the same fields and `inApp: false` |
| A `claude -p` supervisor turn | Call `spawn_child`. The supervisor starts the child |

Example: a root in a Remote Control turn.

```
1. mcp__orch__spawn_child { title: "C1 toy task", goal: "...", doneWhen: "...", inApp: false }
   -> Started child "C1 toy task" (1a2b3c4d-...).
2. End the turn.
   The supervisor makes the child, opens it in the app, and sends it the notice remote-control-self.
   The child turns its own Remote Control on. Its report arrives as "Report from child".
```

## Archive a child

1. Run `orch archive <child id>`. It sends the child the notice `archive-self` and waits for the app.
2. If the app keeps the child for the user (pinned, or open on screen), `orch archive` cannot archive it in the app. You get the notice `archive-child`, or the user gets `user-archive-child`. Do not try again: tell the user to archive it from the sidebar.
3. If a process holds the worktree folder, run `orch archive <child id> --store-only`. The folder stays.

## Rules

- Give each child one task: one area of work, one owner of its questions.
- Give a task an id: the stream letter and a number, for example `C2`.
- A child reports `done` or `blocked`. You get the report as a message that starts with "Report from child".
- After you start children and have nothing else to do, end your turn. Do not wait in a loop.
- Do not archive a child that waits for the user, or a child that has an open PR.
