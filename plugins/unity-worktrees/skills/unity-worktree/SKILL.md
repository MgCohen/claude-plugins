---
name: unity-worktree
description: Use whenever you create a git worktree of a Unity project (a repo with ProjectSettings/ProjectVersion.txt). Gives the Unity CLI command that makes the worktree and seeds its Library.
---

# Make a worktree of a Unity project

Use the Unity CLI. Do not use `git worktree add`. Do not copy the `Library` folder.

```bash
unity vcs git worktree add <branch> <repo-root> --into <repo>.wt/<name> --seed cache --no-register -y --non-interactive
```

| Argument or flag | Meaning |
|---|---|
| `<branch>` | The branch of the worktree. If the branch does not exist, the CLI makes it from the current HEAD. |
| `<repo-root>` | The root of the main checkout (the project to branch from). |
| `--into <repo>.wt/<name>` | The worktree folder, beside the repo. The CLI refuses a folder inside the checkout. |
| `--seed cache` | Copy the package and import caches from the main checkout. Use `full` to copy all of `Library`, or `none` for no copy. |
| `--no-register` | Do not add the worktree to the Unity Hub. |
| `-y --non-interactive` | Do not ask questions. |

## Notes

- The plugin hook denies `git worktree add` in a Unity repo from the Bash and PowerShell tools.
- Worktree sessions of the app already use this command through the `WorktreeCreate` hook.
