"""Build the generated parts of the plugin from the files in rules/.

Usage:
    python scripts/build.py          Write the generated files.
    python scripts/build.py --check  Write nothing. Exit 1 if a file is out of date.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RULES = ROOT / "rules"
SKILL = ROOT / "skills" / "technical-english" / "SKILL.md"
STYLE = ROOT / "output-styles" / "technical-english.md"
CONTEXT = ROOT / "hooks" / "context"


def text_of(path):
    """Read a file with LF line ends, also when git wrote CRLF."""
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


def read(name):
    return text_of(RULES / name).strip()


def hook_json(event, text):
    body = {"hookSpecificOutput": {"hookEventName": event, "additionalContext": text}}
    return json.dumps(body, indent=2, ensure_ascii=False) + "\n"


def fill_block(text, name, content):
    """Replace the text between the markers of one generated block."""
    pattern = re.compile(
        r"(<!-- generated:%s from rules/\S+ -->\n)(?:.*?\n)?(<!-- /generated:%s -->)" % (name, name),
        re.S,
    )
    if not pattern.search(text):
        raise SystemExit(f"Missing markers for block '{name}'")
    return pattern.sub(lambda m: m.group(1) + content + "\n" + m.group(2), text)


def outputs():
    core = read("core.md")
    review = read("review.md")
    files = {
        CONTEXT / "session-start.json": hook_json("SessionStart", read("session-start.md")),
        CONTEXT / "user-prompt-submit.json": hook_json("UserPromptSubmit", read("reminder.md")),
        CONTEXT / "subagent-start.json": hook_json(
            "SubagentStart",
            core + "\n\nWrite your final report and every file you create or edit in STE.",
        ),
        CONTEXT / "post-write-review.json": hook_json(
            "PostToolUse",
            "STE review: you wrote a text file.\n" + review
            + "\n\nIf you find issues, fix them in the same file. Do not publish an artifact"
            " or make any other output that the user did not ask for.",
        ),
        CONTEXT / "post-artifact-review.json": hook_json(
            "PostToolUse",
            "STE review: you published an artifact.\n" + review
            + "\n\nIf you find issues, fix the source file and publish it again to the same artifact.",
        ),
    }
    style = text_of(STYLE)
    files[STYLE] = fill_block(style, "core", core)
    skill = text_of(SKILL)
    skill = fill_block(skill, "core", core)
    files[SKILL] = fill_block(skill, "review", review)
    return files


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
