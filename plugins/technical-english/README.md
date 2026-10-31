# Technical English (ASD-STE100)

This plugin makes Claude write in ASD-STE100 Simplified Technical English (STE).

## Contents

| Part | File | What it does |
|---|---|---|
| Skill | `skills/technical-english/` | The ten direct rules, how to apply STE to replies, files, artifacts, graphs and subagents, a review step, a rules quick reference, a word substitution list, and layout rules (`references/layout.md`). |
| Output style | `output-styles/technical-english.md` | Forced for the plugin (`force-for-plugin: true`). It keeps the default coding instructions and adds the STE rules to the system prompt. |
| Hook: SessionStart | `hooks/hooks.json` | Adds the core rules at startup, resume, clear and compact. |
| Hook: UserPromptSubmit | `hooks/hooks.json` | Adds a one-line reminder on each turn. |
| Hook: SubagentStart | `hooks/hooks.json` | Adds the core rules to each subagent, and tells it to write its report and files in STE. |
| Hook: PostToolUse | `hooks/hooks.json` | After `Artifact`, and after `Write` of `.md`, `.html` or `.txt` files, adds the review checklist. |

The hooks use only `cat` on prepared JSON files. They work on macOS, Linux and Windows (Git Bash).

## Install

This plugin is in the `mgcohen` marketplace (`MgCohen/claude-plugins`). On claude.ai, enable
`technical-english` in that marketplace. It then syncs to each Claude Code session that is signed
in to this account.

Local-only alternative:

```
claude plugin install technical-english@mgcohen --scope user
```

## Local test

```
claude --plugin-dir ./technical-english
```

## House limits

The plugin is stricter than ASD-STE100. Procedure sentences: 15 words maximum (standard: 20).
Descriptive sentences: 20 words maximum (standard: 25). Paragraphs: four sentences maximum
(standard: six). `references/layout.md` adds limits for tables, graphs, documents and splits, and rules for visuals first, tabs and foldables.

## Source of the rules

The rules are a summary of ASD-STE100. They are not the standard. Get the current issue and the
full dictionary from asd-ste100.org.
