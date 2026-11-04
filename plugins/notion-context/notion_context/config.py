"""Load, merge and validate the TOML config.

pointers:  name -> Notion id, for pages that skills and tools refer to by name.
databases: one entry for each Notion database (alias -> id, data source, key property).
documents: one recipe for each output type (which fields, body, related sections).

The config is a stack of layers. Each layer overrides the keys of the layers before it.
"""
import os
import re
import tomllib
from dataclasses import dataclass, field

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_PATH = os.path.join(HERE, "notion-context.default.toml")
FILE_NAME = "notion-context.toml"
POINTER_NAME = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")

SECTION_STYLES = ("table", "list", "full")
CHILD_DB_MODES = ("skip", "link", "rows")


class ConfigError(Exception):
    pass


@dataclass
class Database:
    alias: str
    id: str
    source: str | None = None     # data source id, for the Notion MCP (collection://...)
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
    pointers: dict = field(default_factory=dict)   # name -> id
    layers: list = field(default_factory=list)     # files, lowest first
    origin: dict = field(default_factory=dict)     # "pointers.<name>" or "databases.<alias>" -> file that set it

    def pointer(self, name):
        """Resolve a name: a pointer, a database alias, or <alias>.source."""
        if name in self.pointers:
            return self.pointers[name]
        alias, _, part = name.partition(".")
        if alias in self.databases and part in ("", "id", "source"):
            value = self.databases[alias].source if part == "source" else self.databases[alias].id
            if value:
                return value
        raise ConfigError(f"Unknown pointer {name!r}. Known: {', '.join(self.pointer_names())}")

    def pointer_layer(self, name):
        if name in self.pointers:
            return self.origin.get(f"pointers.{name}", "")
        return self.origin.get(f"databases.{name.partition('.')[0]}", "")

    def pointer_names(self):
        names = list(self.pointers)
        for alias, d in self.databases.items():
            names.append(alias)
            if d.source:
                names.append(f"{alias}.source")
        return sorted(names)

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


def layer_paths(explicit=None, defaults=True):
    """Existing config files, lowest layer first."""
    project = os.environ.get("CLAUDE_PROJECT_DIR")
    user = os.environ.get("NOTION_CONTEXT_USER_CONFIG") or os.path.join(os.path.expanduser("~"), ".claude", FILE_NAME)
    candidates = [DEFAULT_PATH if defaults else None, user if defaults else None,
                  os.path.join(project, FILE_NAME) if project else None, FILE_NAME,
                  os.environ.get("NOTION_CONTEXT_CONFIG"), explicit]
    out, seen = [], set()
    for p in candidates:
        if p and os.path.exists(p):
            real = os.path.realpath(p)
            if real not in seen:
                seen.add(real)
                out.append(p)
    if explicit and not os.path.exists(explicit):
        raise ConfigError(f"No config file {explicit!r}.")
    if not out:
        raise ConfigError(f"No config. Expected {DEFAULT_PATH}, ~/.claude/{FILE_NAME}, "
                          f"$CLAUDE_PROJECT_DIR/{FILE_NAME}, ./{FILE_NAME}, $NOTION_CONTEXT_CONFIG or --config.")
    return out


def load(explicit=None, defaults=True):
    """Merge all layers and parse the result."""
    paths = layer_paths(explicit, defaults)
    raw, origin = {}, {}
    for p in paths:
        with open(p, "rb") as f:
            layer = tomllib.load(f)
        for table in ("pointers", "databases"):
            for name in layer.get(table, {}):
                origin[f"{table}.{name}"] = p
        raw = merge(raw, layer)
    cfg = parse(raw, paths[-1])
    cfg.layers, cfg.origin = paths, origin
    return cfg


def merge(base, top):
    """Tables merge key by key. Other values, arrays too, replace."""
    out = dict(base)
    for k, v in top.items():
        out[k] = merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


def parse(raw, path=""):
    s = raw.get("settings", {})
    pointers = {}
    for name, v in raw.get("pointers", {}).items():
        if not POINTER_NAME.match(name):
            raise ConfigError(f"pointers.{name}: use lowercase letters, digits, '-', '_' and '.'.")
        if not isinstance(v, str) or not v:
            raise ConfigError(f"pointers.{name}: the value must be a Notion id or URL.")
        pointers[name] = v
    dbs = {}
    for alias, d in raw.get("databases", {}).items():
        _keys(d, {"id", "source", "key", "prefix", "document"}, f"databases.{alias}")
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
    cfg = Config(dbs, docs, s.get("child_databases", "link"), s.get("max_depth", 3), path, pointers)
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
