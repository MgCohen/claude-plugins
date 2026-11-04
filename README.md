# claude-plugins

Personal Claude Code plugin marketplace (`mgcohen`). Add it once on claude.ai and it syncs to every Claude Code session signed in to this account.

## Plugins

| Plugin | What it does |
|---|---|
| `core` | Personal skills, agents and hooks that follow me everywhere. Skill `spawn` starts a background session with Remote Control on. Skill `secrets` gives commands their secrets from the 1Password vault `agent` with `op run`. |
| `writing` | Writes all output in ASD-STE100 Simplified Technical English, with content rules for each kind of text (documents, commits, PRs, code comments). |
| `agent-tools` | One MCP server that exposes local scripts as tools, from `tool.toml` manifests. To add a tool, see `plugins/agent-tools/ADD-A-TOOL.md`. |
| `notion-context` | Reads a Notion page and its related pages as one document. Needs `agent-tools`, which exposes `notion_get` and `notion_query`. |
| `triage` | Runs the Linear Triage intake: `/idea` captures a request, `/triage` moves the stalest one a step. See [its README](plugins/triage/README.md). |

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

## Plugin notes

- `core`: personal skills, agents and hooks.
- `agent-tools`: one MCP server for local scripts. Each tool declares itself in a `tool.toml` file in the project, in an installed plugin, or in a folder from `agent-tools.toml`. See `plugins/agent-tools/README.md`.
- `notion-context`: a plugin with only a `tool.toml` and its script. agent-tools finds it in the installed plugins. Put `notion-context.toml` in the root of each project, and set `NOTION_TOKEN`. See `plugins/notion-context/README.md`.
- `unity-worktrees`: every worktree session in a Unity repo gets a worktree beside the repo (`<repo>.wt/<name>`) made by the Unity CLI (`unity vcs git worktree add`), with its `Library` seeded so Unity doesn't re-import. In other repos it makes the plain worktree Claude Code would. Removing a session's worktree keeps it while it has uncommitted changes, and always keeps the branch. Option `seed`: `cache` (default), `full` or `none`. A `PreToolUse` hook denies `git worktree add` (also `git -C <path> worktree add`) from the Bash and PowerShell tools in a Unity repo, and the `unity-worktree` skill gives the Unity CLI command to use. Needs the Unity CLI (`unity`) on PATH. Enable it per Unity repo in that repo's `.claude/settings.json`:

  ```json
  {
    "extraKnownMarketplaces": { "mgcohen": { "source": { "source": "github", "repo": "MgCohen/claude-plugins" } } },
    "enabledPlugins": { "unity-worktrees@mgcohen": true }
  }
  ```

  It ships plain command hooks, not a mod: a mod's hooks module loads after the session's worktree is made, so it can't create it.

## Limits

- Plugins can't ship `permissions` or `env`. Keep those in `~/.claude/settings.json` (local) and in the cloud environment settings (cloud).
- Hooks run on Windows (local) and Linux (cloud), so keep commands portable (`bash`/`node`, `${CLAUDE_PLUGIN_ROOT}` for paths).
- Plugin `CLAUDE.md` is not loaded; put standing guidance in a skill.
