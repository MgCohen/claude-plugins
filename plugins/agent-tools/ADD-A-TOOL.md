# Add a tool

Five steps. You need two files: your script and a `tool.toml` next to it.

## 1. Choose a folder

| Put the folder in | The tool is available |
|---|---|
| Any folder of your project | In that project only |
| A plugin of its own (`plugins/<name>/`, with `.claude-plugin/plugin.json`) | In all projects where the plugin is installed |
| A folder in `paths` of `~/.claude/agent-tools.toml` | In all projects on that machine |
| `<agent-tools>/tools/<name>/` | In all projects. Only for tools that ship with agent-tools |

Any folder in the project is permitted, for example next to the code that the tool uses. The server does not look in these folders:

- hidden folders (`.github`, `.claude`, …)
- paths in `.gitignore`
- folders named `node_modules`, `bin`, `obj`, `dist`, `build`, `target`, `venv`, `__pycache__`, `Library`, `Temp`, `Logs` or `fixtures`

## 2. Write the script

Use any language. The script must:

- write the result to stdout
- exit with 0 on success, and with another code on failure
- not wait for keyboard input (stdin is closed)

```
my-folder/
  hello.py        ← your script
  tool.toml       ← step 3
```

## 3. Write `tool.toml`

The file name must be exactly `tool.toml`.

```toml
[[tool]]
name = "hello"
description = "Say hello to a person. Use it to test agent tools. Returns one line of text."
command = ["python3", "hello.py"]
args = ["{name}"]

[tool.input]
name = { type = "string", required = true, description = "Who to greet" }
```

| Key | Required | Rule |
|---|---|---|
| `name` | Yes | snake_case, unique, not `agent_tools_…` |
| `description` | Yes | 20 to 1,024 characters |
| `command` | Yes | The program and its first arguments |
| `args` | Yes | Other arguments. `{x}` gives input `x`. `[]` is permitted |
| `[tool.input]` | No | One line for each input: a `type`, and a `description` or an `enum` |
| `env` | No | Environment variables that the script needs |

## 4. Test it

```sh
python3 <plugin>/server/main.py check
python3 <plugin>/server/main.py call hello '{"name": "Ana"}'
```

`check` shows each error. `call` runs the tool as the agent does. The tool runs in its own folder.

## 5. Use it

Start a new session, or ask the agent to call `agent_tools_refresh`. The agent then sees `hello` in its tool list.

## More

- `{x?}`, `{x*}`, `{x|--flag}`, `output = "json"`, `effect = "write"`, `timeout`: see [README.md](README.md).
- Languages other than Python, and Windows: see [README.md](README.md).
