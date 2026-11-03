"""Build a document tree from Notion, following the config recipe.

The tree is plain data (dicts and lists). Renderers turn it into Markdown or JSON.
"""
from .blocks import BodyReader
from .config import ConfigError
from .props import filter_for, flatten, parse_key, title_of


class Builder:
    def __init__(self, client, config):
        self.client = client
        self.cfg = config
        self.body = BodyReader(client, databases=config.child_databases)
        self._prefixes = None

    # ---- lookups ---------------------------------------------------------

    def schema(self, db):
        return self.client.database(db.id)["properties"]

    def prefix_map(self):
        """Key prefix -> database, from config or from the unique_id schema."""
        if self._prefixes is None:
            self._prefixes = {}
            for db in self.cfg.databases.values():
                if not db.key:
                    continue
                prefix = db.prefix
                if prefix is None:
                    prop = self.schema(db).get(db.key, {})
                    prefix = (prop.get("unique_id") or {}).get("prefix")
                if prefix:
                    self._prefixes[prefix.upper()] = db
        return self._prefixes

    def find(self, key, database=None):
        """'ISS-12' -> (database, page)."""
        prefix, number = parse_key(key)
        if database:
            db = self.cfg.db(database)
        else:
            if not prefix:
                raise ConfigError(f"{key!r} has no prefix. Use --database.")
            db = self.prefix_map().get(prefix.upper())
            if not db:
                raise ConfigError(f"No database has key prefix {prefix!r}.")
        if not db.key:
            raise ConfigError(f"databases.{db.alias} has no 'key' property.")
        hits = self.client.query(db.id, {"property": db.key, "unique_id": {"equals": number}})
        if not hits:
            raise LookupError(f"{key} not found in {db.alias}.")
        return db, hits[0]

    def filters(self, db, exprs):
        props = self.schema(db)
        out = []
        for e in exprs:
            name, sep, raw = e.partition("=")
            if not sep:
                raise ConfigError(f"Filter {e!r} must be Property=value.")
            if name not in props:
                raise ConfigError(f"{db.alias} has no property {name!r}.")
            out.append(filter_for(name, props[name]["type"], raw))
        return out

    # ---- build -----------------------------------------------------------

    def get(self, key, document=None, database=None):
        db, page = self.find(key, database)
        name = document or db.document
        if not name:
            raise ConfigError(f"No document for {db.alias}. Use --doc or set databases.{db.alias}.document.")
        return self.build(page, self.cfg.document(name), depth=0, seen=set())

    def build(self, page, doc, depth, seen):
        seen = seen | {page["id"]}
        db = self.cfg.db(doc.database)
        node = {
            "key": self._key(db, page),
            "title": title_of(page),
            "url": page.get("url"),
            "document": doc.name,
            "fields": self._fields(page, doc.fields),
        }
        if doc.body:
            node["body"] = self.body.markdown(page["id"])
        node["sections"] = [self._section(page, s, depth, seen) for s in doc.sections]
        return node

    def _section(self, root, sec, depth, seen):
        db = self.cfg.db(sec.database)
        pages = self._related(root, sec, db)
        pages.sort(key=lambda p: _sort_key(flatten(p).get(sec.sort or db.key or "", "")))
        out = {"title": sec.title, "style": sec.style, "columns": sec.columns, "items": []}
        for p in pages:
            if sec.style == "full" and depth < self.cfg.max_depth and p["id"] not in seen:
                out["items"].append(self.build(p, self.cfg.document(sec.document), depth + 1, seen))
            else:
                row = flatten(p, include=set(sec.columns) if sec.columns else None)
                out["items"].append({"key": self._key(db, p), "title": title_of(p),
                                     "url": p.get("url"), "fields": row})
        return out

    def _related(self, root, sec, db):
        extra = self.filters(db, sec.filter)
        if sec.backlink:
            f = [{"property": sec.backlink, "relation": {"contains": root["id"]}}] + extra
            return self.client.query(db.id, {"and": f} if len(f) > 1 else f[0])
        prop = root["properties"].get(sec.relation)
        if not prop or prop["type"] != "relation":
            raise ConfigError(f"Root page has no relation property {sec.relation!r}.")
        ids = [r["id"] for r in prop["relation"]]
        if prop.get("has_more"):  # page objects list at most 25 relations
            ids = [r["id"] for r in self._all_relations(root["id"], prop["id"])]
        pages = [self.client.page(i) for i in ids]
        if extra:  # forward relations: apply filters with one query, then intersect
            keep = {p["id"] for p in self.client.query(db.id, {"and": extra} if len(extra) > 1 else extra[0])}
            pages = [p for p in pages if p["id"] in keep]
        return pages

    def _all_relations(self, page_id, prop_id):
        return [r["relation"] for r in self.client._paginate("GET", f"/pages/{page_id}/properties/{prop_id}")]

    def _fields(self, page, names):
        flat = flatten(page)
        flat.pop("id", None)
        if names == ["*"]:
            return flat
        return {n: flat[n] for n in names if n in flat}

    def _key(self, db, page):
        if db.key:
            prop = page["properties"].get(db.key)
            if prop:
                return flatten({"properties": {db.key: prop}, "id": ""}).get(db.key)
        return None


def _sort_key(v):
    if isinstance(v, str):
        pre, _, num = v.rpartition("-")
        if num.isdigit():
            return (0, pre, int(num), "")
        return (1, "", 0, v)
    if isinstance(v, (int, float)):
        return (0, "", v, "")
    return (2, "", 0, str(v))
