"""Get the missing env variables of a tool from 1Password.

A required variable that is not in the environment is looked up in a secrets.env
file (NAME=op://vault/item/field, one on each line), and `op read` gets the value.
The default file is skills/secrets/secrets.env of the installed `core` plugin.
AGENT_TOOLS_SECRETS_ENV (a path list) replaces it.

The server keeps each value in memory until it stops, so one secret costs one
1Password read for each session. The values never go to the output or to a file.
"""
import glob
import os
import platform
import shutil
import subprocess
import sys

from . import manifest as mf

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SECRETS_PLUGIN = "core"
SECRETS_FILE = os.path.join("skills", "secrets", "secrets.env")
INSTALL_SCRIPT = os.path.join("scripts", "install-op-linux.sh")
TOKEN = "OP_SERVICE_ACCOUNT_TOKEN"
OP_ENV = ("PATH", "HOME", "USERPROFILE", "SYSTEMROOT", "SYSTEMDRIVE", "WINDIR", "TEMP", "TMP",
          "TMPDIR", "APPDATA", "LOCALAPPDATA", "XDG_CONFIG_HOME",
          "HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY", "http_proxy", "https_proxy", "no_proxy",
          "SSL_CERT_FILE")
TIMEOUT = 60

_cache = {}


def env_files(source=None):
    src = os.environ if source is None else source
    custom = src.get("AGENT_TOOLS_SECRETS_ENV")
    if custom is not None:
        return [os.path.expanduser(p) for p in custom.split(os.pathsep) if p]
    for root in mf.installed_plugins(skip=PLUGIN_ROOT):
        if mf._plugin_name(root) == SECRETS_PLUGIN and os.path.isfile(os.path.join(root, SECRETS_FILE)):
            return [os.path.join(root, SECRETS_FILE)]
    return []


def references(files):
    """-> {NAME: (reference, file)}. The first file that declares a name wins."""
    refs = {}
    for path in files:
        try:
            with open(path, encoding="utf-8") as f:
                lines = f.read().splitlines()
        except OSError:
            continue
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            name, ref = (s.strip() for s in line.split("=", 1))
            if ref.startswith("op://") and name not in refs:
                refs[name] = (ref, path)
    return refs


def token(source=None):
    src = os.environ if source is None else source
    value = src.get(TOKEN)
    if value or source is not None or sys.platform != "win32":
        return value
    # Windows: a process that started before the user set the token does not see it.
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
            return winreg.QueryValueEx(key, TOKEN)[0] or None
    except OSError:
        return None


def op_binary(env_file=None):
    found = shutil.which("op") or shutil.which("op.exe")
    if found:
        return found
    candidates = [os.path.join(os.path.expanduser("~"), ".local", "bin", "op")]
    if os.environ.get("LOCALAPPDATA"):  # winget puts op here on Windows
        candidates += glob.glob(os.path.join(os.environ["LOCALAPPDATA"], "Microsoft", "WinGet",
                                             "Packages", "AgileBits.1Password.CLI_*", "op.exe"))
    for c in candidates:
        if os.path.isfile(c):
            return c
    if platform.system() == "Linux" and env_file:
        # Cloud sessions: install op the first time. It is one file and takes a few seconds.
        script = os.path.join(os.path.dirname(env_file), INSTALL_SCRIPT)
        if os.path.isfile(script):
            subprocess.run(["sh", script], capture_output=True, timeout=120, stdin=subprocess.DEVNULL)
            return shutil.which("op") or (candidates[0] if os.path.isfile(candidates[0]) else None)
    return None


def resolve(names):
    """-> ({NAME: value}, problem text or None). Only names with a reference are looked up."""
    found = {n: _cache[n] for n in names if n in _cache}
    todo = [n for n in names if n not in found]
    if not todo:
        return found, None
    refs = references(env_files())
    todo = [n for n in todo if n in refs]
    if not todo:
        return found, None
    tok = token()
    if not tok:
        return found, (f"{TOKEN} is not set, so agent-tools cannot read {', '.join(todo)} from 1Password. "
                       "Set it in the user environment or in the cloud environment settings.")
    op = op_binary(refs[todo[0]][1])
    if not op:
        return found, ("op (the 1Password CLI) is not installed. "
                       "Windows: winget install --id AgileBits.1Password.CLI --exact")
    env = {k: os.environ[k] for k in OP_ENV if k in os.environ}
    env[TOKEN] = tok
    problems = []
    for name in todo:
        value, problem = _read(op, refs[name][0], env)
        if problem:
            problems.append(f"{name}: {problem}")
        else:
            _cache[name] = found[name] = value
    return found, ("; ".join(problems) or None)


def _read(op, ref, env):
    """-> (value, None) or (None, problem). The problem text never holds the value."""
    try:
        p = subprocess.run([op, "read", "--no-newline", ref], env=env, capture_output=True,
                           timeout=TIMEOUT, stdin=subprocess.DEVNULL)
    except (OSError, subprocess.TimeoutExpired) as e:
        return None, f"op did not run ({type(e).__name__})"
    if p.returncode != 0:
        err = p.stderr.decode("utf-8", "replace").strip().splitlines()
        return None, err[-1] if err else f"op exit code {p.returncode}"
    return p.stdout.decode("utf-8"), None
