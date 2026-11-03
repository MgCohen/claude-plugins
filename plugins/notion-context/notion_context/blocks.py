"""Convert a page's block tree to Markdown (recursive)."""
import re

from .client import NotionError
from .props import flatten, rich_text

HEADING = re.compile(r"^#{1,6} ")
LIST_TYPES = {"bulleted_list_item", "numbered_list_item", "to_do"}


class BodyReader:
    """Reads a page body. Child databases: 'skip', 'link' or 'rows'."""

    def __init__(self, client, databases="link", max_depth=8):
        self.client = client
        self.databases = databases
        self.max_depth = max_depth

    def markdown(self, page_id, heading_shift=0):
        lines = _tidy(self._blocks(self.client.children(page_id), 0, heading_shift))
        while lines and (lines[-1] == "" or HEADING.match(lines[-1])):
            lines.pop()  # a last heading with no content, e.g. above linked views only
        return "\n".join(lines).strip() + "\n" if lines else ""

    def _children(self, block, depth, shift):
        if not block.get("has_children") or depth >= self.max_depth:
            return []
        return self._blocks(self.client.children(block["id"]), depth + 1, shift)

    def _blocks(self, blocks, depth, shift):
        out, n = [], 0
        for b in blocks:
            t = b["type"]
            n = n + 1 if t == "numbered_list_item" else 0
            out += self._block(b, t, depth, shift, n)
        return out

    def _block(self, b, t, depth, shift, n):
        d = b.get(t, {})
        text = rich_text(d.get("rich_text", []), markdown=True)
        ind = "  " * depth if depth else ""
        if t.startswith("heading_"):
            level = min(int(t[-1]) + shift, 6)
            head = [f"{'#' * level} {text}", ""]
            if d.get("is_toggleable"):
                return head + self._children(b, depth, shift)
            return head
        if t in LIST_TYPES:
            mark = {"bulleted_list_item": "-", "numbered_list_item": f"{n}.",
                    "to_do": "- [x]" if d.get("checked") else "- [ ]"}[t]
            return [f"{ind}{mark} {text}"] + self._children(b, depth, shift)
        if t == "toggle":
            return [f"{ind}- {text}"] + self._children(b, depth, shift)
        if t == "paragraph":
            return ([f"{ind}{text}", ""] if text else []) + self._children(b, depth, shift)
        if t in ("quote", "callout"):
            icon = (d.get("icon") or {}).get("emoji", "") if t == "callout" else ""
            body = [f"> {icon + ' ' if icon else ''}{text}"]
            body += [f"> {l}" if l else ">" for l in self._children(b, 0, shift)]
            return body + [""]
        if t == "code":
            lang = d.get("language", "")
            return ["```" + ("" if lang == "plain text" else lang), rich_text(d.get("rich_text", [])), "```", ""]
        if t == "divider":
            return ["---", ""]
        if t == "equation":
            return ["$$", d.get("expression", ""), "$$", ""]
        if t == "table":
            return self._table(b) + [""]
        if t == "child_page":
            return [f"{ind}- Subpage: {d.get('title', '')}"]
        if t == "child_database":
            return self._database(b, d.get("title") or "Untitled")
        if t in ("column_list", "column", "synced_block"):
            return self._children(b, depth - 1 if depth else 0, shift)
        if t in ("bookmark", "embed", "link_preview", "image", "file", "pdf", "video"):
            url = d.get("url") or (d.get(d.get("type", ""), {}) or {}).get("url", "")
            cap = rich_text(d.get("caption", []))
            return [f"{ind}[{cap or t}]({url})", ""] if url else []
        if t == "link_to_page":
            return [f"{ind}- Link to page {d.get(d.get('type'), '')}"]
        if text:
            return [f"{ind}{text}", ""]
        return []

    def _table(self, b):
        rows = [[rich_text(c, markdown=True).replace("|", "\\|") for c in r["table_row"]["cells"]]
                for r in self.client.children(b["id"]) if r["type"] == "table_row"]
        if not rows:
            return []
        out = ["| " + " | ".join(rows[0]) + " |", "|" + "---|" * len(rows[0])]
        return out + ["| " + " | ".join(r) + " |" for r in rows[1:]]

    def _database(self, b, title):
        if self.databases == "skip":
            return []
        try:
            self.client.database(b["id"])
        except NotionError as e:
            if "linked database" in str(e):
                return []  # linked view: display only, data comes from relations
            raise
        if self.databases == "link":
            return [f"- Database: {title}", ""]
        rows = [flatten(r) for r in self.client.query(b["id"])]
        return [f"**{title}**", ""] + [f"- {_row_text(r)}" for r in rows] + [""]


def _row_text(row):
    return "; ".join(f"{k}: {v}" for k, v in row.items() if k != "id")


def _tidy(lines):
    """Collapse repeated blank lines."""
    out = []
    for l in lines:
        if l == "" and (not out or out[-1] == ""):
            continue
        out.append(l)
    return out
