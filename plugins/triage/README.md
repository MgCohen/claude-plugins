# Triage

Each new request or idea goes to the Asks database in the Notion teamspace Studio first. This plugin moves each ask, one small step at a time, from a raw idea to a project, feature, plan, bug, task, decision or doc at the correct place. A blocking question from an agent session does not go through triage: it goes to the Questions database.

## How an ask moves

```
/idea ─► New ─► Classify ─► Fill ─► Review ─► Converted
                   │          ▲        │
             kind + template  └ change ┘
Any status ─► Dropped
```

| Status | Claude does | You do |
|---|---|---|
| New | Makes the ask row | Give the idea |
| Classify | Proposes a kind (Bug, Feature, Chore …) | Accept or change the kind |
| Fill | Does research and proposes one section at a time | Accept, edit or skip |
| Review | Runs the review checklist | Approve |
| Converted | Makes the row in Projects, Features, Plans, Bugs, Tasks, Decisions or Docs | Nothing |

## Install

On claude.ai, enable `triage` in the `MgCohen/claude-plugins` marketplace. Or, in Claude Code:

```
/plugin install triage --marketplace MgCohen/claude-plugins
```

## Start it

| Command | Effect |
|---|---|
| `/idea <text>` | Captures a new ask. No interview starts. |
| `/triage` | Takes the stalest ask and moves it one step |
| `/triage ASK-3` | Moves that ask one step |

The skill also starts on "idea:", "next in triage", "skip" and "approve".

## Small steps

- Each question has a proposed answer and 2 to 3 options.
- If you skip an ask two times, Claude splits the open section into smaller `Q:` sub-asks.
- The ask page holds only accepted text. Research and drafts go into sub-asks (`Q:`, `Ctx:`, `Draft:`).

## Where the rules live

The rules live in Notion, not in this plugin. To change a rule, edit Notion. The plugin does not need a release.

| Rule | Notion location |
|---|---|
| Stages, queue, skip, exit steps | Docs row `Triage · Rules` |
| Kinds, signals, sections, exits, review checklist | Docs row `Triage · Kinds` |
| Form of one kind | Templates row `Ask · <Kind>` |

To add a kind of work, follow "To add a kind" in `Triage · Kinds`.

## Plugin layout

```
.claude-plugin/plugin.json
commands/idea.md, triage.md
skills/triage/SKILL.md         # Rule 0, pointer names and mode router
skills/triage/references/      # one file for each mode
```

Needs the Notion MCP server, with access to the Workflow page. The notion-context plugin gives the `notion_pointers` tool, which resolves the page and database names to ids.
