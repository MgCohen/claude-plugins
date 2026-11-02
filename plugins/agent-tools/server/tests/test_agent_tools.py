import json
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import time
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from agent_tools import argv as argvmod  # noqa: E402
from agent_tools import manifest as mf  # noqa: E402
from agent_tools import runner  # noqa: E402

FIXTURES = os.path.join(HERE, "fixtures")
MAIN = os.path.join(os.path.dirname(HERE), "main.py")


def write_tool(root, folder, body):
    os.makedirs(os.path.join(root, folder), exist_ok=True)
    with open(os.path.join(root, folder, "tool.toml"), "w", encoding="utf-8") as f:
        f.write(textwrap.dedent(body))


GOOD = """
    [[tool]]
    name = "{name}"
    description = "A tool for tests. Returns a short text."
    command = ["python3", "-c", "print('hi')"]
    args = []
"""


class ManifestTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp)

    def test_fixture_loads_and_hides_write_tools(self):
        tools, errors = mf.load_all([FIXTURES])
        self.assertEqual(errors, [])
        self.assertEqual(sorted(tools), ["echo_args", "echo_fail", "echo_sleep"])
        tools, _ = mf.load_all([FIXTURES], allow_write=True)
        self.assertIn("echo_write", tools)

    def test_schema(self):
        t = mf.load_all([FIXTURES])[0]["echo_args"]
        self.assertEqual(t.schema["required"], ["word"])
        self.assertEqual(t.schema["properties"]["items"], {"type": "array", "items": {"type": "string"},
                                                           "description": "Repeated items"})
        self.assertFalse(t.schema["additionalProperties"])

    def test_bad_manifests_are_reported_not_fatal(self):
        write_tool(self.tmp, "ok", GOOD.format(name="good_tool"))
        write_tool(self.tmp, "badname", GOOD.format(name="Bad-Name"))
        write_tool(self.tmp, "unused", GOOD.format(name="x_tool") + '\n[tool.input]\nq = { type = "string", description = "d" }\n')
        write_tool(self.tmp, "dup", GOOD.format(name="good_tool"))
        write_tool(self.tmp, "syntax", "[[tool]\n")
        tools, errors = mf.load_all([self.tmp])
        self.assertEqual(list(tools), ["good_tool"])  # "dup" sorts before "ok": first wins
        text = "\n".join(errors)
        for needle in ("name must match", "inputs not used", "already defined", "syntax"):
            self.assertIn(needle, text)

    def test_search_roots_order_and_env(self):
        with mock.patch.dict(os.environ, {"AGENT_TOOLS_PATH": os.pathsep.join(["/x", "/y"])}, clear=False):
            roots = mf.search_roots("/plugin", "/proj")
        self.assertEqual(roots, [os.path.abspath(p) for p in ("/plugin/tools", "/proj/tools", "/x", "/y")])

    def test_validate(self):
        t = mf.load_all([FIXTURES])[0]["echo_args"]
        self.assertEqual(mf.validate(t, {"word": "w"}), {"word": "w", "count": 1})
        for bad, msg in (({}, "required"), ({"word": "w", "zzz": 1}, "unknown"),
                         ({"word": "w", "tag": "c"}, "one of"), ({"word": "w", "count": True}, "integer"),
                         ({"word": "w", "items": [1]}, "items must be string")):
            with self.assertRaisesRegex(ValueError, msg):
                mf.validate(t, bad)


class ArgvTests(unittest.TestCase):
    T = ["get", "{key}", "--doc={doc?}", "--where={w*}", "{v|--verbose}"]

    def test_rules(self):
        self.assertEqual(argvmod.build(["c"], self.T, {"key": "K-1"}), ["c", "get", "K-1"])
        self.assertEqual(argvmod.build(["c"], self.T, {"key": "K", "doc": "d", "w": ["a=1", "b=2"], "v": True}),
                         ["c", "get", "K", "--doc=d", "--where=a=1", "--where=b=2", "--verbose"])

    def test_missing_and_option_injection(self):
        with self.assertRaisesRegex(ValueError, "no value"):
            argvmod.build(["c"], self.T, {})
        with self.assertRaisesRegex(ValueError, "must not start"):
            argvmod.build(["c"], self.T, {"key": "--out=/etc/x"})
        self.assertEqual(argvmod.build(["c"], ["--doc={d}"], {"d": "-x"}), ["c", "--doc=-x"])  # attached: safe

    def test_one_placeholder_per_element(self):
        with self.assertRaises(ValueError):
            argvmod.placeholders(["{a}{b}"])


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.tools = mf.load_all([FIXTURES], allow_write=True)[0]

    def test_json_output_and_env_filter(self):
        with mock.patch.dict(os.environ, {"ECHO_SECRET": "s3", "ECHO_OTHER": "leak"}):
            r = runner.run(self.tools["echo_args"], {"word": "hi", "items": ["a"], "loud": True})
        self.assertFalse(r.is_error, r.text)
        self.assertEqual(r.data["argv"], ["show", "hi", "--item=a", "--loud", "--n=1"])
        self.assertEqual(r.data["secret"], "s3")
        self.assertIsNone(r.data["other"])  # not declared: not passed

    def test_required_env_missing(self):
        t = self.tools["echo_args"]
        t.env = ["ECHO_REQUIRED"]
        r = runner.run(t, {"word": "x"})
        self.assertTrue(r.is_error)
        self.assertIn("ECHO_REQUIRED", r.text)

    def test_failure_timeout_and_invalid_args(self):
        r = runner.run(self.tools["echo_fail"], {})
        self.assertTrue(r.is_error)
        self.assertIn("exit code 3", r.text)
        self.assertIn("something broke", r.text)
        r = runner.run(self.tools["echo_sleep"], {})
        self.assertTrue(r.is_error)
        self.assertIn("timeout", r.text)
        r = runner.run(self.tools["echo_args"], {"nope": 1})
        self.assertTrue(r.is_error)
        self.assertIn("Invalid arguments", r.text)

    def test_cap(self):
        self.assertIn("[truncated 5 bytes]", runner._cap("x" * 15, 10))


class ServerTests(unittest.TestCase):
    """Starts the real server as a subprocess and talks JSON-RPC over stdio."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp)
        self.p = subprocess.Popen(
            [sys.executable, MAIN, "--project", self.tmp, "--root", FIXTURES, "--root", self.tmp,
             "serve", "--poll", "0.2"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        self.addCleanup(self._close)
        self.n = 0

    def _close(self):
        self.p.stdin.close()
        self.p.wait(timeout=5)
        self.p.stdout.close()

    def rpc(self, method, params=None):
        self.n += 1
        self.p.stdin.write((json.dumps({"jsonrpc": "2.0", "id": self.n, "method": method,
                                        "params": params or {}}) + "\n").encode())
        self.p.stdin.flush()
        while True:
            msg = json.loads(self.p.stdout.readline())
            if msg.get("id") == self.n:
                return msg

    def test_protocol_and_dynamic_list(self):
        init = self.rpc("initialize", {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "t"}})
        self.assertEqual(init["result"]["protocolVersion"], "2025-06-18")
        self.assertTrue(init["result"]["capabilities"]["tools"]["listChanged"])

        names = [t["name"] for t in self.rpc("tools/list")["result"]["tools"]]
        self.assertEqual(names, ["echo_args", "echo_fail", "echo_sleep"])

        call = self.rpc("tools/call", {"name": "echo_args", "arguments": {"word": "w"}})["result"]
        self.assertFalse(call["isError"])
        self.assertEqual(call["structuredContent"]["argv"], ["show", "w", "--n=1"])

        bad = self.rpc("tools/call", {"name": "echo_args", "arguments": {}})["result"]
        self.assertTrue(bad["isError"])
        self.assertEqual(self.rpc("nope")["error"]["code"], -32601)

        write_tool(self.tmp, "added", GOOD.format(name="added_tool"))
        deadline = time.time() + 5
        while time.time() < deadline:
            msg = json.loads(self.p.stdout.readline())
            if msg.get("method") == "notifications/tools/list_changed":
                break
        else:
            self.fail("no list_changed notification")
        names = [t["name"] for t in self.rpc("tools/list")["result"]["tools"]]
        self.assertIn("added_tool", names)
        call = self.rpc("tools/call", {"name": "added_tool", "arguments": {}})["result"]
        self.assertEqual(call["content"][0]["text"].strip(), "hi")


if __name__ == "__main__":
    unittest.main()
