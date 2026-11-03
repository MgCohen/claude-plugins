"""Find and load tool manifests (tool.toml), and compile their input schemas.

A manifest is a file named `tool.toml` at any depth below a search root
(see search_roots). In a git work tree, `git ls-files` finds them (tracked files, and new files
that .gitignore does not exclude). Elsewhere, a folder walk finds them.
Both skip the folders in EXCLUDE_DIRS and AGENT_TOOLS_EXCLUDE.
"""
import json
import os
import re
import subprocess
import tomllib
from dataclasses import dataclass, field

from .argv import placeholder_modes

NAME_RE = re.compile(r"^[a-z][a-z0-9_]{0,47}$")
TYPES = {"string", "integer", "number", "boolean", "array"}
EFFECTS = {"read", "write"}
OUTPUTS = {"text", "json"}
TOOL_KEYS = {"name", "description", "command", "args", "input", "output", "effect",
             "env", "timeout", "cwd", "enabled"}
INPUT_KEYS = {"type", "description", "required", "enum", "default", "items"}
DEFAULTS = {"output": "text", "effect": "read", "env": [], "timeout": 60, "cwd": ".", "enabled": True}


class ManifestError(Exception):
    pass


@dataclass
class Tool:
    name: str
    description: str
    command: list
    args: list
    input: dict
    output: str
    effect: str
    env: list          # names; a trailing "?" marks an optional variable
    timeout: float
    cwd: str           # absolute
    source: str        # manifest path
    enabled: bool = True
    schema: dict = field(default_factory=dict)


MANIFEST = "tool.toml"
EXCLUDE_DIRS = {"node_modules", "bin", "obj", "dist", "build", "target", "venv", "__pycache__",
                "Library", "Temp", "Logs", "fixtures"}
MAX_DEPTH = 10


CONFIG = "agent-tools.toml"
PLUGIN_STORES = ("cache", "synced")   # below <claude config>/plugins/
PLUGIN_JSON = os.path.join(".claude-plugin", "plugin.json")
PLUGIN_DEPTH = 4                       # cache/<marketplace>/<plugin>/<version>


def claude_dir():
    return os.environ.get("CLAUDE_CONFIG_DIR") or os.path.join(os.path.expanduser("~"), ".claude")


def search_roots(plugin_root=None, project_dir=None, extra=None, errors=None):
    """Ordered roots. The first manifest that declares a tool name wins.

    1. <agent-tools>/tools/  2. the project  3. paths from the project and user agent-tools.toml
    4. AGENT_TOOLS_PATH  5. the newest copy of each other installed plugin.
    Problems with an agent-tools.toml go to `errors` (a list), if given.
    """
    errors = [] if errors is None else errors
    project = project_dir or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    roots = []
    if plugin_root:
        roots.append(os.path.join(plugin_root, "tools"))
    roots.append(project)
    scan_plugins = True
    for cfg in (os.path.join(project, ".claude", CONFIG), os.path.join(claude_dir(), CONFIG)):
        paths, plugins = read_config(cfg, errors)
        roots += paths
        scan_plugins = scan_plugins and plugins
    for p in (extra if extra is not None else os.environ.get("AGENT_TOOLS_PATH", "")).split(os.pathsep):
        if p:
            roots.append(os.path.expanduser(p))
    if scan_plugins:
        roots += installed_plugins(skip=plugin_root)
    seen, out = set(), []
    for r in roots:
        r = os.path.abspath(r)
        if r not in seen:
            seen.add(r)
            out.append(r)
    return out


def read_config(path, errors):
    """-> (extra roots, scan installed plugins?). A missing file gives ([], True)."""
    if not os.path.isfile(path):
        return [], True
    try:
        with open(path, "rb") as f:
            raw = tomllib.load(f)
    except (OSError, tomllib.TOMLDecodeError) as e:
        errors.append(f"{path}: {type(e).__name__}: {e}")
        return [], True
    unknown = set(raw) - {"paths", "plugins"}
    paths, plugins = raw.get("paths", []), raw.get("plugins", True)
    if unknown:
        errors.append(f"{path}: unknown keys {sorted(unknown)}; use paths and plugins")
    if not (isinstance(paths, list) and all(isinstance(p, str) for p in paths)):
        errors.append(f"{path}: paths must be a list of strings")
        paths = []
    if not isinstance(plugins, bool):
        errors.append(f"{path}: plugins must be true or false")
        plugins = True
    base = os.path.dirname(os.path.abspath(path))
    return [os.path.join(base, os.path.expanduser(p)) for p in paths], plugins


def installed_plugins(home=None, skip=None):
    """Root folder of the newest copy of each installed plugin, except `skip` and its name.

    Claude Code keeps old versions (cache/<marketplace>/<plugin>/<version>/) and old
    generations (synced/<id>/<plugin>~gN/) on disk. Only the newest plugin.json counts.
    """
    home = home or os.path.join(claude_dir(), "plugins")
    skip_name = _plugin_name(skip) if skip else None
    best = {}
    for store in PLUGIN_STORES:
        top = os.path.join(home, store)
        base = top.rstrip(os.sep).count(os.sep)
        for folder, dirs, _ in os.walk(top):
            if os.path.isfile(os.path.join(folder, PLUGIN_JSON)):
                dirs[:] = []
                name = _plugin_name(folder)
                if not name or name == skip_name:
                    continue
                group = os.path.relpath(folder, top).split(os.sep)[0]  # marketplace or sync id
                key = (store, group, name)
                mtime = os.path.getmtime(os.path.join(folder, PLUGIN_JSON))
                if key not in best or mtime > best[key][0]:
                    best[key] = (mtime, folder)
                continue
            depth = folder.count(os.sep) - base
            dirs[:] = sorted(d for d in dirs if not d.startswith(".") and depth < PLUGIN_DEPTH)
    return [folder for _, folder in sorted(best.values(), key=lambda v: v[1])]


def _plugin_name(root):
    try:
        with open(os.path.join(root, PLUGIN_JSON), encoding="utf-8") as f:
            name = json.load(f).get("name")
    except (OSError, ValueError, AttributeError):
        return None
    return name if isinstance(name, str) and name else None


def excluded_dirs():
    extra = {d for d in os.environ.get("AGENT_TOOLS_EXCLUDE", "").split(os.pathsep) if d}
    return EXCLUDE_DIRS | extra


def manifest_paths(roots):
    seen = set()
    for root in roots:
        if not os.path.isdir(root):
            continue
        found = _git_manifests(root)
        if found is None:
            found = _walk_manifests(root)
        skip = excluded_dirs()
        for p in sorted(found):
            rel = os.path.relpath(p, root).split(os.sep)[:-1]
            if any(part in skip or part.startswith(".") for part in rel):
                continue
            if p not in seen and os.path.isfile(p):
                seen.add(p)
                yield p


def _git_manifests(root):
    """Manifest paths from git, or None if root is not in a git work tree."""
    try:
        r = subprocess.run(
            ["git", "-C", root, "ls-files", "-z", "--cached", "--others", "--exclude-standard",
             "--", MANIFEST, f":(glob)**/{MANIFEST}"],
            capture_output=True, timeout=15, stdin=subprocess.DEVNULL)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if r.returncode != 0:
        return None
    names = [n for n in r.stdout.decode("utf-8", "replace").split("\0") if n]
    return [os.path.normpath(os.path.join(root, n)) for n in names]


def _walk_manifests(root):
    skip = excluded_dirs()
    out = []
    base = root.rstrip(os.sep).count(os.sep)
    for folder, dirs, files in os.walk(root):
        depth = folder.count(os.sep) - base
        dirs[:] = [d for d in dirs if d not in skip and not d.startswith(".") and depth < MAX_DEPTH]
        if MANIFEST in files:
            out.append(os.path.join(folder, MANIFEST))
    return out


def load_all(roots, allow_write=False):
    """-> (tools by name, list of error strings). Bad manifests are skipped."""
    tools, errors = {}, []
    for path in manifest_paths(roots):
        try:
            for t in load(path):
                if not t.enabled:
                    continue
                if t.effect == "write" and not allow_write:
                    continue
                if t.name in tools:
                    errors.append(f"{path}: tool {t.name!r} is already defined in {tools[t.name].source}")
                    continue
                tools[t.name] = t
        except ManifestError as e:
            errors.append(f"{path}: {e}")
        except (OSError, tomllib.TOMLDecodeError, TypeError, ValueError, AttributeError, KeyError) as e:
            errors.append(f"{path}: {type(e).__name__}: {e}")  # one bad manifest never stops the server
    return tools, errors


def load(path):
    with open(path, "rb") as f:
        raw = tomllib.load(f)
    extra = set(raw) - {"defaults", "tool"}
    if extra:
        raise ManifestError(f"unknown top-level keys {sorted(extra)}")
    base = dict(DEFAULTS, **raw.get("defaults", {}))
    entries = raw.get("tool", [])
    if not entries:
        raise ManifestError("no [[tool]] entries")
    folder = os.path.dirname(os.path.abspath(path))
    return [_tool(dict(base, **e), folder, path) for e in entries]


def _tool(d, folder, path):
    where = d.get("name", "?")
    extra = set(d) - TOOL_KEYS
    if extra:
        raise ManifestError(f"tool {where}: unknown keys {sorted(extra)}")
    for k in ("name", "description", "command", "args"):
        if k not in d:
            raise ManifestError(f"tool {where}: {k!r} is required")
    if not NAME_RE.match(d["name"]):
        raise ManifestError(f"tool {where}: name must match {NAME_RE.pattern}")
    if d["name"].startswith("agent_tools_"):
        raise ManifestError(f"tool {where}: the prefix agent_tools_ is reserved for built-in tools")
    if not isinstance(d["description"], str):
        raise ManifestError(f"tool {where}: description must be a string")
    desc = " ".join(d["description"].split())
    if not 20 <= len(desc) <= 1024:
        raise ManifestError(f"tool {where}: description must be 20 to 1024 characters")
    if not (isinstance(d["command"], list) and d["command"] and all(isinstance(c, str) for c in d["command"])):
        raise ManifestError(f"tool {where}: command must be a non-empty list of strings")
    if not (isinstance(d["args"], list) and all(isinstance(a, str) for a in d["args"])):
        raise ManifestError(f"tool {where}: args must be a list of strings")
    if d["effect"] not in EFFECTS:
        raise ManifestError(f"tool {where}: effect must be one of {sorted(EFFECTS)}")
    if d["output"] not in OUTPUTS:
        raise ManifestError(f"tool {where}: output must be one of {sorted(OUTPUTS)}")
    if not isinstance(d["timeout"], (int, float)) or isinstance(d["timeout"], bool) or d["timeout"] <= 0:
        raise ManifestError(f"tool {where}: timeout must be a number above 0")
    if not (isinstance(d["env"], list) and all(isinstance(e, str) for e in d["env"])):
        raise ManifestError(f"tool {where}: env must be a list of strings")
    if not isinstance(d["cwd"], str) or not isinstance(d["enabled"], bool):
        raise ManifestError(f"tool {where}: cwd must be a string and enabled a boolean")
    inputs = d.get("input", {})
    if not isinstance(inputs, dict):
        raise ManifestError(f"tool {where}: input must be a table")
    for name, spec in inputs.items():
        if not isinstance(spec, dict):
            raise ManifestError(f"tool {where}: input {name} must be a table")
        _check_input(where, name, spec)
    try:
        mods = placeholder_modes(d["args"])
    except ValueError as e:
        raise ManifestError(f"tool {where}: {e}") from None
    used = set(mods)
    for name, mode in mods.items():
        t = inputs.get(name, {}).get("type")
        if t is None:
            continue
        if mode == "*" and t != "array":
            raise ManifestError(f"tool {where}: {{{name}*}} needs an array input")
        if mode == "|" and t != "boolean":
            raise ManifestError(f"tool {where}: {{{name}|...}} needs a boolean input")
        if mode in ("", "?") and t == "array":
            raise ManifestError(f"tool {where}: array input {name} needs {{{name}*}}")
    unknown = used - set(inputs)
    if unknown:
        raise ManifestError(f"tool {where}: args use undeclared inputs {sorted(unknown)}")
    unused = set(inputs) - used
    if unused:
        raise ManifestError(f"tool {where}: inputs not used in args {sorted(unused)}")
    t = Tool(name=d["name"], description=desc, command=d["command"], args=d["args"], input=inputs,
             output=d["output"], effect=d["effect"], env=list(d["env"]), timeout=float(d["timeout"]),
             cwd=os.path.normpath(os.path.join(folder, d["cwd"])), source=path, enabled=d["enabled"])
    t.schema = compile_schema(inputs)
    return t


def _check_input(tool, name, spec):
    if not re.match(r"^[a-z][a-z0-9_]*$", name):
        raise ManifestError(f"tool {tool}: input name {name!r} must be snake_case")
    extra = set(spec) - INPUT_KEYS
    if extra:
        raise ManifestError(f"tool {tool}: input {name}: unknown keys {sorted(extra)}")
    if spec.get("type") not in TYPES:
        raise ManifestError(f"tool {tool}: input {name}: type must be one of {sorted(TYPES)}")
    if spec["type"] == "array" and spec.get("items", "string") not in TYPES - {"array"}:
        raise ManifestError(f"tool {tool}: input {name}: items must be a scalar type")
    if not spec.get("description") and not spec.get("enum"):
        raise ManifestError(f"tool {tool}: input {name}: give a description or an enum")


def compile_schema(inputs):
    props, required = {}, []
    for name, spec in inputs.items():
        p = {"type": spec["type"]}
        if spec["type"] == "array":
            p["items"] = {"type": spec.get("items", "string")}
        for k in ("description", "enum", "default"):
            if k in spec:
                p[k] = spec[k]
        props[name] = p
        if spec.get("required"):
            required.append(name)
    schema = {"type": "object", "properties": props, "additionalProperties": False}
    if required:
        schema["required"] = required
    return schema


PY_TYPES = {"string": str, "integer": int, "number": (int, float), "boolean": bool, "array": list}


def validate(tool, args):
    """Return a clean argument dict with defaults, or raise ValueError."""
    if not isinstance(args, dict):
        raise ValueError("arguments must be an object")
    extra = set(args) - set(tool.input)
    if extra:
        raise ValueError(f"unknown arguments {sorted(extra)}; allowed: {sorted(tool.input)}")
    out = {}
    for name, spec in tool.input.items():
        if name not in args or args[name] is None:
            if spec.get("required"):
                raise ValueError(f"{name!r} is required")
            if "default" in spec:
                out[name] = spec["default"]
            continue
        v = args[name]
        t = spec["type"]
        if t == "boolean" and not isinstance(v, bool):
            raise ValueError(f"{name!r} must be a boolean")
        if t in ("integer", "number") and isinstance(v, bool):
            raise ValueError(f"{name!r} must be a {t}")
        if not isinstance(v, PY_TYPES[t]):
            raise ValueError(f"{name!r} must be a {t}")
        if t == "array":
            it = spec.get("items", "string")
            for x in v:
                ok = isinstance(x, bool) if it == "boolean" else (
                    isinstance(x, PY_TYPES[it]) and not isinstance(x, bool))
                if not ok:
                    raise ValueError(f"{name!r} items must be {it}")
        if "enum" in spec and v not in spec["enum"]:
            raise ValueError(f"{name!r} must be one of {spec['enum']}")
        out[name] = v
    return out
