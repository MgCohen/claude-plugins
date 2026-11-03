# agent-tools

**To add a tool, read [ADD-A-TOOL.md](ADD-A-TOOL.md) (five steps).** This README is the full reference.

`agent-tools` is one MCP server that exposes local scripts as tools. Each tool declares itself in a `tool.toml` manifest next to its script, anywhere in the project. You keep no central list. The server uses only the Python 3.11+ standard library.

```mermaid
flowchart LR
    S[Session start] --> H[Hook: catalog into context]
    S --> B[Server: scan for tool.toml]
    B --> C[Tool list]
    A[Agent] -->|tools/call| D[Validate, build argv]
    D --> F[Run subprocess]
    F -->|text or JSON| A
    A -->|agent_tools_refresh| B
```

## Discovery

| When | What happens |
|---|---|
| Session start | The server scans once and loads the tools. The `SessionStart` hook writes a short catalog (each name and its first sentence) into the context |
| On demand | The built-in tool `agent_tools_refresh` scans again. If the tools changed, it sends `notifications/tools/list_changed` |

If you add a manifest during a session, the new tool appears only after a refresh. The prefix `agent_tools_` is reserved for built-in tools.

## Where tools live

A manifest is a file named `tool.toml` at any depth below a search root.

| Order | Search root | Use it for |
|---|---|---|
| 1 | `<plugin>/tools/` | Tools for every project |
| 2 | `<project>/` | Tools of one repository, in any folder |
| 3 | Each path in `AGENT_TOOLS_PATH` | Other folders, for example a personal tool folder |

- In a git work tree, `git ls-files` finds the manifests. It includes new files and obeys `.gitignore`. Elsewhere, a folder walk finds them, 10 levels deep maximum.
- Both skip hidden folders and `node_modules`, `bin`, `obj`, `dist`, `build`, `target`, `venv`, `__pycache__`, `Library`, `Temp`, `Logs` and `fixtures`. Add folder names to `AGENT_TOOLS_EXCLUDE`.
- `<project>` is `$CLAUDE_PROJECT_DIR` if it is set, else the server's current folder.
- `AGENT_TOOLS_PATH` and `AGENT_TOOLS_EXCLUDE` use the path separator of the system (`:` on Linux and macOS, `;` on Windows).
- If two manifests declare the same tool name, the first one wins. `check` shows the conflict.

## Manifest (`tool.toml`)

One manifest can declare one or more tools. `[defaults]` gives shared values to each `[[tool]]` entry.

```toml
[defaults]
command = ["python3", "-m", "notion_context"]   # argv, never a shell string
env = ["NOTION_TOKEN", "NOTION_CONTEXT_CONFIG?"] # "?" = optional
timeout = 120

[[tool]]
name = "notion_get"
description = """Read one Notion page by its key, with its related pages, as one document. \
Use it before you work on a spec or an issue. Returns Markdown."""
args = ["get", "{key}", "--doc={doc?}", "--format={format}"]
[tool.input]
key    = { type = "string", required = true, description = "Page key, for example SPEC-1" }
doc    = { type = "string", description = "Document recipe" }
format = { type = "string", enum = ["md", "json"], default = "md" }
```

### Tool keys

| Key | Required | Default | Rule |
|---|---|---|---|
| `name` | Yes | None | `snake_case`, 48 characters maximum, unique |
| `description` | Yes | None | 20–1024 characters. What, when, what it returns |
| `command` | Yes | None | List. `python3`, `python` or `py` use the server's Python |
| `args` | Yes | None | List of argv templates (see below) |
| `input` | No | None | Table of inputs (see below) |
| `output` | No | `text` | `text` or `json` (JSON object → `structuredContent`) |
| `effect` | No | `read` | `read` or `write`. The server hides write tools |
| `env` | No | None | Variable names to pass. `NAME?` is optional |
| `timeout` | No | `60` | Seconds |
| `cwd` | No | `.` | Relative to the manifest folder |
| `enabled` | No | `true` | `false` hides the tool |

A `command` that starts with `./` is relative to the manifest folder.

### Input keys

| Key | Rule |
|---|---|
| `type` | `string`, `integer`, `number`, `boolean` or `array` |
| `description` | Required, unless `enum` is set |
| `required` | `true` or `false` |
| `enum` | List of permitted values |
| `default` | Used when the agent gives no value |
| `items` | Item type of an `array`. Default `string` |

Each input must appear in `args`, and each placeholder in `args` must be an input. `check` reports a mismatch.

### Argv templates

Each element of `args` has one placeholder maximum.

| Template | Value | Result |
|---|---|---|
| `"{key}"` | `"SPEC-1"` | `SPEC-1`. Error if no value |
| `"--doc={doc?}"` | None | The element is removed |
| `"--where={where*}"` | `["A=1", "B=2"]` | `--where=A=1 --where=B=2` |
| `"{verbose\|--verbose}"` | `true` | `--verbose`. Removed if `false` |

A value in a standalone placeholder (`"{key}"`, or an item of `"{items*}"`) cannot start with `-`. This stops option injection. It also rejects a negative number such as `-5`. Attach the value to its flag (`"--n={n}"`) if it can start with `-`.

The modifier must agree with the input type: `*` only for `array`, `|` only for `boolean`, and no modifier or `?` only for the other types.

## What the server does for each call

1. Validates the arguments against the input schema. If they are not valid, it returns `isError` with the reason.
2. Builds argv as a list and runs it with no shell.
3. Passes only a base environment (`PATH`, `HOME`, proxy and certificate variables) and the `env` names of the tool. It also sets `CLAUDE_PROJECT_DIR` to the project folder, because the tool runs in its manifest folder.
4. Stops the process after `timeout`.
5. Cuts stdout to 100 KB and stderr to 8 KB.
6. If the exit code is not 0, returns `isError` with stderr.

## Trust

The server runs the commands that the manifests in the opened project declare. Treat a `tool.toml` like a script in the repository:

- Enable the plugin only for repositories that you trust. A manifest in a cloned repository can run any program that is on `PATH`.
- `effect = "read"` is what the manifest says about itself. The server does not verify it.
- The `SessionStart` catalog puts tool descriptions from the repository into the session context. Do not trust the text of a manifest that you did not read.
- `cwd` and a `./` command are relative to the manifest folder, and can use `..`.

## Install

The plugin starts the server automatically (`.mcp.json` → `sh server/run.sh serve`). `run.sh` uses the first Python 3.11+ on `PATH`.

On Windows, Claude Code starts the MCP server as a Windows process, not in Git Bash. Thus, `sh.exe` must be on the Windows `PATH`. The default Git for Windows install adds only `Git\cmd`. Add `C:\Program Files\Git\usr\bin` (or `Git\bin`) to `PATH`, or the server does not start.

Plugins cannot ship environment values. Set each variable that a tool declares, for example `NOTION_TOKEN`, in `~/.claude/settings.json` (`env`) or in the cloud environment settings.

## Commands

Run them from the project folder:

```sh
python3 <plugin>/server/main.py check                 # validate manifests, show the search roots
python3 <plugin>/server/main.py list                  # tools that the server exposes
python3 <plugin>/server/main.py catalog               # the text that the SessionStart hook writes
python3 <plugin>/server/main.py call notion_get '{"key":"SPEC-1"}'
```

| Option | Use |
|---|---|
| `--root PATH` | Add a search root. You can repeat it |
| `--project PATH` | Set the project folder |
| `--allow-write` or `AGENT_TOOLS_ALLOW_WRITE=1` | Also expose `effect = "write"` tools |

## Refresh: client support

`agent_tools_refresh` needs a client that acts on `list_changed`.

| Client | `list_changed` | If not supported |
|---|---|---|
| Claude Code 2.1.0 or later | Yes | Not applicable |
| Cursor | Not reliable | Restart the server |
| Others | Unknown | Reconnect (`/mcp`) or start a new session |

With tool search, Claude Code loads only the tool names at start. The full description loads when the agent searches. Thus, the description must contain the words that an agent searches for.

## Tests

```sh
cd server && python3 -m unittest discover -s tests
```

The tests start the real server as a subprocess. They call a fixture tool, add a manifest and call `agent_tools_refresh`, and check the git scan with `.gitignore`.
