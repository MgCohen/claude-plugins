"""Command line: get, query, pointers, check, schema, snippets."""
import argparse
import json
import os
import sys

from . import config as cfgmod
from . import snippets
from .builder import Builder, _sort_key
from .client import Client, NotionError
from .props import flatten, title_of
from .render import to_json, to_markdown


def main(argv=None):
    p = build_parser()
    a = p.parse_args(argv)
    return _run(a)


def build_parser():
    p = argparse.ArgumentParser(prog="notion-context", description="Deterministic Notion context for agents.")
    p.add_argument("--config", help="top config layer; it overrides the plugin default, ~/.claude, project, ./ and $NOTION_CONTEXT_CONFIG layers")
    p.add_argument("--no-defaults", action="store_true", help="do not load the plugin default and the ~/.claude layers")
    p.add_argument("--stats", action="store_true", help="print the API call count to stderr")
    sub = p.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("get", help="one page by key (ISS-12), rendered with a document recipe")
    g.add_argument("key")
    g.add_argument("--doc", help="document recipe (default: the database's document)")
    g.add_argument("--database", help="database alias, for keys with no prefix")
    _output_args(g)

    q = sub.add_parser("query", help="rows of one database")
    q.add_argument("database", help="database alias")
    q.add_argument("--where", action="append", default=[], metavar="PROP=VALUE",
                   help="filter; repeat for AND; prefix the value with ! to negate")
    q.add_argument("--columns", help="comma-separated properties")
    _output_args(q)

    o = sub.add_parser("pointers", help="resolve names to Notion ids (all names if none are given)")
    o.add_argument("names", nargs="*")
    o.add_argument("--format", choices=("md", "json"), default="md")

    sub.add_parser("check", help="compare the config with the live schemas")

    s = sub.add_parser("schema", help="list the properties of a database")
    s.add_argument("database", help="database alias or id")

    n = sub.add_parser("snippets", help="write code from this git repo into the Snippets database code blocks")
    n.add_argument("mode", nargs="?", choices=("plan", "apply", "force"), default="plan")
    n.add_argument("--database", default=os.environ.get("NOTION_SNIPPETS_DATABASE"),
                   help="Snippets database id (default: $NOTION_SNIPPETS_DATABASE, then the config pointer 'snippets')")
    return p


def _run(a):
    if a.cmd == "snippets":
        return _snippets(a)
    try:
        cfg = cfgmod.load(a.config, defaults=not a.no_defaults)
        if a.cmd == "pointers":
            _write(_pointers(a, cfg), None)
            return 0
        client = Client()
        out = {"get": _get, "query": _query, "check": _check, "schema": _schema}[a.cmd](a, cfg, client)
    except (cfgmod.ConfigError, LookupError, ValueError, NotionError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    if out is not None:
        _write(out, getattr(a, "out", None))
    if a.stats:
        print(f"api_calls={client.calls}", file=sys.stderr)
    return 0 if not (a.cmd == "check" and out and "ERROR" in out) else 1


def _snippets(a):
    if not a.database:
        try:
            a.database = cfgmod.load(a.config, defaults=not a.no_defaults).pointer("snippets")
        except cfgmod.ConfigError:
            pass
    if not a.database:
        print("error: set NOTION_SNIPPETS_DATABASE, --database or the config pointer 'snippets'", file=sys.stderr)
        return 2
    client = Client()
    try:
        summary, code = snippets.run(client, a.database, a.mode)
    except (ValueError, NotionError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    sys.stdout.write(summary)
    return code


def _output_args(sp):
    sp.add_argument("--format", choices=("md", "json"), default="md")
    sp.add_argument("--out", help="write to this file instead of stdout")


def _write(text, path):
    if path:
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
    else:
        sys.stdout.write(text)


def _get(a, cfg, client):
    node = Builder(client, cfg).get(a.key, a.doc, a.database)
    return to_json(node) if a.format == "json" else to_markdown(node)


def _pointers(a, cfg):
    names = a.names or cfg.pointer_names()
    rows = {n: {"id": cfg.pointer(n), "layer": cfg.pointer_layer(n)}
            for n in names}
    if a.format == "json":
        return json.dumps({n: r["id"] for n, r in rows.items()}, indent=2) + "\n"
    lines = ["| Name | Id | Layer |", "|---|---|---|"]
    lines += [f"| {n} | {r['id']} | {r['layer']} |" for n, r in rows.items()]
    return "\n".join(lines) + "\n"


def _query(a, cfg, client):
    b = Builder(client, cfg)
    db = cfg.db(a.database)
    f = b.filters(db, a.where)
    rows = client.query(db.id, {"and": f} if len(f) > 1 else (f[0] if f else None))
    cols = [c.strip() for c in a.columns.split(",")] if a.columns else None
    items = [{"key": b._key(db, r), "title": title_of(r), "url": r.get("url"),
              "fields": flatten(r, include=set(cols) if cols else None)} for r in rows]
    items.sort(key=lambda i: _sort_key(i["key"] if i["key"] is not None else i["title"]))
    if a.format == "json":
        return to_json(items)
    node = {"title": db.alias, "fields": {}, "sections": [
        {"title": "Rows", "style": "table", "columns": cols or [], "items": items}]}
    return to_markdown(node)


def _schema(a, cfg, client):
    try:
        db_id = cfg.db(a.database).id
    except cfgmod.ConfigError:
        db_id = a.database
    props = client.database(db_id)["properties"]
    lines = [f"{n}\t{p['type']}" + _schema_extra(p) for n, p in sorted(props.items())]
    return "\n".join(lines) + "\n"


def _schema_extra(p):
    t = p["type"]
    if t in ("select", "multi_select", "status"):
        return "\t" + ", ".join(o["name"] for o in p[t]["options"])
    if t == "relation":
        return "\t-> " + p["relation"]["database_id"]
    if t == "unique_id":
        return f"\tprefix={p['unique_id'].get('prefix')}"
    return ""


def _check(a, cfg, client):
    """Report each problem as ERROR; return the report."""
    out, schemas = [f"layer {p}" for p in cfg.layers], {}
    for name, pid in sorted(cfg.pointers.items()):
        try:
            client.page(pid)
            out.append(f"ok    pointer {name}")
        except NotionError:
            try:
                client.database(pid)
                out.append(f"ok    pointer {name}")
            except NotionError as e:
                out.append(f"ERROR pointer {name}: {e} (is the page shared with the integration?)")
    for db in cfg.databases.values():
        try:
            schemas[db.alias] = client.database(db.id)["properties"]
            out.append(f"ok    database {db.alias}")
        except NotionError as e:
            out.append(f"ERROR database {db.alias}: {e} (is the database shared with the integration?)")
            continue
        if db.key:
            t = schemas[db.alias].get(db.key, {}).get("type")
            if t != "unique_id":
                out.append(f"ERROR database {db.alias}: key {db.key!r} is {t or 'missing'}, not unique_id")
    for doc in cfg.documents.values():
        root = schemas.get(doc.database)
        if root is None:
            continue
        for f in doc.fields:
            if f != "*" and f not in root:
                out.append(f"ERROR document {doc.name}: no field {f!r} in {doc.database}")
        for s in doc.sections:
            target = schemas.get(s.database)
            if target is None:
                continue
            if s.backlink and target.get(s.backlink, {}).get("type") != "relation":
                out.append(f"ERROR document {doc.name}/{s.title}: {s.database}.{s.backlink} is not a relation")
            if s.relation and root.get(s.relation, {}).get("type") != "relation":
                out.append(f"ERROR document {doc.name}/{s.title}: {doc.database}.{s.relation} is not a relation")
            for c in s.columns:
                if c not in target:
                    out.append(f"ERROR document {doc.name}/{s.title}: no column {c!r} in {s.database}")
            for e in s.filter:
                if e.partition("=")[0] not in target:
                    out.append(f"ERROR document {doc.name}/{s.title}: filter on unknown property {e!r}")
        if not any(l.startswith(f"ERROR document {doc.name}") for l in out):
            out.append(f"ok    document {doc.name}")
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    sys.exit(main())
