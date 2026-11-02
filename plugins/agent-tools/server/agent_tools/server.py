"""MCP server over stdio (JSON-RPC 2.0, one JSON object on each line). Standard library only.

Discovery: the server scans for manifests once, at start. The built-in tool
agent_tools_refresh scans again and sends notifications/tools/list_changed if the
tools changed. An optional watcher (poll > 0) does the same on a timer.
"""
import json
import sys
import threading

from . import __version__
from . import manifest as mf
from .runner import run

SUPPORTED = ("2025-11-25", "2025-06-18", "2025-03-26", "2024-11-05")
STRUCTURED_FROM = "2025-06-18"
REFRESH_TOOL = {
    "name": "agent_tools_refresh",
    "description": "Scan the project again for tool.toml manifests and update the tool list. "
                   "Use it after you add, change or remove a manifest in this session. "
                   "Returns the tools that were added, removed or changed, and any manifest errors.",
    "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    "annotations": {"title": "agent_tools_refresh", "readOnlyHint": True, "openWorldHint": False},
}


class Server:
    def __init__(self, roots, allow_write=False, poll=0, out=None, inp=None, log=None):
        self.roots = roots
        self.allow_write = allow_write
        self.poll = poll
        self.out = out or sys.stdout.buffer
        self.inp = inp or sys.stdin.buffer
        self.log = log or sys.stderr
        self.lock = threading.Lock()
        self.version = SUPPORTED[0]
        self.stop = threading.Event()
        self.fp = mf.fingerprint(roots)  # baseline of the watcher: the state at load time
        self.tools, errors = mf.load_all(roots, allow_write)
        self._report(errors)

    # --- transport ---------------------------------------------------------

    def send(self, msg):
        data = (json.dumps(msg, ensure_ascii=False) + "\n").encode("utf-8")
        with self.lock:
            self.out.write(data)
            self.out.flush()

    def serve(self):
        if self.poll:
            threading.Thread(target=self._watch, daemon=True).start()
        try:
            for line in self.inp:
                line = line.strip()
                if not line:
                    continue
                try:
                    msg = json.loads(line)
                except ValueError:
                    self.send({"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}})
                    continue
                for m in (msg if isinstance(msg, list) else [msg]):
                    self._dispatch(m)
        finally:
            self.stop.set()

    def _dispatch(self, msg):
        mid, method = msg.get("id"), msg.get("method")
        if mid is None:
            return  # notification: initialized, cancelled, ...
        handler = {"initialize": self.initialize, "ping": lambda p: {},
                   "tools/list": self.list_tools, "tools/call": self.call_tool}.get(method)
        if handler is None:
            self.send({"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": f"Method not found: {method}"}})
            return
        try:
            result = handler(msg.get("params") or {})
            self.send({"jsonrpc": "2.0", "id": mid, "result": result})
        except Exception as e:  # never let one request stop the server
            self.send({"jsonrpc": "2.0", "id": mid, "error": {"code": -32603, "message": str(e)}})

    # --- methods ----------------------------------------------------------

    def initialize(self, params):
        asked = params.get("protocolVersion")
        self.version = asked if asked in SUPPORTED else SUPPORTED[0]
        return {
            "protocolVersion": self.version,
            "capabilities": {"tools": {"listChanged": True}},
            "serverInfo": {"name": "agent-tools", "version": __version__},
            "instructions": "Tools from tool.toml manifests. Each tool runs one local script and returns its output.",
        }

    def list_tools(self, params):
        tools = [self._describe(t) for t in self.tools.values()]
        return {"tools": [REFRESH_TOOL] + tools}

    def call_tool(self, params):
        name = params.get("name")
        if name == REFRESH_TOOL["name"]:
            return {"content": [{"type": "text", "text": self.refresh()}], "isError": False}
        tool = self.tools.get(name)
        if tool is None:
            return {"content": [{"type": "text", "text": f"Unknown tool {name!r}. "
                                 f"Call {REFRESH_TOOL['name']} if you added it in this session."}],
                    "isError": True}
        r = run(tool, params.get("arguments"))
        out = {"content": [{"type": "text", "text": r.text}], "isError": r.is_error}
        if r.data is not None and isinstance(r.data, dict) and self.version >= STRUCTURED_FROM:
            out["structuredContent"] = r.data
        return out

    # --- discovery --------------------------------------------------------

    def reload(self):
        self.fp = mf.fingerprint(self.roots)
        self.tools, errors = mf.load_all(self.roots, self.allow_write)
        self._report(errors)
        return errors

    def refresh(self):
        """Scan again. Send list_changed if the set of tools or a manifest changed."""
        before = {n: (t.source, t.description, t.schema) for n, t in self.tools.items()}
        errors = self.reload()
        after = {n: (t.source, t.description, t.schema) for n, t in self.tools.items()}
        added = sorted(set(after) - set(before))
        removed = sorted(set(before) - set(after))
        changed = sorted(n for n in set(after) & set(before) if after[n] != before[n])
        if added or removed or changed:
            self.send({"jsonrpc": "2.0", "method": "notifications/tools/list_changed"})
        lines = [f"{len(after)} tools loaded."]
        for label, names in (("Added", added), ("Removed", removed), ("Changed", changed)):
            if names:
                lines.append(f"{label}: {', '.join(names)}")
        if not (added or removed or changed):
            lines.append("No change.")
        lines += [f"Manifest error: {e}" for e in errors]
        return "\n".join(lines)

    def _describe(self, t):
        d = {"name": t.name, "description": t.description, "inputSchema": t.schema,
             "annotations": {"title": t.name, "readOnlyHint": t.effect == "read",
                             "destructiveHint": t.effect == "write", "openWorldHint": True}}
        return d

    def _watch(self):
        while not self.stop.wait(self.poll):
            if mf.fingerprint(self.roots) != self.fp:
                self.refresh()

    def _report(self, errors):
        for e in errors:
            print(f"agent-tools: skipped: {e}", file=self.log, flush=True)
