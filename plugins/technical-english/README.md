# Technical English (ASD-STE100)

This plugin makes Claude write in ASD-STE100 Simplified Technical English (STE). It also adds
house rules for visuals, tables, graphs and long documents.

## Parts

Each rule is in one file that Claude reads.

| Part | File | When it loads | Contains |
|---|---|---|---|
| Output style | `output-styles/technical-english.md` | Always (forced) | Core rules |
| Skill | `skills/technical-english/SKILL.md` | Before documents | Examples, layout, limits |
| Word list | `skills/technical-english/references/words.md` | When necessary | Word substitutions |
| Hooks | `hooks/hooks.json` | See the hook table | Short pointers |

| Hook | Text |
|---|---|
| UserPromptSubmit | One-line reminder |
| SubagentStart | The output style rules, from `hooks/subagent-start.sh` (subagents do not get the output style) |
| PostToolUse (`Write` of `.md`, `.html`, `.txt`) | One-line check |
| PostToolUse (`Artifact`) | One-line check |

The hooks use `cat` on prepared JSON files, and `sh` with `awk` for the subagent rules. They work
on macOS, Linux and Windows (Git Bash).

## Change the rules

| To change | Edit |
|---|---|
| Core rules | `output-styles/technical-english.md` (subagents get the change automatically) |
| Layout rules or examples | `skills/technical-english/SKILL.md` |
| Words | `skills/technical-english/references/words.md` |
| Other hook text | `hooks/context/*.json` |

## Install

The plugin is in the `MgCohen/claude-plugins` marketplace. Enable `technical-english` in that
marketplace on claude.ai. claude.ai syncs it to each Claude Code session of this account.

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

The rules are a summary of ASD-STE100, not the standard. Get the full dictionary from
asd-ste100.org.
