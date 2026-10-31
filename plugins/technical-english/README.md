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
| SubagentStart | Core rules (subagents do not get the output style) |
| PostToolUse (`Write` of `.md`, `.html`, `.txt`) | One-line check |
| PostToolUse (`Artifact`) | One-line check |

The hooks use only `cat` on prepared JSON files. They work on macOS, Linux and Windows (Git Bash).

## Change the rules

| To change | Edit | Then |
|---|---|---|
| Core rules | `rules/core.md` | Run the build |
| Layout rules or examples | `SKILL.md` | Nothing |
| Words | `references/words.md` | Nothing |
| Hook text | `hooks/context/*.json` | Nothing |

The build copies `rules/core.md` into the output style and the subagent hook:

```bash
python scripts/build.py
```

Before you commit, make sure that the copies are current:

```bash
python scripts/build.py --check
```

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
