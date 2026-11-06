import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import textwrap
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from agent_tools import argv as argvmod  # noqa: E402
from agent_tools import manifest as mf  # noqa: E402
from agent_tools import runner  # noqa: E402
from agent_tools import secrets  # noqa: E402

FIXTURES = os.path.join(HERE, "fixtures")
MAIN = os.path.join(os.path.dirname(HERE), "main.py")
NO_PLUGIN = os.path.join(FIXTURES, "no-plugin")  # has no tools/ folder: the real plugin tools stay out of the tests
# An empty Claude config folder: the installed plugins and ~/.claude/agent-tools.toml of this
# machine stay out of the tests. The server subprocesses inherit it.
os.environ["CLAUDE_CONFIG_DIR"] = tempfile.mkdtemp(prefix="agent-tools-claude-")
# No secrets.env: the tests never read 1Password. SecretsTests sets its own file.
os.environ["AGENT_TOOLS_SECRETS_ENV"] = ""


def rmtree(path):
    """shutil.rmtree that also deletes read-only files (git objects on Windows)."""
    def retry(func, p, _):
        os.chmod(p, stat.S_IWRITE)
        func(p)
    if sys.version_info >= (3, 12):
        shutil.rmtree(path, onexc=retry)
    else:
        shutil.rmtree(path, onerror=retry)


def write_file(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(textwrap.dedent(text))


def write_plugin(folder, name, mtime=None):
    path = os.path.join(folder, ".claude-plugin", "plugin.json")
    write_file(path, json.dumps({"name": name}))
    if mtime is not None:
        os.utime(path, (mtime, mtime))


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
        self.addCleanup(rmtree, self.tmp)

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
        claude, proj = os.path.join(self.tmp, "claude"), os.path.join(self.tmp, "proj")
        write_plugin(os.path.join(claude, "plugins", "cache", "mkt", "notes", "1.0"), "notes")
        write_file(os.path.join(proj, ".claude", "agent-tools.toml"), 'paths = ["../shared"]\n')
        write_file(os.path.join(claude, "agent-tools.toml"), 'paths = ["mine"]\n')
        env = {"CLAUDE_CONFIG_DIR": claude, "AGENT_TOOLS_PATH": os.pathsep.join(["/x", "/y"])}
        with mock.patch.dict(os.environ, env):
            errors = []
            roots = mf.search_roots("/plugin", proj, errors=errors)
        self.assertEqual(errors, [])
        self.assertEqual(roots, [os.path.abspath(p) for p in (
            "/plugin/tools", proj, os.path.join(proj, ".claude", "..", "shared"),
            os.path.join(claude, "mine"), "/x", "/y",
            os.path.join(claude, "plugins", "cache", "mkt", "notes", "1.0"))])

    def test_installed_plugins_newest_copy_and_skip(self):
        home = os.path.join(self.tmp, "plugins")
        write_plugin(os.path.join(home, "cache", "mkt", "notes", "1.0"), "notes", mtime=100)
        write_plugin(os.path.join(home, "cache", "mkt", "notes", "2.0"), "notes", mtime=200)
        write_plugin(os.path.join(home, "synced", "acct", "notes"), "notes", mtime=300)
        write_plugin(os.path.join(home, "synced", "acct", "notes~g2"), "notes", mtime=400)
        write_plugin(os.path.join(home, "synced", "acct", ".staging", "notes"), "notes", mtime=500)
        write_plugin(os.path.join(home, "synced", "acct", "agent-tools~g3"), "agent-tools")
        me = os.path.join(self.tmp, "me")
        write_plugin(me, "agent-tools")
        found = mf.installed_plugins(home, skip=me)
        self.assertEqual(found, [os.path.join(home, "cache", "mkt", "notes", "2.0"),
                                 os.path.join(home, "synced", "acct", "notes~g2")])

    def test_installed_plugins_next_to_this_plugin(self):
        # The desktop app keeps the account plugins in its own folder, one folder per plugin id.
        home, store = os.path.join(self.tmp, "plugins"), os.path.join(self.tmp, "rpm", "acct")
        me = os.path.join(store, "plugin_01")
        write_plugin(me, "agent-tools")
        write_plugin(os.path.join(store, "plugin_02"), "notes")
        write_plugin(os.path.join(store, "plugin_03"), "todo", mtime=100)
        write_plugin(os.path.join(store, "plugin_04"), "todo", mtime=200)
        write_plugin(os.path.join(store, ".tmp_05"), "staged")
        os.makedirs(os.path.join(store, "not-a-plugin"))
        write_plugin(os.path.join(home, "synced", "acct", "notes"), "notes")  # also in the store
        write_plugin(os.path.join(home, "synced", "acct", "other"), "other")
        found = mf.installed_plugins(home, skip=me)
        self.assertEqual(found, [os.path.join(home, "synced", "acct", "other"),
                                 os.path.join(store, "plugin_02"), os.path.join(store, "plugin_04")])

    def test_config_errors_and_plugins_false(self):
        claude, proj = os.path.join(self.tmp, "claude"), os.path.join(self.tmp, "proj")
        write_plugin(os.path.join(claude, "plugins", "cache", "mkt", "notes", "1.0"), "notes")
        write_file(os.path.join(proj, ".claude", "agent-tools.toml"), "plugins = false\n")
        write_file(os.path.join(claude, "agent-tools.toml"), 'paths = "one"\ncolour = 1\n')
        with mock.patch.dict(os.environ, {"CLAUDE_CONFIG_DIR": claude, "AGENT_TOOLS_PATH": ""}):
            errors = []
            roots = mf.search_roots(None, proj, errors=errors)
        self.assertEqual(roots, [os.path.abspath(proj)])  # no plugins: the project set false
        text = "\n".join(errors)
        self.assertIn("unknown keys ['colour']", text)
        self.assertIn("paths must be a list", text)

    def test_walk_finds_nested_manifests_and_skips_excluded(self):
        write_tool(self.tmp, "a/b/c", GOOD.format(name="deep_tool"))
        write_tool(self.tmp, "node_modules/x", GOOD.format(name="npm_tool"))
        write_tool(self.tmp, ".hidden", GOOD.format(name="hidden_tool"))
        write_tool(self.tmp, "src/fixtures/t", GOOD.format(name="fixture_tool"))
        write_tool(self.tmp, "custom", GOOD.format(name="custom_tool"))
        with mock.patch.dict(os.environ, {"AGENT_TOOLS_EXCLUDE": "custom"}):
            tools, errors = mf.load_all([self.tmp])
        self.assertEqual((list(tools), errors), (["deep_tool"], []))

    def test_git_scan_obeys_gitignore_and_sees_new_files(self):
        run = lambda *a: subprocess.run(["git", "-C", self.tmp, *a], check=True, capture_output=True)
        run("init", "-q")
        write_tool(self.tmp, "tracked", GOOD.format(name="tracked_tool"))
        write_tool(self.tmp, "ignored", GOOD.format(name="ignored_tool"))
        with open(os.path.join(self.tmp, ".gitignore"), "w") as f:
            f.write("ignored/\n")
        run("add", "tracked", ".gitignore")
        write_tool(self.tmp, "deep/new", GOOD.format(name="new_tool"))  # not committed
        self.assertIsNotNone(mf._git_manifests(self.tmp))
        tools, _ = mf.load_all([self.tmp])
        self.assertEqual(sorted(tools), ["new_tool", "tracked_tool"])

    def test_wrong_types_are_reported_not_fatal(self):
        base = GOOD.format(name="t_tool")
        cases = {
            "timeout": base + 'timeout = "abc"\n',
            "desc": base.replace('description = "A tool for tests. Returns a short text."', "description = 5"),
            "env": base + 'env = "FOO"\n',
            "input": base + 'input = "x"\n',
            "star": base.replace("args = []", 'args = ["{w*}"]') + '[tool.input]\nw = { type = "string", description = "d" }\n',
            "flag": base.replace("args = []", 'args = ["{w|--w}"]') + '[tool.input]\nw = { type = "string", description = "d" }\n',
            "plain": base.replace("args = []", 'args = ["{w}"]') + '[tool.input]\nw = { type = "array", description = "d" }\n',
        }
        for folder, body in cases.items():
            write_tool(self.tmp, folder, body)
        tools, errors = mf.load_all([self.tmp])
        self.assertEqual(tools, {})
        self.assertEqual(len(errors), len(cases), errors)

    def test_reserved_prefix(self):
        write_tool(self.tmp, "r", GOOD.format(name="agent_tools_mine"))
        tools, errors = mf.load_all([self.tmp])
        self.assertEqual(tools, {})
        self.assertIn("reserved", errors[0])

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
        with self.assertRaisesRegex(ValueError, "must not start"):
            argvmod.build(["c"], ["{w*}"], {"w": ["ok", "--output=/etc/x"]})
        self.assertEqual(argvmod.build(["c"], ["--w={w*}"], {"w": ["-x"]}), ["c", "--w=-x"])

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

    def test_project_dir_is_passed(self):
        t = self.tools["echo_args"]
        env, _ = runner.environment(t, {"CLAUDE_PROJECT_DIR": "/proj"})
        self.assertEqual(env["CLAUDE_PROJECT_DIR"], "/proj")
        env, _ = runner.environment(t, {})
        self.assertEqual(env["CLAUDE_PROJECT_DIR"], os.getcwd())

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


class SecretsTests(unittest.TestCase):
    def setUp(self):
        self.tools = mf.load_all([FIXTURES], allow_write=True)[0]
        self.tmp = tempfile.mkdtemp(prefix="agent-tools-secrets-")
        self.file = os.path.join(self.tmp, "secrets.env")
        write_file(self.file, """
            # comment
            ECHO_SECRET=op://agent/ECHO_ITEM/credential
            PLAIN=not-a-reference
        """)
        self.reads = []
        secrets._cache.clear()
        self.addCleanup(secrets._cache.clear)
        self.addCleanup(rmtree, self.tmp)

    def fake_read(self, op, ref, env):
        self.reads.append((op, ref, env.get(secrets.TOKEN)))
        return "from-1password", None

    def start(self, token="tok", op="/bin/op", env=None):
        values = {"AGENT_TOOLS_SECRETS_ENV": self.file, **(env or {})}
        if token:
            values[secrets.TOKEN] = token
        patches = [mock.patch.dict(os.environ, values), mock.patch.object(secrets, "_read", self.fake_read),
                   mock.patch.object(secrets, "op_binary", lambda f=None: op),
                   mock.patch.object(secrets, "token", lambda source=None: token)]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)
        if "ECHO_SECRET" not in values:
            os.environ.pop("ECHO_SECRET", None)

    def run_echo(self):
        t = self.tools["echo_args"]
        t.env = ["ECHO_SECRET"]
        return runner.run(t, {"word": "x"})

    def test_references(self):
        self.assertEqual(secrets.references([self.file, os.path.join(self.tmp, "none.env")]),
                         {"ECHO_SECRET": ("op://agent/ECHO_ITEM/credential", self.file)})

    def test_missing_env_comes_from_1password_once(self):
        self.start()
        r = self.run_echo()
        self.assertFalse(r.is_error, r.text)
        self.assertEqual(r.data["secret"], "from-1password")
        self.run_echo()
        self.assertEqual(self.reads, [("/bin/op", "op://agent/ECHO_ITEM/credential", "tok")])  # cached

    def test_set_env_wins(self):
        self.start(env={"ECHO_SECRET": "local"})
        r = self.run_echo()
        self.assertEqual(r.data["secret"], "local")
        self.assertEqual(self.reads, [])

    def test_no_token_says_why(self):
        self.start(token=None)
        r = self.run_echo()
        self.assertTrue(r.is_error)
        self.assertIn("OP_SERVICE_ACCOUNT_TOKEN is not set", r.text)
        self.assertEqual(self.reads, [])

    def test_no_op_says_why(self):
        self.start(op=None)
        r = self.run_echo()
        self.assertTrue(r.is_error)
        self.assertIn("op (the 1Password CLI) is not installed", r.text)

    def test_name_without_reference_is_not_read(self):
        self.start()
        self.assertEqual(secrets.resolve(["OTHER", "PLAIN"]), ({}, None))
        self.assertEqual(self.reads, [])

    def test_core_plugin_file_is_the_default(self):
        root = os.path.join(self.tmp, "plugins", "core")
        write_plugin(root, "core")
        write_file(os.path.join(root, secrets.SECRETS_FILE), "A=op://agent/A/credential\n")
        with mock.patch.object(mf, "installed_plugins", lambda skip=None: [root]):
            self.assertEqual(secrets.env_files({}), [os.path.join(root, secrets.SECRETS_FILE)])
            self.assertEqual(secrets.env_files({"AGENT_TOOLS_SECRETS_ENV": ""}), [])


class ServerTests(unittest.TestCase):
    """Starts the real server as a subprocess and talks JSON-RPC over stdio."""

    def start(self, *extra):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(rmtree, self.tmp)
        self.p = subprocess.Popen(
            [sys.executable, MAIN, "--plugin-root", NO_PLUGIN, "--project", self.tmp, "--root", FIXTURES, "serve", *extra],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        self.addCleanup(self._close)
        self.n = 0
        init = self.rpc("initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                                       "clientInfo": {"name": "t"}})
        self.assertEqual(init["result"]["protocolVersion"], "2025-06-18")
        self.assertTrue(init["result"]["capabilities"]["tools"]["listChanged"])

    def _close(self):
        self.p.stdin.close()
        self.p.wait(timeout=5)
        self.p.stdout.close()

    def rpc(self, method, params=None):
        self.n += 1
        self.p.stdin.write((json.dumps({"jsonrpc": "2.0", "id": self.n, "method": method,
                                        "params": params or {}}) + "\n").encode())
        self.p.stdin.flush()
        self.notes = []
        while True:
            msg = json.loads(self.p.stdout.readline())
            if msg.get("id") == self.n:
                return msg
            self.notes.append(msg.get("method"))

    def names(self):
        return [t["name"] for t in self.rpc("tools/list")["result"]["tools"]]

    def test_refresh_reads_project_config_again(self):
        self.start()
        shared = tempfile.mkdtemp()  # outside the project: only the config can add it
        self.addCleanup(rmtree, shared)
        write_tool(shared, "t", GOOD.format(name="shared_tool"))
        self.rpc("tools/call", {"name": "agent_tools_refresh"})
        self.assertNotIn("shared_tool", self.names())
        write_file(os.path.join(self.tmp, ".claude", "agent-tools.toml"),
                   f"paths = [{json.dumps(shared)}]\n")
        self.rpc("tools/call", {"name": "agent_tools_refresh"})
        self.assertIn("shared_tool", self.names())

    def test_protocol(self):
        self.start()
        self.assertEqual(self.names(), ["agent_tools_refresh", "echo_args", "echo_fail", "echo_sleep"])
        call = self.rpc("tools/call", {"name": "echo_args", "arguments": {"word": "w"}})["result"]
        self.assertFalse(call["isError"])
        self.assertEqual(call["structuredContent"]["argv"], ["show", "w", "--n=1"])
        self.assertTrue(self.rpc("tools/call", {"name": "echo_args", "arguments": {}})["result"]["isError"])
        self.assertEqual(self.rpc("nope")["error"]["code"], -32601)
        for bad in (b"5\n", b"[1]\n"):  # not an object: error, and the server keeps running
            self.p.stdin.write(bad)
            self.p.stdin.flush()
            self.assertEqual(json.loads(self.p.stdout.readline())["error"]["code"], -32600)
        self.assertEqual(self.rpc("ping")["result"], {})

    def test_scan_at_start_and_refresh_on_demand(self):
        self.start()
        write_tool(self.tmp, "tools/added", GOOD.format(name="added_tool"))
        self.assertNotIn("added_tool", self.names())  # the list is fixed until a refresh
        unknown = self.rpc("tools/call", {"name": "added_tool"})["result"]
        self.assertIn("agent_tools_refresh", unknown["content"][0]["text"])
        r = self.rpc("tools/call", {"name": "agent_tools_refresh"})["result"]
        self.assertIn("Added: added_tool", r["content"][0]["text"])
        self.assertIn("notifications/tools/list_changed", self.notes)
        self.assertIn("added_tool", self.names())
        call = self.rpc("tools/call", {"name": "added_tool", "arguments": {}})["result"]
        self.assertEqual(call["content"][0]["text"].strip(), "hi")
        again = self.rpc("tools/call", {"name": "agent_tools_refresh"})["result"]
        self.assertIn("No change.", again["content"][0]["text"])
        self.assertNotIn("notifications/tools/list_changed", self.notes)



class CatalogTests(unittest.TestCase):
    def catalog(self, project):
        return subprocess.run([sys.executable, MAIN, "--plugin-root", NO_PLUGIN, "--project", project, "catalog"],
                              capture_output=True, text=True, timeout=30)

    def test_lists_first_sentences(self):
        tmp = tempfile.mkdtemp()
        self.addCleanup(rmtree, tmp)
        write_tool(tmp, "t", GOOD.format(name="cat_tool"))
        r = self.catalog(tmp)
        self.assertEqual(r.returncode, 0)
        self.assertIn("- cat_tool: A tool for tests.", r.stdout)
        self.assertNotIn("Returns a short text", r.stdout)

    def test_silent_when_no_tools(self):
        tmp = tempfile.mkdtemp()
        self.addCleanup(rmtree, tmp)
        self.assertEqual(self.catalog(tmp).stdout, "")


if __name__ == "__main__":
    unittest.main()
