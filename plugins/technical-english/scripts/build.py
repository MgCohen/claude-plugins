"""Copy rules/core.md into the output style and the subagent hook.

Usage:
    python scripts/build.py          Write the generated files.
    python scripts/build.py --check  Write nothing. Exit 1 if a file is out of date.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORE = ROOT / "rules" / "core.md"
STYLE = ROOT / "output-styles" / "technical-english.md"
SUBAGENT = ROOT / "hooks" / "context" / "subagent-start.json"
MARKERS = re.compile(r"(<!-- generated:core from rules/core.md -->\n)(?:.*?\n)?(<!-- /generated:core -->)", re.S)


def text_of(path):
    """Read a file with LF line ends, also when git wrote CRLF."""
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


def outputs():
    core = text_of(CORE).strip()
    style = text_of(STYLE)
    if not MARKERS.search(style):
        raise SystemExit("Missing the generated:core markers in the output style")
    subagent = {
        "hookSpecificOutput": {
            "hookEventName": "SubagentStart",
            "additionalContext": core + "\n\nWrite your final report and every file you create or edit in STE.",
        }
    }
    return {
        STYLE: MARKERS.sub(lambda m: m.group(1) + core + "\n" + m.group(2), style),
        SUBAGENT: json.dumps(subagent, indent=2, ensure_ascii=False) + "\n",
    }


def main():
    check = "--check" in sys.argv
    stale = []
    for path, content in outputs().items():
        current = text_of(path) if path.exists() else None
        if current == content:
            continue
        stale.append(path.relative_to(ROOT).as_posix())
        if not check:
            path.write_bytes(content.encode("utf-8"))
    if check and stale:
        print("Out of date. Run: python scripts/build.py")
        print("\n".join("  " + p for p in stale))
        sys.exit(1)
    print("Updated: " + ", ".join(stale) if stale else "All generated files are current.")


if __name__ == "__main__":
    main()
