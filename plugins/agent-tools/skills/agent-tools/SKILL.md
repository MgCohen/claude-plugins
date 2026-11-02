---
name: agent-tools
description: Make a local script available as an MCP tool with a tool.toml manifest, or fix one. Use it when the user asks to add, expose, register or change an agent tool, or when an agent-tools tool is missing or fails.
---

# Add a script as an agent tool

The `agent-tools` MCP server exposes each tool that a `tool.toml` manifest declares. The full specification is in the plugin README (`${CLAUDE_PLUGIN_ROOT}/README.md`).

## Steps

1. Put the script in its own folder: `<project>/tools/<folder>/` for one repository, or `<plugin>/tools/<folder>/` for all projects.
2. Make the script deterministic. It must write the result to stdout, write errors to stderr, and exit with a code that is not 0 on failure.
3. Write `tool.toml` in the same folder. Use one `[[tool]]` entry for each agent task, not one for each flag.
4. Run `python3 ${CLAUDE_PLUGIN_ROOT}/server/main.py check`. Fix each `ERROR` line.
5. Run `python3 ${CLAUDE_PLUGIN_ROOT}/server/main.py call <name> '<json>'` with sample input.
6. If the script is a Python CLI with argparse, add a drift test: build the argv from the manifest and give it to the parser.

## Rules for a good tool

- **Name:** `<area>_<verb>`, in snake_case, for example `notion_get`.
- **Description:** start with a verb. Say what the tool returns and when to use it. The agent reads only this text.
- **Inputs:** give each input a description or an enum. Use `enum` for each closed set of values.
- **Effect:** set `effect = "write"` if the tool changes anything outside its output. The server hides write tools unless the user starts it with `--allow-write`.
- **Secrets:** list the variable names in `env`. Never put a value in the manifest. The script must not print a secret.
- **Output:** keep it short, preferably below 25,000 tokens. Use `output = "json"` only if the script prints one JSON object or array.
- **Forbidden:** shell strings, `sh -c`, and an input that sets an output path or a command.
