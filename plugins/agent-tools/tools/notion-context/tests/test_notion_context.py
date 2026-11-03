import os
import tempfile
import unittest
from unittest import mock

from notion_context import config as cfgmod
from notion_context.blocks import BodyReader
from notion_context.builder import Builder
from notion_context.props import filter_for, flatten, parse_key, value
from notion_context.render import to_markdown

from fake import FakeClient, block, checkbox, key, rel, rt, select, text, title

SPECS, ISSUES, TASKS = "db-specs", "db-issues", "db-tasks"

CONFIG = {
    "databases": {
        "specs": {"id": SPECS, "key": "Key", "document": "spec"},
        "issues": {"id": ISSUES, "key": "Key", "document": "issue"},
        "tasks": {"id": TASKS},
    },
    "documents": {
        "spec": {"database": "specs", "fields": ["Status"], "sections": [
            {"title": "Issues", "database": "issues", "backlink": "Spec", "document": "issue"},
        ]},
        "issue": {"database": "issues", "fields": ["Status"], "body": False, "sections": [
            {"title": "Tasks", "database": "tasks", "backlink": "Issue", "style": "list", "columns": ["Done"]},
            {"title": "Specs", "database": "specs", "backlink": "Issues", "style": "full", "document": "spec"},
        ]},
        "spec-fwd": {"database": "specs", "body": False, "sections": [
            {"title": "Issues", "database": "issues", "relation": "Issues", "columns": ["Key", "Title"],
             "filter": ["Status=!Done"]},
        ]},
    },
}


def workspace():
    c = FakeClient()
    c.add_db(SPECS, {"Key": {"type": "unique_id", "unique_id": {"prefix": "SPEC"}},
                     "Name": {"type": "title"}, "Status": {"type": "select"},
                     "Issues": {"type": "relation"}})
    c.add_db(ISSUES, {"Key": {"type": "unique_id", "unique_id": {"prefix": "ISS"}},
                      "Title": {"type": "title"}, "Status": {"type": "select"}, "Spec": {"type": "relation"}})
    c.add_db(TASKS, {"Task": {"type": "title"}, "Done": {"type": "checkbox"}, "Issue": {"type": "relation"}})
    c.add_page(SPECS, "s1", {"Key": key("SPEC", 1), "Name": title("Spec one"), "Status": select("Review"),
                             "Issues": rel("i1", "i2")},
               body=[block("heading_2", "Problem"), block("paragraph", "Text one.")])
    c.add_page(SPECS, "s2", {"Key": key("SPEC", 2), "Name": title("Spec two"), "Status": select("Draft"),
                             "Issues": rel("i3")})
    c.add_page(ISSUES, "i2", {"Key": key("ISS", 2), "Title": title("Second"), "Status": select("Done"),
                              "Spec": rel("s1")})
    c.add_page(ISSUES, "i1", {"Key": key("ISS", 1), "Title": title("First"), "Status": select("Ready"),
                              "Spec": rel("s1")})
    c.add_page(ISSUES, "i3", {"Key": key("ISS", 3), "Title": title("Other spec"), "Status": select("Ready"),
                              "Spec": rel("s2")})
    c.add_page(TASKS, "t1", {"Task": title("Do it"), "Done": checkbox(False), "Issue": rel("i1")})
    return c


class ConfigTests(unittest.TestCase):
    def test_valid_config_parses(self):
        cfg = cfgmod.parse(CONFIG)
        self.assertEqual(cfg.document("spec").sections[0].style, "full")

    def test_section_needs_exactly_one_source(self):
        bad = {"databases": {"a": {"id": "x"}}, "documents": {"d": {"database": "a", "sections": [
            {"title": "S", "database": "a", "backlink": "P", "relation": "Q"}]}}}
        with self.assertRaisesRegex(cfgmod.ConfigError, "exactly one"):
            cfgmod.parse(bad)

    def test_unknown_keys_and_references_fail(self):
        with self.assertRaisesRegex(cfgmod.ConfigError, "unknown keys"):
            cfgmod.parse({"databases": {"a": {"id": "x", "colour": "red"}}})
        with self.assertRaisesRegex(cfgmod.ConfigError, "'database' is required"):
            cfgmod.parse({"databases": {}, "documents": {"d": {}}})
        with self.assertRaisesRegex(cfgmod.ConfigError, "unknown database"):
            cfgmod.parse({"databases": {}, "documents": {"d": {"database": "missing"}}})

    def test_find_path_falls_back_to_project_dir(self):
        with tempfile.TemporaryDirectory() as proj, tempfile.TemporaryDirectory() as here:
            cfg = os.path.join(proj, "notion-context.toml")
            open(cfg, "w").close()
            old = os.getcwd()
            os.chdir(here)
            try:
                with mock.patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": proj}):
                    os.environ.pop("NOTION_CONTEXT_CONFIG", None)
                    self.assertEqual(cfgmod.find_path(), cfg)
                with mock.patch.dict(os.environ, {}, clear=True):
                    with self.assertRaisesRegex(cfgmod.ConfigError, "CLAUDE_PROJECT_DIR"):
                        cfgmod.find_path()
            finally:
                os.chdir(old)

    def test_db_lookup_by_alias_or_id(self):
        cfg = cfgmod.parse(CONFIG)
        self.assertEqual(cfg.db("db-issues").alias, "issues")
        self.assertEqual(cfg.db("issues").id, ISSUES)


class PropsTests(unittest.TestCase):
    def test_values(self):
        self.assertEqual(value(key("ISS", 4)), "ISS-4")
        self.assertEqual(value(select(None)), None)
        self.assertEqual(value(rel("a", "b")), ["a", "b"])
        self.assertEqual(value({"type": "date", "date": {"start": "2026-01-01", "end": "2026-01-02"}}),
                         "2026-01-01/2026-01-02")
        self.assertEqual(value({"type": "formula", "formula": {"type": "number", "number": 3}}), 3)

    def test_flatten_drops_empty_values(self):
        page = {"id": "p", "properties": {"A": text(""), "B": select("X")}}
        self.assertEqual(flatten(page), {"B": "X", "id": "p"})

    def test_filters_by_type(self):
        self.assertEqual(filter_for("S", "status", "!Done"), {"property": "S", "status": {"does_not_equal": "Done"}})
        self.assertEqual(filter_for("D", "checkbox", "no"), {"property": "D", "checkbox": {"equals": False}})
        self.assertEqual(filter_for("K", "unique_id", "ISS-7"), {"property": "K", "unique_id": {"equals": 7}})
        self.assertEqual(filter_for("K", "unique_id", "!ISS-7"), {"property": "K", "unique_id": {"does_not_equal": 7}})
        with self.assertRaisesRegex(ValueError, "negate"):
            filter_for("D", "date", "!2026-01-01")
        with self.assertRaises(ValueError):
            filter_for("F", "formula", "x")

    def test_parse_key(self):
        self.assertEqual(parse_key("SPEC-12"), ("SPEC", 12))
        self.assertEqual(parse_key("12"), (None, 12))
        with self.assertRaises(ValueError):
            parse_key("SPEC-x")


class BodyTests(unittest.TestCase):
    def test_nested_blocks_to_markdown(self):
        c = FakeClient()
        linked = block("child_database", title="View")
        c.linked.add(linked["id"])
        table = block("table", children=[block("table_row", cells=[rt("a"), rt("b")]),
                                         block("table_row", cells=[rt("1"), rt("x|y")])])
        c.bodies["p"] = [
            block("heading_2", "Head"),
            block("bulleted_list_item", "one", children=[block("numbered_list_item", "inner")]),
            block("to_do", "task", checked=True),
            block("code", "print(1)", language="python"),
            table,
            block("paragraph", "bold", children=None),
            block("heading_2", "Related"),
            linked,
        ]
        c.bodies["p"][5]["paragraph"]["rich_text"] = rt("bold", bold=True)
        md = BodyReader(c).markdown("p")
        self.assertEqual(md, "\n".join([
            "## Head", "", "- one", "  1. inner", "- [x] task",
            "```python", "print(1)", "```", "",
            "| a | b |", "|---|---|", "| 1 | x\\|y |", "",
            "**bold**", "",
        ]))  # linked view and its empty heading are dropped


class BuilderTests(unittest.TestCase):
    def setUp(self):
        self.client = workspace()
        self.builder = Builder(self.client, cfgmod.parse(CONFIG))

    def test_spec_shows_only_its_own_issues(self):
        node = self.builder.get("SPEC-1")
        issues = node["sections"][0]["items"]
        self.assertEqual([i["key"] for i in issues], ["ISS-1", "ISS-2"])  # sorted, ISS-3 excluded
        self.assertEqual(issues[0]["sections"][0]["items"][0]["title"], "Do it")

    def test_cycles_stop(self):
        node = self.builder.get("SPEC-1")
        back = node["sections"][0]["items"][0]["sections"][1]["items"][0]
        self.assertNotIn("sections", back)  # SPEC-1 -> ISS-1 -> SPEC-1 is a one-line item
        self.assertEqual(back["key"], "SPEC-1")

    def test_forward_relation_with_filter(self):
        node = self.builder.get("SPEC-1", document="spec-fwd")
        self.assertEqual([i["key"] for i in node["sections"][0]["items"]], ["ISS-1"])

    def test_unknown_prefix_and_missing_key(self):
        with self.assertRaisesRegex(cfgmod.ConfigError, "prefix"):
            self.builder.get("ADR-1")
        with self.assertRaises(LookupError):
            self.builder.get("SPEC-9")

    def test_markdown_render(self):
        md = to_markdown(self.builder.get("SPEC-1"))
        self.assertTrue(md.startswith("# SPEC-1: Spec one\n\n- **Status:** Review\n\n## Problem\n\nText one.\n"))
        self.assertIn("## Issues (2)\n\n### ISS-1: First", md)
        self.assertIn("#### Tasks (1)\n\n- Do it (Done: no)", md)


if __name__ == "__main__":
    unittest.main()
