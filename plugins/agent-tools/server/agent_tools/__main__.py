"""CLI: serve | list | check | call.

  serve            run the MCP server on stdio
  list             print the tools that the server would expose
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
    s = sub.add_parser("serve")
    s.add_argument("--poll", type=float, default=2.0, help="seconds between manifest checks; 0 = off")
    sub.add_parser("list")
    sub.add_parser("check")
    c = sub.add_parser("call")
    c.add_argument("name")
    c.add_argument("arguments", nargs="?", default="{}", help="JSON object")
    a = p.parse_args(argv)

    roots = mf.search_roots(PLUGIN_ROOT, a.project)
    roots += [os.path.abspath(r) for r in a.root if os.path.abspath(r) not in roots]

    if a.cmd == "serve":
        Server(roots, a.allow_write, a.poll).serve()
        return 0
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


if __name__ == "__main__":
    sys.exit(main())
