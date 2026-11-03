"""Drift check: the argv that tool.toml builds must parse with the real CLI parser."""
import os
import re
import tomllib
import unittest

from notion_context.cli import build_parser

MANIFEST = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tool.toml")
PH = re.compile(r"\{([a-z][a-z0-9_]*)(\?|\*|\|[^}]*)?\}")  # same as agent-tools argv.PH


def sample(spec):
    if "enum" in spec:
        return spec["enum"][0]
    return {"string": "X-1", "integer": 1, "number": 1, "boolean": True, "array": ["A=b"]}[spec["type"]]


def expand(template, values):
    out = []
    for el in template:
        m = PH.search(el)
        if not m:
            out.append(el)
            continue
        v, mod = values[m.group(1)], m.group(2) or ""
        if mod.startswith("|"):
            out.append(mod[1:])
        elif mod == "*":
            out += [el[:m.start()] + str(x) + el[m.end():] for x in v]
        else:
            out.append(el[:m.start()] + str(v) + el[m.end():])
    return out


class ToolManifestTests(unittest.TestCase):
    def test_each_tool_parses_with_all_inputs(self):
        with open(MANIFEST, "rb") as f:
            raw = tomllib.load(f)
        self.assertTrue(raw["tool"])
        for tool in raw["tool"]:
            with self.subTest(tool=tool["name"]):
                values = {k: sample(s) for k, s in tool.get("input", {}).items()}
                argv = expand(tool["args"], values)
                build_parser().parse_args(argv)  # SystemExit on an unknown flag or a missing value


if __name__ == "__main__":
    unittest.main()
