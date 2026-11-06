"""Run a tool as a subprocess: no shell, filtered environment, timeout, output cap."""
import json
import os
import subprocess
import sys

from . import argv as argvmod
from . import secrets
from .manifest import validate

BASE_ENV = ("PATH", "HOME", "USERPROFILE", "SYSTEMROOT", "SYSTEMDRIVE", "WINDIR", "COMSPEC",
            "TEMP", "TMP", "TMPDIR", "LANG", "LC_ALL", "PATHEXT", "APPDATA", "LOCALAPPDATA",
            "HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY", "http_proxy", "https_proxy", "no_proxy",
            "SSL_CERT_FILE", "REQUESTS_CA_BUNDLE", "NODE_EXTRA_CA_CERTS")
MAX_STDOUT = 100_000
MAX_STDERR = 8_000
PYTHON_NAMES = ("python", "python3", "py")


class Result:
    def __init__(self, text, is_error=False, data=None):
        self.text, self.is_error, self.data = text, is_error, data


def resolve_command(tool):
    cmd = list(tool.command)
    if cmd[0] in PYTHON_NAMES:
        cmd[0] = sys.executable  # the same interpreter as the server: portable on Windows
    elif cmd[0].startswith("./") or cmd[0].startswith(".\\"):
        cmd[0] = os.path.normpath(os.path.join(os.path.dirname(tool.source), cmd[0]))
    return cmd


def environment(tool, source=None):
    src = os.environ if source is None else source
    env = {k: src[k] for k in BASE_ENV if k in src}
    env["PYTHONIOENCODING"] = "utf-8"
    # A tool runs in its manifest folder, so it gets the project folder here (same rule as search_roots).
    env["CLAUDE_PROJECT_DIR"] = src.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    missing = []
    for name in tool.env:
        optional = name.endswith("?")
        key = name.rstrip("?")
        if key in src:
            env[key] = src[key]
        elif not optional:
            missing.append(key)
    return env, missing


def run(tool, arguments):
    try:
        args = validate(tool, arguments or {})
        argv = argvmod.build(resolve_command(tool), tool.args, args)
    except ValueError as e:
        return Result(f"Invalid arguments for {tool.name}: {e}", is_error=True)
    env, missing = environment(tool)
    problem = None
    if missing:
        found, problem = secrets.resolve(missing)
        env.update(found)
        missing = [m for m in missing if m not in found]
    if missing:
        return Result(f"{tool.name} needs these environment variables: {', '.join(missing)}. "
                      "Set them in the environment of the MCP client, or add them to the "
                      "1Password vault (core:secrets)." + (f"\n{problem}" if problem else ""),
                      is_error=True)
    try:
        p = subprocess.run(argv, cwd=tool.cwd, env=env, capture_output=True,
                           timeout=tool.timeout, stdin=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        return Result(f"{tool.name} stopped after {tool.timeout:g} s (timeout).", is_error=True)
    except OSError as e:
        return Result(f"{tool.name} could not start: {e}", is_error=True)
    out = _cap(p.stdout.decode("utf-8", "replace"), MAX_STDOUT)
    err = _cap(p.stderr.decode("utf-8", "replace"), MAX_STDERR)
    if p.returncode != 0:
        return Result(f"{tool.name} failed with exit code {p.returncode}.\n{err or out}".rstrip(), is_error=True)
    data = None
    if tool.output == "json":
        try:
            data = json.loads(out)
        except ValueError:
            return Result(f"{tool.name} returned output that is not valid JSON.\n{out[:2000]}", is_error=True)
    return Result(out, data=data)


def _cap(s, limit):
    b = s.encode("utf-8")
    if len(b) <= limit:
        return s
    return b[:limit].decode("utf-8", "ignore") + f"\n[truncated {len(b) - limit} bytes]"
