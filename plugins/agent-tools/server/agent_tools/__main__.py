"""CLI: serve | list | catalog | check | call.

  serve            run the MCP server on stdio
  list             print the tools that the server would expose
  catalog          print a short tool list for the session context (SessionStart hook)
  check            validate all manifests; exit 1 on errors
  call NAME JSON   run one tool, as the server does, and print the result
"""
import argparse
import json
import os
import sys

from . import manifest as mf
from .runner import run
from .server import Server

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main(argv=None):
    p = argparse.ArgumentParser(prog="agent-tools")
    p.add_argument("--root", action="append", default=[],
                   help="extra search root (folder that holds <tool>/tool.toml); repeatable")
    p.add_argument("--project", help="project folder (default: $CLAUDE_PROJECT_DIR or the current folder)")
    p.add_argument("--allow-write", action="store_true",
                   default=os.environ.get("AGENT_TOOLS_ALLOW_WRITE") == "1",
                   help="also expose tools with effect = \"write\"")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("serve")
    sub.add_parser("list")
    sub.add_parser("catalog", help="short tool list for session context (SessionStart hook)")
    sub.add_parser("check")
    c = sub.add_parser("call")
    c.add_argument("name")
    c.add_argument("arguments", nargs="?", default="{}", help="JSON object")
    a = p.parse_args(argv)

    roots = mf.search_roots(PLUGIN_ROOT, a.project)
    roots += [os.path.abspath(r) for r in a.root if os.path.abspath(r) not in roots]

    if a.cmd == "serve":
        Server(roots, a.allow_write).serve()
        return 0
    if a.cmd == "catalog":
        return _catalog(roots, a.allow_write)
    tools, errors = mf.load_all(roots, a.allow_write)
    if a.cmd == "list":
        for t in tools.values():
            print(f"{t.name}\t{t.effect}\t{t.description}")
            print(f"\tsource: {t.source}")
        for e in errors:
            print(f"skipped: {e}", file=sys.stderr)
        return 0
    if a.cmd == "check":
        print("search roots:")
        for r in roots:
            print(f"  {'ok ' if os.path.isdir(r) else '-- '} {r}")
        for t in tools.values():
            print(f"ok    {t.name} ({t.source})")
        for e in errors:
            print(f"ERROR {e}")
        return 1 if errors else 0
    if a.cmd == "call":
        tool = tools.get(a.name)
        if tool is None:
            print(f"Unknown tool {a.name!r}. Known: {', '.join(tools) or 'none'}", file=sys.stderr)
            return 2
        r = run(tool, json.loads(a.arguments))
        (sys.stderr if r.is_error else sys.stdout).write(r.text if r.text.endswith("\n") else r.text + "\n")
        return 1 if r.is_error else 0
    return 2


def _catalog(roots, allow_write):
    """Print nothing if there are no tools. Never fail: this runs at session start."""
    try:
        tools, errors = mf.load_all(roots, allow_write)
    except Exception as e:  # noqa: BLE001
        print(f"agent-tools: catalog failed: {e}", file=sys.stderr)
        return 0
    if not tools and not errors:
        return 0
    print('Agent tools (MCP server "agent-tools"). After you add or change a tool.toml, '
          "call agent_tools_refresh.")
    for t in tools.values():
        print(f"- {t.name}: {_first_sentence(t.description)}")
    if errors:
        print(f"- {len(errors)} manifest(s) have errors. Run the check command of agent-tools.")
    return 0


def _first_sentence(text, limit=160):
    s = text.split(". ")[0].rstrip(".") + "."
    return s if len(s) <= limit else s[:limit - 1].rstrip() + "…"


if __name__ == "__main__":
    sys.exit(main())
