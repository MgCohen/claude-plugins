"""Convert Notion property values to plain Python values, and build filters."""


def rich_text(items, markdown=False):
    if not markdown:
        return "".join(t.get("plain_text", "") for t in items)
    out = []
    for t in items:
        s = t.get("plain_text", "")
        if not s:
            continue
        a = t.get("annotations", {})
        if a.get("code"):
            s = f"`{s}`"
        if a.get("bold"):
            s = f"**{s}**"
        if a.get("italic"):
            s = f"*{s}*"
        if a.get("strikethrough"):
            s = f"~~{s}~~"
        href = t.get("href")
        if href and t.get("type") != "mention":
            s = f"[{s}]({href})"
        out.append(s)
    return "".join(out)


def value(prop):
    """One property -> str | int | float | bool | list | None."""
    t = prop["type"]
    v = prop.get(t)
    if t in ("title", "rich_text"):
        return rich_text(v) or None
    if t in ("select", "status"):
        return v["name"] if v else None
    if t == "multi_select":
        return [o["name"] for o in v]
    if t == "unique_id":
        return f'{v["prefix"]}-{v["number"]}' if v.get("prefix") else v["number"]
    if t == "relation":
        return [r["id"] for r in v]
    if t == "people":
        return [p.get("name") or p["id"] for p in v]
    if t == "date":
        if not v:
            return None
        return f'{v["start"]}/{v["end"]}' if v.get("end") else v["start"]
    if t == "formula":
        return v.get(v["type"]) if v else None
    if t == "rollup":
        if v["type"] == "array":
            return [value(x) for x in v["array"]]
        return v.get(v["type"])
    if t == "files":
        return [f.get("name") for f in v]
    if t in ("created_by", "last_edited_by"):
        return v.get("name") or v.get("id")
    if t == "verification":
        return v.get("state") if v else None
    # number, checkbox, url, email, phone_number, created_time, last_edited_time
    return v


def flatten(page, include=None, exclude=()):
    """Page -> {property: value}, plus id. Drops empty values."""
    out = {}
    for name, p in page["properties"].items():
        if include is not None and name not in include:
            continue
        if name in exclude:
            continue
        v = value(p)
        if v not in (None, [], ""):
            out[name] = v
    out["id"] = page["id"]
    return out


def title_of(page):
    for p in page["properties"].values():
        if p["type"] == "title":
            return rich_text(p["title"])
    return ""


def parse_key(key):
    """'ISS-12' -> ('ISS', 12); '12' -> (None, 12)."""
    prefix, _, num = key.rpartition("-")
    if not num.isdigit():
        raise ValueError(f"Not a key: {key!r}")
    return (prefix or None), int(num)


def filter_for(prop_name, prop_type, raw):
    """Build a Notion filter from 'Prop=value' text, based on the property type."""
    neg = raw.startswith("!")
    val = raw[1:] if neg else raw
    if prop_type in ("select", "status"):
        return {"property": prop_name, prop_type: {"does_not_equal" if neg else "equals": val}}
    if prop_type in ("multi_select", "relation", "people"):
        return {"property": prop_name, prop_type: {"does_not_contain" if neg else "contains": val}}
    if prop_type == "checkbox":
        b = val.lower() in ("1", "true", "yes", "y")
        return {"property": prop_name, "checkbox": {"equals": (not b) if neg else b}}
    if prop_type in ("number",):
        return {"property": prop_name, "number": {"does_not_equal" if neg else "equals": float(val)}}
    if prop_type == "unique_id":
        return {"property": prop_name, "unique_id": {"does_not_equal" if neg else "equals": parse_key(val)[1]}}
    if prop_type in ("title", "rich_text", "url", "email", "phone_number"):
        return {"property": prop_name, prop_type: {"does_not_contain" if neg else "contains": val}}
    if prop_type == "date":
        if neg:
            raise ValueError(f"Cannot negate a date filter on {prop_name!r}.")
        return {"property": prop_name, "date": {"equals": val}}
    raise ValueError(f"Cannot filter on {prop_name!r} (type {prop_type}).")
