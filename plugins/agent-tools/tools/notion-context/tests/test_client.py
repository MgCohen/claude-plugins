import io
import json
import unittest
import urllib.error
from unittest import mock

from notion_context.client import Client, NotionError


def http_error(code, body, headers=None):
    return urllib.error.HTTPError("u", code, "x", headers or {}, io.BytesIO(json.dumps(body).encode()))


class Ok(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class ClientTests(unittest.TestCase):
    def test_retries_429_with_retry_after(self):
        waits = []
        c = Client(token="t", sleep=waits.append)
        responses = [http_error(429, {}, {"Retry-After": "1.5"}), Ok(b'{"ok": true}')]
        with mock.patch("urllib.request.urlopen", side_effect=responses):
            self.assertEqual(c.request("GET", "/x"), {"ok": True})
        self.assertEqual(waits, [1.5])
        self.assertEqual(c.calls, 2)

    def test_client_errors_are_not_retried(self):
        c = Client(token="t", sleep=lambda s: self.fail("no retry expected"))
        err = http_error(400, {"code": "validation_error", "message": "bad"})
        with mock.patch("urllib.request.urlopen", side_effect=[err]):
            with self.assertRaisesRegex(NotionError, "400 validation_error: bad"):
                c.request("GET", "/x")

    def test_network_errors_are_retried_then_reported(self):
        waits = []
        c = Client(token="t", sleep=waits.append, max_retries=2)
        errs = [urllib.error.URLError("no route")] * 3
        with mock.patch("urllib.request.urlopen", side_effect=errs):
            with self.assertRaisesRegex(NotionError, "network_error: no route"):
                c.request("GET", "/x")
        self.assertEqual(waits, [1, 2])

    def test_pagination_follows_cursor(self):
        c = Client(token="t")
        pages = [{"results": [1], "has_more": True, "next_cursor": "c2"}, {"results": [2], "has_more": False}]
        with mock.patch.object(c, "request", side_effect=pages) as req:
            self.assertEqual(c.query("db"), [1, 2])
        self.assertEqual(req.call_args_list[1].args[2]["start_cursor"], "c2")


if __name__ == "__main__":
    unittest.main()
