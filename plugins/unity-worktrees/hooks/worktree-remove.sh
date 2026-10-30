#!/usr/bin/env bash
# WorktreeRemove: remove the session's worktree folder (Library included) unless it has uncommitted
# work. The session's branch is always kept.
input=$(cat)
dir=$(printf '%s' "$input" | sed -nE 's/.*"worktree_path"[[:space:]]*:[[:space:]]*"([^"]*)".*/\1/p' | sed 's#\\\\#/#g')
[ -d "$dir" ] || exit 0

# Uncommitted work, ignoring the .slnx Unity writes beside the project.
if git -C "$dir" status --porcelain | grep -v '\.slnx$' | grep -q .; then
  echo "unity-worktrees: kept $dir, it has uncommitted changes." >&2
  exit 1
fi

case "$dir" in
  *.wt/*) UNITY_NO_PAGER=1 UNITY_NO_CRASH_REPORT=1 UNITY_NO_CLI_INVOKED_TELEMETRY=1 \
            unity vcs git worktree remove "$dir" --discard-changes -y --non-interactive --no-banner >&2 && exit 0 ;;
esac
git worktree remove --force "$dir" >&2
