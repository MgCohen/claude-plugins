"""In-memory stand-in for notion_context.client.Client. No network."""
from notion_context.client import NotionError


def rt(text, **annotations):
    return [{"type": "text", "plain_text": text, "href": None, "annotations": annotations}]


def title(text):
    return {"type": "title", "title": rt(text)}


def text(s):
    return {"type": "rich_text", "rich_text": rt(s)}


def select(name):
    return {"type": "select", "select": {"name": name} if name else None}


def key(prefix, n):
    return {"type": "unique_id", "unique_id": {"prefix": prefix, "number": n}}


def rel(*ids):
    return {"id": "r", "type": "relation", "relation": [{"id": i} for i in ids], "has_more": False}


def checkbox(v):
    return {"type": "checkbox", "checkbox": v}


def block(t, s="", children=None, **extra):
    d = {"rich_text": rt(s)} if t not in ("divider", "child_database", "table", "table_row") else {}
    d.update(extra)
    return {"id": f"b-{id(d)}", "type": t, t: d, "has_children": bool(children), "_children": children or []}


class FakeClient:
    def __init__(self):
        self.calls = 0
        self.schemas = {}   # db id -> properties schema
        self.rows = {}      # db id -> [page]
        self.bodies = {}    # page/block id -> [block]
        self.linked = set() # block ids that are linked views

    def add_db(self, db_id, schema):
        self.schemas[db_id] = schema
        self.rows[db_id] = []

    def add_page(self, db_id, page_id, props, body=None):
        page = {"id": page_id, "url": f"https://notion.test/{page_id}", "properties": props}
        self.rows[db_id].append(page)
        self.bodies[page_id] = body or []
        return page

    # --- Client API ---
    def database(self, db_id):
        self.calls += 1
        if db_id in self.linked:
            raise NotionError(400, "validation_error", f"Database with ID {db_id} is a linked database.")
        if db_id not in self.schemas:
            raise NotionError(404, "object_not_found", db_id)
        return {"properties": self.schemas[db_id]}

    def query(self, db_id, filter=None, sorts=None):
        self.calls += 1
        return [p for p in self.rows[db_id] if _match(p, filter)]

    def page(self, page_id):
        self.calls += 1
        for rows in self.rows.values():
            for p in rows:
                if p["id"] == page_id:
                    return p
        raise NotionError(404, "object_not_found", page_id)

    def children(self, block_id):
        self.calls += 1
        if block_id in self.bodies:
            return self.bodies[block_id]
        for blocks in self.bodies.values():
            found = _find(blocks, block_id)
            if found is not None:
                return found["_children"]
        return []


def _find(blocks, block_id):
    for b in blocks:
        if b["id"] == block_id:
            return b
        f = _find(b["_children"], block_id)
        if f is not None:
            return f
    return None


def _match(page, f):
    if not f:
        return True
    if "and" in f:
        return all(_match(page, x) for x in f["and"])
    prop = page["properties"].get(f["property"])
    if prop is None:
        return False
    (kind, cond), = [(k, v) for k, v in f.items() if k != "property"]
    (op, val), = cond.items()
    t = prop["type"]
    if t == "relation":
        have = [r["id"] for r in prop["relation"]]
    elif t == "unique_id":
        have = prop["unique_id"]["number"]
    elif t in ("select", "status"):
        have = (prop[t] or {}).get("name")
    elif t == "multi_select":
        have = [o["name"] for o in prop[t]]
    elif t == "checkbox":
        have = prop["checkbox"]
    else:
        have = "".join(x["plain_text"] for x in prop.get(t, []))
    ops = {"equals": lambda: have == val, "does_not_equal": lambda: have != val,
           "contains": lambda: val in have, "does_not_contain": lambda: val not in have}
    return ops[op]()
