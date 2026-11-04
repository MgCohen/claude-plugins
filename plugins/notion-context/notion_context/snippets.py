import collections
import hashlib
import os
import re
import subprocess
import urllib.parse

from .client import NotionError
from .props import rich_text
from .snippet_range import snippet_range

LANGUAGES = {"cs": "c#", "js": "javascript", "jsx": "javascript", "mjs": "javascript", "ts": "typescript", "tsx": "typescript", "py": "python", "sql": "sql", "json": "json"}
FILE = re.compile(r"https://github\.com/([^/]+/[^/]+)/blob/([^/]+)/([^?#]+)")
COMMIT = re.compile(r"[0-9a-f]{7,40}")
HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", re.M)
CHUNK = 1000
MAX_CHUNKS = 100


def git(*args):
    run = subprocess.run(["git", *args], capture_output=True, text=True, encoding="utf-8")
    if run.returncode:
        raise ValueError(run.stderr.strip() or f"git {args[0]} failed.")
    return run.stdout


def texts(prop):
    prop = prop or {}
    return prop.get("rich_text") or prop.get("title") or []


def number(prop):
    value = (prop or {}).get("number")
    return None if value is None else int(value)


def rich(content, url=None):
    return {"rich_text": [{"type": "text", "text": {"content": content, "link": {"url": url} if url else None}}] if content else []}


def read_rows(client, database):
    rows = []
    for p in client.query(database):
        pr = p["properties"]
        file = (pr.get("File") or {}).get("url") or ""
        link = FILE.match(file)
        region = texts(pr.get("Region"))
        since = FILE.match(region[0].get("href") or "") if region else None
        rows.append({
            "id": p["id"],
            "name": rich_text(texts(pr.get("Name"))),
            "file": file,
            "repo": link and link[1],
            "ref": link and link[2],
            "path": link and urllib.parse.unquote(link[3]),
            "method": rich_text(texts(pr.get("Method"))).strip(),
            "overload": number(pr.get("Overload")) or 1,
            "start": number(pr.get("Start line")),
            "end": number(pr.get("End line")),
            "before": number(pr.get("Lines before")) or 0,
            "after": number(pr.get("Lines after")) or 0,
            "since": since[2] if since and COMMIT.fullmatch(since[2]) else None,
            "hash": rich_text(texts(pr.get("Hash"))),
            "status": ((pr.get("Status") or {}).get("select") or {}).get("name"),
            "message": rich_text(texts(pr.get("Message"))),
        })
    return rows


def follow_range(diff, start, end):
    new_start, new_end, edited = start, end, False
    for m in HUNK.finditer(diff):
        old, old_count = int(m[1]), 1 if m[2] is None else int(m[2])
        new, new_count = int(m[3]), 1 if m[4] is None else int(m[4])
        if old_count == 0:
            new_start += new_count if old < start else 0
            new_end += new_count if old < end else 0
            edited |= start <= old < end
            continue
        old_last, first_new = old + old_count - 1, new if new_count else new + 1
        if old_last < start:
            new_start += new_count - old_count
        elif old <= start:
            new_start = first_new
        if old_last < end:
            new_end += new_count - old_count
        elif old <= end:
            new_end = first_new + new_count - 1
        edited |= old <= end and old_last >= start
    return new_start, new_end, edited


def dedent(lines):
    cut = min((len(line) - len(line.lstrip()) for line in lines if line.strip()), default=0)
    return [line[cut:] for line in lines]


def resolve(row, head):
    if not row["path"]:
        raise ValueError(f'File must be a GitHub file link, not "{row["file"]}".')
    path = row["path"]
    commit = row["ref"] if COMMIT.fullmatch(row["ref"]) else head
    source = git("show", f"{commit}:{path}")
    start, end, moved = row["start"], row["end"], None
    if not row["method"] and start and end and commit == head and row["since"]:
        try:
            new_start, new_end, edited = follow_range(git("diff", "-U0", row["since"], head, "--", path), start, end)
        except ValueError:
            new_start, new_end, edited = start, end, False
        if new_end < new_start:
            raise ValueError(f"The lines {start}-{end} were deleted.")
        if (new_start, new_end) != (start, end) or edited:
            moved = f"{'edited' if edited else 'moved'}, was {start}-{end}"
            start, end = new_start, new_end
    first, last = snippet_range(source, row["method"], row["overload"], start, end, row["before"], row["after"])
    lines = source.replace("\r", "").split("\n")
    code = "\n".join(dedent(lines[first - 1 : last]))
    if len(code) > CHUNK * MAX_CHUNKS:
        raise ValueError(f"The code has more than {CHUNK * MAX_CHUNKS} characters.")
    language = LANGUAGES.get(path.rsplit(".", 1)[-1].lower(), "plain text")
    region = f"L{first}-L{last}"
    return {
        "code": code,
        "language": language,
        "anchor": f"{path}#{region}",
        "region": region,
        "commit": commit,
        "permalink": f"https://github.com/{row['repo']}/blob/{commit}/{urllib.parse.quote(path)}#{region}",
        "hash": hashlib.sha256(f"{language}\n{path}#{region}\n{code}".encode()).hexdigest()[:16],
        "moved": moved,
        "start": start,
        "end": end,
    }


def find_code_block(client, block_id, depth=0):
    for b in client._paginate("GET", f"/blocks/{block_id}/children"):
        if b["type"] == "code":
            return b["id"]
        if b["has_children"] and depth < 2 and b["type"] not in ("child_page", "child_database"):
            inner = find_code_block(client, b["id"], depth + 1)
            if inner:
                return inner
    return None


def write(client, row, snippet):
    block = find_code_block(client, row["id"])
    if not block:
        raise ValueError("No code block on the row page.")
    code = snippet["code"]
    parts = [{"type": "text", "text": {"content": code[i : i + CHUNK]}} for i in range(0, max(len(code), 1), CHUNK)]
    caption = rich(snippet["anchor"], snippet["permalink"])["rich_text"] + rich(f" @ {snippet['commit'][:7]}")["rich_text"]
    client.request("PATCH", f"/blocks/{block}", {"code": {"rich_text": parts, "language": snippet["language"], "caption": caption}})
    properties = {
        "Region": rich(snippet["region"], snippet["permalink"]),
        "Hash": rich(snippet["hash"]),
        "Status": {"select": {"name": "In sync"}},
        "Message": rich(""),
    }
    if snippet["moved"]:
        properties.update({"Start line": {"number": snippet["start"]}, "End line": {"number": snippet["end"]}})
    client.request("PATCH", f"/pages/{row['id']}", {"properties": properties})


def sync(client, rows, repo, head, mode):
    results = []
    for row in rows:
        target = row["method"] or (f"L{row['start']}-L{row['end'] or 'end'}" if row["start"] else "file")
        report = lambda result, note: results.append((row["name"], target, result, note))
        if not row["file"]:
            report("skipped", "File is empty")
            continue
        if row["repo"] and row["repo"].lower() != repo.lower():
            report("skipped", f"File is in {row['repo']}")
            continue
        try:
            snippet = resolve(row, head)
            note = f"{snippet['anchor']} ({snippet['moved']})" if snippet["moved"] else snippet["anchor"]
            if mode != "force" and snippet["hash"] == row["hash"] and row["status"] == "In sync" and not snippet["moved"]:
                report("unchanged", note)
            elif mode == "plan":
                report("will update" if row["hash"] else "new", note)
            else:
                write(client, row, snippet)
                report("updated" if row["hash"] else "new", note)
        except (ValueError, NotionError) as e:
            error = str(e)[:2000]
            known = row["status"] == "Error" and row["message"] == error
            if mode != "plan" and not known:
                try:
                    client.request("PATCH", f"/pages/{row['id']}", {"properties": {"Status": {"select": {"name": "Error"}}, "Message": rich(error)}})
                except NotionError as status_error:
                    error += f" Status not written: {status_error}"
            report("error (known)" if known else "error", error)
    return results


def current_repo():
    return os.environ.get("GITHUB_REPOSITORY") or re.search(r"github\.com[:/](.+?)(?:\.git)?$", git("remote", "get-url", "origin").strip())[1]


def run(client, database, mode):
    head = os.environ.get("GITHUB_SHA") or git("rev-parse", "HEAD").strip()
    results = sync(client, read_rows(client, database), current_repo(), head, mode)
    counts = collections.Counter(result for _, _, result, _ in results)
    rows = [f"| {name} | `{target}` | {result} | {note.replace('|', chr(92) + '|')} |" for name, target, result, note in results]
    summary = "\n".join([
        f"### Notion snippets: {mode} at `{head[:7]}`",
        "",
        ", ".join(f"{v} {k}" for k, v in counts.items()) + f", {client.calls} Notion API calls",
        "",
        "| Snippet | Target | Result | Region or error |",
        "|---|---|---|---|",
        *rows,
    ])
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
            f.write(summary + "\n")
    return summary + "\n", 1 if counts["error"] else 0
