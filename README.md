# claude-plugins

Personal Claude Code plugin marketplace (`mgcohen`). Add it once on claude.ai and it syncs to every Claude Code session signed in to this account.

## Layout

```
.claude-plugin/marketplace.json   # marketplace catalog
plugins/core/
  .claude-plugin/plugin.json      # bump "version" on every change
  skills/<name>/SKILL.md          # skills
  agents/<name>.md                # subagents
  commands/<name>.md              # slash commands (optional)
  hooks/hooks.json                # hooks (same shape as settings.json "hooks")
```

## Install (account level)

claude.ai → Customize → Plugins → Add → Add marketplace → `MgCohen/claude-plugins`, then enable `core`.

Local-only alternative:

```
claude plugin marketplace add MgCohen/claude-plugins
claude plugin install core@mgcohen --scope user
```

## Limits

- Plugins can't ship `permissions` or `env`. Keep those in `~/.claude/settings.json` (local) and in the cloud environment settings (cloud).
- Hooks run on Windows (local) and Linux (cloud), so keep commands portable (`bash`/`node`, `${CLAUDE_PLUGIN_ROOT}` for paths).
- Plugin `CLAUDE.md` is not loaded; put standing guidance in a skill.
