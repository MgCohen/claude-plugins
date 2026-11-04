---
name: notion-snippets
description: Adds or changes a live code snippet in Notion. A row in the Notion Snippets database selects a method or a line range of a GitHub file, and a GitHub Action writes that code into a native Notion code block. Use when the user asks to show, embed, quote or keep code from a repo in a Notion page, or to fix a Snippets row with Status Error.
---

# Notion snippets

A Snippets row selects code in a GitHub file. The Action of that repo writes the code into the first code block on the row page. Doc pages show that code block with a reference to its synced block.

## Add a snippet

1. Make a row in the Snippets database. Write the properties from the table below.
2. On the row page, put one empty code block inside a synced block. A doc page can show only a synced block.
3. Run the plan in a checkout of the code repo: `python -m notion_context snippets plan`, with `PYTHONPATH` set to the `notion-context` plugin folder, and `NOTION_TOKEN` and `NOTION_SNIPPETS_DATABASE` set. If you cannot run it, run the workflow: `gh workflow run notion-snippets.yml -f mode=plan`.
4. If the plan shows the correct range, run the workflow with `-f mode=apply`, or wait for the next push to `main`.
5. On the doc page, add a reference to the synced block of the row page.

| Property | Value | Example |
|---|---|---|
| File | GitHub file link | `https://github.com/owner/repo/blob/main/src/OrderService.cs` |
| Method | Declaration name, empty for a line range | `OrderService.Total` |
| Overload | Which declaration, if more than one has the name | `2` |
| Start line, End line | Line range, if Method is empty | `21`, `32` |
| Lines before, Lines after | Lines to add on each side | `3`, `2` |

## Select the code

- Use a method when you can. The Action finds the method again after each change. A line range moves only with the git diff, and only if Start line and End line both have a value.
- A method range starts at the declaration line. Use Lines before for attributes and doc comments.
- A commit in the File link (`blob/<sha>/...`) pins the code. The snippet never changes. A branch in the link has no effect: the Action reads the commit that it runs on.
- If Method, Start line and End line are all empty, the snippet is the whole file.
- `Outer.Inner` searches `Inner` inside `Outer`. A declaration is a method, constructor, property, field or type in C#, TypeScript or JavaScript.

## Fix a row with Status Error

The Message property gives the reason. Correct the row, then run the plan again.

| Message | Fix |
|---|---|
| `No declaration named "X"` | The method was renamed or deleted. Write the correct name |
| `Only N declaration(s) named "X"` | Write a smaller Overload, or use `Outer.X` |
| `Line N is outside the file` | Write a line range in the file |
| `No code block on the row page` | Put an empty code block on the row page |

## Rules

- Do not edit a synced code block in Notion. The next run replaces the edit.
- The Action of a repo writes only the rows whose File is in that repo. One database can serve many repos.
