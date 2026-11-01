# Linear Triage

Every new request or idea goes to the `Triage` project in Linear first. This plugin moves each request, one small step at a time, from a raw idea to a task, project or initiative at the correct place.

## How a request moves

```
/idea ─► 1 Captured ─► 2 Classify ─► 3 Fill ─► 4 Review ─► Exit
                          │             ▲          │
                     kind + template    └─ change ─┘
Any stage ─► Closed (Canceled or Duplicate)
```

| Stage | Claude does | You do |
|---|---|---|
| 1 · Captured | Creates the issue | Give the idea |
| 2 · Classify | Proposes a kind (Bug, Feature, Chore …) | Accept or change the kind |
| 3 · Fill | Researches and proposes one section at a time | Accept, edit or skip |
| 4 · Review | Runs the review checklist | Approve |
| Exit | Moves or creates the item, sets labels | Nothing |

## Install

On claude.ai, enable `triage` in the `MgCohen/claude-plugins` marketplace. Or, in Claude Code:

```
/plugin install triage --marketplace MgCohen/claude-plugins
```

## Start it

| Command | Effect |
|---|---|
| `/idea <text>` | Captures a new request. No interview starts. |
| `/triage` | Takes the stalest issue and moves it one step |
| `/triage MAT-49` | Moves that issue one step |

The skill also starts on "idea:", "next in triage", "skip" and "approve".

## Small steps

- Each question has a proposed answer and 2 to 3 options.
- If you skip an issue two times, Claude splits the open section into smaller `Q:` sub-issues.
- The issue description holds only accepted text. Research and drafts go into sub-issues (`Q:`, `Ctx:`, `Draft:`).

## Where the rules live

The rules live in Linear, not in this plugin. To change a rule, edit Linear. The plugin does not need a release.

| Rule | Linear location |
|---|---|
| Stages, queue, skip, exit steps | Project `Triage`, description |
| Kinds, signals, review checklist | Document `Triage · Kinds` |
| Sections of one kind | Document `Template · <Kind>` |

To add a kind of work, add a row to `Triage · Kinds` and copy a template document.

## Plugin layout

```
.claude-plugin/plugin.json
commands/idea.md, triage.md
skills/triage/SKILL.md         # Rule 0 and mode router
skills/triage/references/      # one file for each mode
```

Needs the Linear MCP server, connected to workspace `mgcohen`.
