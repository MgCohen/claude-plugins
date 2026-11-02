"""Find and load tool manifests (tool.toml), and compile their input schemas.

A manifest folder is any directory that holds a `tool.toml` file, one level
below a search root: <root>/<folder>/tool.toml.
"""
import os
import re
import tomllib
from dataclasses import dataclass, field

from .argv import placeholders

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


def search_roots(plugin_root=None, project_dir=None, extra=None):
    """Ordered roots: plugin tools, project tools, then AGENT_TOOLS_PATH entries."""
    roots = []
    if plugin_root:
        roots.append(os.path.join(plugin_root, "tools"))
    project = project_dir or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    roots.append(os.path.join(project, "tools"))
    for p in (extra if extra is not None else os.environ.get("AGENT_TOOLS_PATH", "")).split(os.pathsep):
        if p:
            roots.append(p)
    seen, out = set(), []
    for r in roots:
        r = os.path.abspath(r)
        if r not in seen:
            seen.add(r)
            out.append(r)
    return out


def manifest_paths(roots):
    for root in roots:
        if not os.path.isdir(root):
            continue
        for entry in sorted(os.listdir(root)):
            p = os.path.join(root, entry, "tool.toml")
            if os.path.isfile(p):
                yield p


def fingerprint(roots):
    """Changes when a manifest is added, removed or edited."""
    out = []
    for p in manifest_paths(roots):
        try:
            out.append((p, os.stat(p).st_mtime_ns))
        except OSError:
            pass
    return tuple(out)


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
        except (OSError, tomllib.TOMLDecodeError) as e:
            errors.append(f"{path}: {e}")
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
    inputs = d.get("input", {})
    for name, spec in inputs.items():
        _check_input(where, name, spec)
    try:
        used = placeholders(d["args"])
    except ValueError as e:
        raise ManifestError(f"tool {where}: {e}") from None
    unknown = used - set(inputs)
    if unknown:
        raise ManifestError(f"tool {where}: args use undeclared inputs {sorted(unknown)}")
    unused = set(inputs) - used
    if unused:
        raise ManifestError(f"tool {where}: inputs not used in args {sorted(unused)}")
    t = Tool(name=d["name"], description=desc, command=d["command"], args=d["args"], input=inputs,
             output=d["output"], effect=d["effect"], env=list(d["env"]), timeout=float(d["timeout"]),
             cwd=os.path.normpath(os.path.join(folder, d["cwd"])), source=path, enabled=bool(d["enabled"]))
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
