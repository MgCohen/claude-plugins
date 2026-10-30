#!/usr/bin/env bash
# WorktreeCreate: in a git repo whose root is a Unity project, make the session's worktree with
# `unity vcs git worktree add`, beside the repo in `<repo>.wt/<name>` (the Unity CLI refuses a
# worktree inside the checkout), its Library seeded from the main checkout. Anywhere else, or when
# the Unity CLI fails, make the plain git worktree Claude Code would. Prints the worktree's path.
input=$(cat)
field() { printf '%s' "$input" | sed -nE "s/.*\"$1\"[[:space:]]*:[[:space:]]*\"([^\"]*)\".*/\1/p" | sed 's#\\\\#/#g'; }
cwd=$(field cwd)
name=$(field name)
seed=${CLAUDE_PLUGIN_OPTION_SEED:-cache}

# The main checkout's root, also when cwd is inside one of its worktrees.
root=$(git -C "$cwd" rev-parse --path-format=absolute --git-common-dir) || exit 1
root=${root%/.git}

plain() {
  dir="$root/.claude/worktrees/$name"
  git -C "$root" worktree add -q -b "worktree-$name" "$dir" HEAD >&2 ||
    git -C "$root" worktree add -q "$dir" "worktree-$name" >&2 || exit 1
  echo "$dir"
  exit 0
}

git -C "$root" cat-file -e HEAD:ProjectSettings/ProjectVersion.txt 2>/dev/null || plain
command -v unity >/dev/null 2>&1 || { echo "unity-worktrees: Unity CLI not found; plain worktree." >&2; plain; }

dir="$root.wt/$name"
if git -C "$root" worktree list --porcelain | grep -qixF "worktree $dir"; then echo "$dir"; exit 0; fi

# The app records the session's branch as the worktree name, so the branch is the name.
UNITY_NO_PAGER=1 UNITY_NO_CRASH_REPORT=1 UNITY_NO_CLI_INVOKED_TELEMETRY=1 \
  unity vcs git worktree add "$name" "$root" --into "$dir" --seed "$seed" \
  --no-register -y --non-interactive --no-banner >&2 ||
  { echo "unity-worktrees: Unity CLI failed; plain worktree." >&2; plain; }
echo "$dir"
