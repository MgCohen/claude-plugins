---
name: stream-tracker
description: Read and write a stream tracker page (a copy of the Stream Tracker Template with its own database), make a new copy, or change the template. Use it when you update a project tracker after a session, a merge, a release, a PR or an issue change, or when the user asks for a tracker.
---

# Stream tracker

A stream tracker is an Artifact page with its own database. The page code comes from one template. Each project has one copy. The page shows only data: you change the data, not the page.

## Pages

| Page | URL | Owner session (writes the data) |
|---|---|---|
| Template (sample data) | https://claude.ai/artifact/SZPxucxEj6rHCbjrLVmLQD | The session that changes the template |
| Umpire (vsa-template) | https://claude.ai/artifact/6W18kfHNc1MTa5FA1Vi5AA | Run Orchestrator (local_21ecf451) |
| Session orchestrator (playground) | https://claude.ai/artifact/CemHkpNcXTfe6d6kHhLrBV | Orchestrator: root (local_ab9acae5) |
| vsa-unity test suite | https://claude.ai/artifact/5W7EdkKmdTBedXtnTG5f3T | Unity testing automation (local_3cd7ba6c) |
| vsa-unity | https://claude.ai/artifact/XgxVDhQihS7TQHV8Fe4xTH | VSA project preview review (local_b2d473a6) |

Only the owner session writes the data of a copy. Another session asks the owner.

## Write data

Use the `ArtifactData` tool with `url` = the page URL.

1. Read a document before you write it. Pass its version as `if_version`. If the write fails, read again and redo it.
2. Use `update` to change some fields. Use `set` only for a new document or a full replace.
3. For more than two writes, use one `batch` (50 writes at most).
4. Do not publish the page. Do not delete items: old items keep the history.
5. Do not add free text for the page to show, and do not add custom tabs (`views`).

### Collections

| Collection | Document id | Holds |
|---|---|---|
| `settings` | `project` | Title, repositories, streams, roadmap steps (`phases`), timeline position, `updated` |
| `items` | The item id (characters `A-Z a-z 0-9 _ - . ~ : @ +` only) | Tasks, research, capabilities, releases, integration points |
| `sessions` | The first 8 characters of the session id, after `local_` | Session records |
| `issues` | The number, or `name:number` for another repository | GitHub issues |
| `prs` | The number, or `name:number` for another repository | GitHub PRs |

### Common changes

| Event | Write |
|---|---|
| An item changes state | `update` items/<id>: `state` (and `waits` when a person must act) |
| New task | `set` items/<id>: `id`, `kind`, `stream`, `title`, `state`, `phase`, `seq`, `in`; add `after`, `from`, `prs`, `issues`, `session`, `needs` when known |
| Item waits for another project | `update` items/<id>: `state: "ext"`, `waits` |
| New release on main | `set` items/<id>: `kind: "release"`, `state: "main"`, `label`, `phase`, `seq`; set `in` on the items that it holds; `update` settings/project: `hereAfter`, `hereLabel`, `updated` |
| New integration point | `set` items/<id>: `kind: "integration"`, `state`, `seq`, `label`; `into` when it merges into a release or into a later point |
| New session | `set` sessions/<8 chars>: `id`, `name`, `status`, `lastActivity`; `update` the item: `session` |
| Session archived | `update` sessions/<8 chars>: `status: "Archived"` |
| PR opened or merged | `set` or `update` prs/<n>: `number`, `title`, `state`; add the number to `prs` of the item |
| Issue opened or closed | `set` or `update` issues/<n>; set `status` with the rule below |
| Current step moves | `update` settings/project: `phases`, with `current: true` on one step only |

## Rules: issues and items

1. A GitHub issue is for a bug, a problem or research. A step (an item) is for a feature, a limitation or a detail of a feature.
2. A step can name issues in `issues`. It does not need one.
3. When work on an issue is expected, a step must name it. An issue that no step names is "Not planned": no work is expected yet.

### Issue status

| Status | GitHub | Items that name the issue |
|---|---|---|
| Done | Closed as completed | Any |
| Closed | Closed as not planned | Any |
| In progress | Open | One item is `work` or `stack` |
| Waits for another team | Open | Each item is `ext` |
| Partly done | Open | One item is `main` or `int` |
| Planned | Open | Items exist, none started |
| Not planned | Open | No item names it |

## State codes

| Code | Health | Stage |
|---|---|---|
| `main`, `int` | Done | Merged |
| `stack` | Done | PR open |
| `work` | In progress | Running |
| `user` | Waits for you | Waits for an answer |
| `plan` | Planning | Waits for an answer |
| `future` | Not started | None |
| `ext` | Waits for another team | None |

An item can set `health` (fine, run, wait, block, plan, off, ext) or `stage` (merged, open, review, answer, running, cancelled, stopped, none) to override one mark.

## Timeline model

- **Points:** an item of kind `release` is a square on lane 0 (main). An item of kind `integration` is a diamond on lane 1 (the integration line). Integration points with no `into` chain on lane 1. An integration point with `into` = a later release merges there. With `into` = another integration point, it is a nested point on its own lane.
- **Items:** `in` is the point where the line merges. The timeline shows only items with `in`. `from` is the point where the line starts, when it is not the point before. `after` is one parent item or a list of parents. `merge: false` ends a side line that does not merge.
- **Lanes:** the page computes them. A line that an item of the same point continues does not merge on its own.
- **Headings:** a step heading shows when the step (`phase`) changes. `section` on an item shows a free heading in its place. `timelineHeadings: "sections"` in settings shows only the free headings.
- **Position:** `hereAfter` (a point id) and `hereLabel` place the "You are here" line.

## Fields

### settings/project

| Field | Use |
|---|---|
| `title` | Page heading and tab title |
| `repo` | The GitHub repository URL; numbers link to it |
| `repos` | Other repositories by short name, for example `{ tpl: "https://github.com/owner/repo" }`; a link `"tpl#230"` uses it |
| `updated` | Date of the last data change |
| `here` | Optional note for writers; the page does not show it |
| `hereAfter`, `hereLabel` | Timeline position (see above) |
| `since` | Optional: hide the points before this point id |
| `streams` | `{ id, name, desc, session, external, prs, issues, artifacts }` in display order; `external: true` marks a stream that another team owns |
| `phases` | Roadmap steps in order: `{ id, name, content, current, waits, state, prs, issues, artifacts }`. The step number is the place in the list: 1 to N, with no restart and no labels. Do not add milestone headings or groups |
| `states` | Optional: state code → `[health, stage]`, merged over the defaults |
| `timelineHeadings` | Optional: `"sections"` |
| `owner` | Footer line: who keeps the data |

### items

`id`, `kind` (task, research, capability, release, integration), `stream`, `title`, `state`, `health`, `stage`, `seq` (sort and time order), `phase` (roadmap step; an item with no step shows only in the inventory), `needs` (items that come first), `tag` (short text after the id), `in`, `from`, `after`, `into`, `section`, `merge`, `label` (timeline row text), `prs`, `issues` (numbers, or `"name#n"`), `artifacts` (`[{ title, url }]`), `branch`, `session`, `waits`, `note`.

### sessions

`id` (full id), `name`, `status` (Running, Open, Shelf or Archived), `pr`, `lastActivity`.

### issues

`number`, `title`, `state` (open or closed), `status` (see the table), `prs`, `items`, `phase`, `milestone`, `repo` (short name for another repository).

### prs

`number`, `title`, `state` (merged, open or closed), `repo` (short name for another repository).

## Make a new copy

1. Write a shell file `index.html` with three lines: `<title>NAME Stream Map</title>`, `<div id="app"></div>` and `<script src="tracker.js"></script>`.
2. Publish it with the `Artifact` tool:
   - `files: { "tracker.js": { "artifact": "<template URL>", "path": "tracker.js" } }`
   - `capabilities: { "db": { "rules": [{ "path": "", "read": "view", "write": "admin" }] } }`
   - `icon: "map"`
3. Write `settings/project` and the items with `ArtifactData` batches.
4. Add the new page to the table in this skill.

## Change the template

1. Read `tracker.js` from the template: `Artifact` action `read`, `path: "tracker.js"`.
2. Edit the saved file. Check it with sample data on a phone width and a desktop width before you publish.
3. Publish the template with `files: { "tracker.js": "<local path>" }`.
4. For each copy: read its `tracker.js` (a publish needs it), then publish its shell again with `files: { "tracker.js": { "artifact": "<template URL>", "path": "tracker.js" } }`.
5. Tell each owner session what changed.
