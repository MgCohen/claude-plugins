---
name: secrets
description: Get API keys, tokens and passwords for scripts and tools from 1Password, without the values in the chat. Use when a command, script, CLI, build or service needs a secret (for example INBOX_TOKEN, NOTION_TOKEN, a Cloudflare or GitHub token), when a secret is missing, or when the user asks to store, find or use a secret.
---

# Secrets from 1Password

All secrets for agents are in the 1Password vault `agent`. A service account opens that vault, and only that vault, with read and write access. Its token is the environment variable `OP_SERVICE_ACCOUNT_TOKEN`, the only secret on each machine.

```
1Password vault "agent" ──► op run --env-file secrets.env -- <command>
                              └─ the values exist only in that command's environment
```

## Rules

- Never print, echo, log or write a secret value. This includes the chat, files, commit messages, PR text and memory.
- Use `op run` to give secrets to a command. Do not use `op read` to see a value.
- If you must pipe a value (for example into `wrangler secret put`), use `op read "<reference>" | <command>` in Bash. Do not pipe in Windows PowerShell 5.1: it adds characters.
- Never type a secret into a web form or a browser field. Ask the user to do that.
- Never put a secret in a URL or a query string.
- To add a secret, pipe a JSON item into `op item create --vault agent` (see "Add a secret"). Never put a value in a command argument.
- Do not change or delete an item, unless the user asks.
- Each read counts against a limit of 1,000 reads a day for the account. Do not call `op` in a loop.

## Desktop app and CLI

The user and the agent both change the same vault. A secret that one of them adds is available immediately, on each machine and in the cloud. The app and the CLI do not conflict. The app does not include `op`.

## Names

`secrets.env` (next to this file) maps each environment variable to its 1Password reference. It holds references only, never values.

| Item in vault `agent` | Field | Environment variable |
|---|---|---|
| Title = the variable name, for example `INBOX_TOKEN` | `credential` | Same as the title |

Exception: `NOTION_TOKEN` uses the item `NOTION_API_TOKEN`.

Reference format: `op://agent/<ITEM>/credential`. Use the item type "API Credential" for new items.

## Steps

1. Find the variable in `secrets.env`. If it is not there, make the item (see "Add a secret"). If you do not have the value, ask the user for the item. Then add the line to `secrets.env` in `MgCohen/claude-plugins`.
2. Run the command with the wrapper:
   - Windows (PowerShell): `& "<skill folder>/scripts/with-secrets.ps1" <command> <args>`
   - Bash (Windows Git Bash, Linux, cloud): `"<skill folder>/scripts/with-secrets.sh" <command> <args>`
3. If the wrapper fails, read the error:

| Error | Cause | Action |
|---|---|---|
| `OP_SERVICE_ACCOUNT_TOKEN is not set` | No token on this machine | Ask the user to set it as a user environment variable (Windows) or in the cloud environment settings |
| `op is not installed` | No CLI | Windows: `winget install --id AgileBits.1Password.CLI --exact`. Linux and cloud: `with-secrets.sh` installs it. If that fails, read its output. |
| `isn't an item` or `could not find item` | The item does not exist | Ask the user to create it in vault `agent` |
| `rate limit` | The daily limit is reached | Stop. Tell the user. The limit resets after 24 hours. |

## Add a secret

Make the JSON in a pipe, so the value is never in a command argument or in the output. Bash example, for a token from `gh`:

```bash
gh auth token | python -c "import json,sys;print(json.dumps({'title':'NAME','category':'API_CREDENTIAL','fields':[{'id':'credential','type':'CONCEALED','label':'credential','value':sys.stdin.read().strip()}]}))" | with-secrets.sh op item create --vault agent --format json > /dev/null
```

Then add the line `NAME=op://agent/NAME/credential` to `secrets.env`.

## Wrappers

The wrappers do these steps:

1. They find `op`.
2. They find `OP_SERVICE_ACCOUNT_TOKEN`. On Windows they also read the user environment in the registry, because a process that started before the token was set does not see it.
3. They run `op run --env-file secrets.env -- <command>`.

`op run` masks secret values in the command output.

## Agent tools

The agent-tools MCP server reads this `secrets.env` by itself. If a tool declares a required `env` variable that is not set, the server gets it with `op read` and keeps it in memory until the session stops. The tools need no wrapper. See `plugins/agent-tools/README.md`.

## Cloud sessions

Cloud environments are settings of the Claude account, not of a repository. One environment serves all projects.

1. Set `OP_SERVICE_ACCOUNT_TOKEN` in the environment variables of the cloud environment. This is the only setting.
2. `with-secrets.sh` installs `op` the first time that it does not find it on Linux (`scripts/install-op-linux.sh`, a few seconds).
3. Optional: to install `op` before the first use, put `curl -fsSL <raw URL of install-op-linux.sh> | sh` in the setup script of the environment.
