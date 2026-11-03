"""Load and validate the TOML config.

databases: one entry for each Notion database (alias -> id, key property).
documents: one recipe for each output type (which fields, body, related sections).
"""
import os
import tomllib
from dataclasses import dataclass, field

SECTION_STYLES = ("table", "list", "full")
CHILD_DB_MODES = ("skip", "link", "rows")


class ConfigError(Exception):
    pass


@dataclass
class Database:
    alias: str
    id: str
    key: str | None = None        # unique_id property, for lookups such as ISS-12
    prefix: str | None = None     # key prefix; read from the schema when not set
    document: str | None = None   # default document for this database


@dataclass
class Section:
    title: str
    database: str
    backlink: str | None = None   # relation property on the section database -> root page
    relation: str | None = None   # relation property on the root page -> section pages
    columns: list = field(default_factory=list)
    filter: list = field(default_factory=list)  # ["Status=!Done", ...]
    sort: str | None = None
    style: str = "table"
    document: str | None = None   # with style "full": render each item with this document


@dataclass
class Document:
    name: str
    database: str
    fields: list = field(default_factory=list)   # ["*"] for all
    body: bool = True
    sections: list = field(default_factory=list)


@dataclass
class Config:
    databases: dict
    documents: dict
    child_databases: str = "link"
    max_depth: int = 3
    path: str = ""

    def db(self, name_or_id):
        if name_or_id in self.databases:
            return self.databases[name_or_id]
        norm = name_or_id.replace("-", "")
        for d in self.databases.values():
            if d.id.replace("-", "") == norm:
                return d
        raise ConfigError(f"Unknown database {name_or_id!r}. Known: {', '.join(self.databases)}")

    def document(self, name):
        if name not in self.documents:
            raise ConfigError(f"Unknown document {name!r}. Known: {', '.join(self.documents)}")
        return self.documents[name]


def find_path(explicit=None):
    project = os.environ.get("CLAUDE_PROJECT_DIR")
    in_project = os.path.join(project, "notion-context.toml") if project else None
    for p in (explicit, os.environ.get("NOTION_CONTEXT_CONFIG"), "notion-context.toml", in_project):
        if p and os.path.exists(p):
            return p
    raise ConfigError("No config. Use --config, NOTION_CONTEXT_CONFIG, ./notion-context.toml "
                      "or $CLAUDE_PROJECT_DIR/notion-context.toml.")


def load(path):
    with open(path, "rb") as f:
        return parse(tomllib.load(f), path)


def parse(raw, path=""):
    s = raw.get("settings", {})
    dbs = {}
    for alias, d in raw.get("databases", {}).items():
        _keys(d, {"id", "key", "prefix", "document"}, f"databases.{alias}")
        if "id" not in d:
            raise ConfigError(f"databases.{alias}: 'id' is required.")
        dbs[alias] = Database(alias=alias, **d)
    docs = {}
    for name, d in raw.get("documents", {}).items():
        where = f"documents.{name}"
        _keys(d, {"database", "fields", "body", "sections"}, where)
        if "database" not in d:
            raise ConfigError(f"{where}: 'database' is required.")
        secs = []
        for i, sd in enumerate(d.get("sections", [])):
            w = f"{where}.sections[{i}]"
            _keys(sd, set(Section.__dataclass_fields__), w)
            sec = Section(**sd)
            if bool(sec.backlink) == bool(sec.relation):
                raise ConfigError(f"{w}: set exactly one of 'backlink' or 'relation'.")
            if sec.style not in SECTION_STYLES:
                raise ConfigError(f"{w}: style must be one of {SECTION_STYLES}.")
            if sec.document and sec.style != "full":
                sec.style = "full"
            secs.append(sec)
        docs[name] = Document(name=name, database=d["database"], fields=d.get("fields", []),
                              body=d.get("body", True), sections=secs)
    cfg = Config(dbs, docs, s.get("child_databases", "link"), s.get("max_depth", 3), path)
    _validate_refs(cfg)
    return cfg


def _keys(d, allowed, where):
    extra = set(d) - allowed
    if extra:
        raise ConfigError(f"{where}: unknown keys {sorted(extra)}.")


def _validate_refs(cfg):
    if cfg.child_databases not in CHILD_DB_MODES:
        raise ConfigError(f"settings.child_databases must be one of {CHILD_DB_MODES}.")
    for d in cfg.databases.values():
        if d.document and d.document not in cfg.documents:
            raise ConfigError(f"databases.{d.alias}: unknown document {d.document!r}.")
    for doc in cfg.documents.values():
        if doc.database not in cfg.databases:
            raise ConfigError(f"documents.{doc.name}: unknown database {doc.database!r}.")
        for s in doc.sections:
            if s.database not in cfg.databases:
                raise ConfigError(f"documents.{doc.name}: section {s.title!r} has unknown database {s.database!r}.")
            if s.document and s.document not in cfg.documents:
                raise ConfigError(f"documents.{doc.name}: section {s.title!r} has unknown document {s.document!r}.")
