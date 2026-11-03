"""Minimal Notion REST client: auth, retries, pagination, schema cache."""
import json
import os
import time
import urllib.error
import urllib.request

API = "https://api.notion.com/v1"
VERSION = "2022-06-28"


class NotionError(Exception):
    def __init__(self, status, code, message):
        super().__init__(f"{status} {code}: {message}")
        self.status, self.code = status, code


class Client:
    """Thin wrapper over the REST API. Counts calls for --stats."""

    def __init__(self, token=None, max_retries=5, sleep=time.sleep):
        self.token = token or os.environ.get("NOTION_TOKEN")
        if not self.token:
            raise SystemExit("NOTION_TOKEN is not set.")
        self.max_retries = max_retries
        self.sleep = sleep
        self.calls = 0
        self._schemas = {}

    def request(self, method, path, body=None):
        data = json.dumps(body).encode() if body is not None else None
        for attempt in range(self.max_retries + 1):
            self.calls += 1
            req = urllib.request.Request(API + path, data=data, method=method, headers={
                "Authorization": f"Bearer {self.token}",
                "Notion-Version": VERSION,
                "Content-Type": "application/json",
            })
            try:
                with urllib.request.urlopen(req, timeout=60) as r:
                    return json.load(r)
            except urllib.error.HTTPError as e:
                retryable = e.code == 429 or e.code >= 500
                if retryable and attempt < self.max_retries:
                    wait = float(e.headers.get("Retry-After") or 2 ** attempt)
                    self.sleep(wait)
                    continue
                try:
                    err = json.load(e)
                except Exception:
                    err = {}
                raise NotionError(e.code, err.get("code", "http_error"), err.get("message", str(e))) from None
            except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
                if attempt < self.max_retries:
                    self.sleep(2 ** attempt)
                    continue
                reason = getattr(e, "reason", e)
                raise NotionError(0, "network_error", f"{reason} (after {attempt + 1} tries)") from None

    def _paginate(self, method, path, body=None):
        cursor = None
        while True:
            if method == "GET":
                sep = "&" if "?" in path else "?"
                p = f"{path}{sep}page_size=100" + (f"&start_cursor={cursor}" if cursor else "")
                res = self.request("GET", p)
            else:
                b = dict(body or {}, page_size=100)
                if cursor:
                    b["start_cursor"] = cursor
                res = self.request("POST", path, b)
            yield from res["results"]
            if not res.get("has_more"):
                return
            cursor = res["next_cursor"]

    def query(self, database_id, filter=None, sorts=None):
        body = {}
        if filter:
            body["filter"] = filter
        if sorts:
            body["sorts"] = sorts
        return list(self._paginate("POST", f"/databases/{database_id}/query", body))

    def page(self, page_id):
        return self.request("GET", f"/pages/{page_id}")

    def children(self, block_id):
        return list(self._paginate("GET", f"/blocks/{block_id}/children"))

    def database(self, database_id):
        """Database object (schema). Cached for the run."""
        if database_id not in self._schemas:
            self._schemas[database_id] = self.request("GET", f"/databases/{database_id}")
        return self._schemas[database_id]
