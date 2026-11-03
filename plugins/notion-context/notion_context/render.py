"""Render a document tree as Markdown or JSON."""
import json
import re


def to_json(node):
    return json.dumps(node, ensure_ascii=False, indent=2) + "\n"


def to_markdown(node, level=1):
    out = []
    _node(node, level, out)
    return "\n".join(_tidy(out)).strip() + "\n"


def _node(node, level, out):
    h = "#" * min(level, 6)
    head = f'{node["key"]}: {node["title"]}' if node.get("key") else node["title"]
    out += [f"{h} {head}", ""]
    for k, v in node.get("fields", {}).items():
        out.append(f"- **{k}:** {_cell(v)}")
    if node.get("fields"):
        out.append("")
    if node.get("body"):
        out += [_shift(node["body"], level), ""]
    for s in node.get("sections", []):
        out += [f'{"#" * min(level + 1, 6)} {s["title"]} ({len(s["items"])})', ""]
        if not s["items"]:
            out += ["None.", ""]
        elif s["style"] == "full":
            for item in s["items"]:
                if "sections" in item:
                    _node(item, level + 2, out)
                else:  # depth limit or cycle: fall back to one line
                    out.append(f'- {_label(item)}')
            out.append("")
        elif s["style"] == "list":
            out += [f'- {_label(i)}{_suffix(i, s["columns"])}' for i in s["items"]] + [""]
        else:
            out += _table(s["items"], s["columns"]) + [""]


def _label(item):
    return f'{item["key"]}: {item["title"]}' if item.get("key") else item["title"]


def _suffix(item, columns):
    vals = [f"{c}: {_cell(item['fields'][c])}" for c in columns
            if c in item["fields"] and _cell(item["fields"][c]) not in (item.get("key"), item.get("title"))]
    return f' ({"; ".join(vals)})' if vals else ""


def _table(items, columns):
    cols = columns or sorted({k for i in items for k in i["fields"] if k != "id"})
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for i in items:
        out.append("| " + " | ".join(_cell(i["fields"].get(c)) for c in cols) + " |")
    return out


def _cell(v):
    if v is None:
        return ""
    if isinstance(v, bool):
        return "yes" if v else "no"
    if isinstance(v, list):
        v = ", ".join(map(str, v))
    return str(v).replace("|", "\\|").replace("\n", " ")


def _headings(md):
    """(line index, hash count) of each Markdown heading outside code fences."""
    found, in_code = [], False
    for i, line in enumerate(md.splitlines()):
        if line.startswith("```"):
            in_code = not in_code
        elif not in_code and re.match(r"^#{1,6} ", line):
            found.append((i, len(line) - len(line.lstrip("#"))))
    return found


def _shift(md, level):
    """Put the top body heading one level below the node heading."""
    heads = _headings(md)
    if not heads:
        return md
    delta = level + 1 - min(h for _, h in heads)
    lines = md.splitlines()
    for i, h in heads:
        lines[i] = "#" * max(1, min(h + delta, 6)) + lines[i][h:]
    return "\n".join(lines)


def _tidy(lines):
    out = []
    for l in lines:
        if l == "" and (not out or out[-1] == ""):
            continue
        out.append(l)
    return out
