# Technical English (ASD-STE100)

This plugin makes Claude write in ASD-STE100 Simplified Technical English (STE). It also adds
house rules for visuals, tables, graphs and long documents.

## How the rules reach Claude

```mermaid
flowchart LR
    core[rules/core.md] --> build[scripts/build.py]
    review[rules/review.md] --> build
    build --> style[Output style]
    build --> skill[SKILL.md blocks]
    build --> hooks[Hook context files]
    style --> main[Main agent]
    hooks --> sub[Subagents]
    hooks --> after[After Write or Artifact]
```

| Part | File | When it loads |
|---|---|---|
| Output style | `output-styles/technical-english.md` | Always (forced) |
| Skill | `skills/technical-english/SKILL.md` | When Claude loads it |
| Layout rules | `skills/technical-english/references/layout.md` | Before documents |
| Word list | `skills/technical-english/references/words.md` | When necessary |
| STE summary | `skills/technical-english/references/rules.md` | When necessary |
| Hooks | `hooks/hooks.json` | See the hook table |

| Hook | Text |
|---|---|
| SessionStart | Short pointer to the skill |
| UserPromptSubmit | One-line reminder |
| SubagentStart | Core rules, and STE for the report |
| PostToolUse (`Write` of `.md`, `.html`, `.txt`) | Review checklist |
| PostToolUse (`Artifact`) | Review checklist |

The hooks use only `cat` on prepared JSON files. They work on macOS, Linux and Windows (Git Bash).

## Change the rules

Each rule has one source file. Do not edit generated text.

| To change | Edit | Then |
|---|---|---|
| Core rules | `rules/core.md` | Run the build |
| Review checklist | `rules/review.md` | Run the build |
| Hook pointer or reminder | `rules/session-start.md`, `rules/reminder.md` | Run the build |
| Layout rules | `references/layout.md` | Change `rules/review.md` if a limit changes |
| Words | `references/words.md` | Nothing |

```bash
python scripts/build.py
```

Before you commit, make sure that the generated files are current:

```bash
python scripts/build.py --check
```

## Install

The plugin is in the `MgCohen/claude-plugins` marketplace. Enable `technical-english` in that
marketplace on claude.ai. claude.ai syncs it to each Claude Code session of this account. A new
session gets each new version.

For a local test, load the folder directly:

```bash
claude --plugin-dir ./plugins/technical-english
```

## House limits

| Item | Plugin | ASD-STE100 |
|---|---|---|
| Procedure sentence | 15 words | 20 words |
| Descriptive sentence | 20 words | 25 words |
| Paragraph | 4 sentences | 6 sentences |

## Source of the rules

The STE rules are a summary of ASD-STE100. They are not the standard. Get the current issue and
the full dictionary from asd-ste100.org.
