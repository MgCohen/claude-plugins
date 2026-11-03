#!/usr/bin/env bash
# PreToolUse (Bash, PowerShell): deny `git worktree add` and `git -C <path> worktree add` when the
# target repo is a Unity project. A plain git worktree has no Library, so Unity imports from zero.
# `unity vcs git worktree add` seeds the Library. All other commands pass.
input=$(cat | tr -d '\r\n')
str() { printf '%s' "$input" | sed -nE "s/.*\"$1\"[[:space:]]*:[[:space:]]*\"((\\\\.|[^\"\\\\])*)\".*/\1/p"; }
cmd=$(str command | sed -e 's/\\"/"/g' -e 's/\\\\/\\/g')
cwd=$(str cwd | sed 's#\\\\#/#g')

# The Unity CLI command itself contains "git worktree add": hide it before the match.
plain=$(printf '%s' "$cmd" | sed -E 's/vcs[[:space:]]+git/vcs-git/g')
re='(^|[^[:alnum:]_.-])git(\.exe)?([[:space:]]+-C[[:space:]]+("[^"]*"|'"'"'[^'"'"']*'"'"'|[^[:space:]]+))?[[:space:]]+worktree[[:space:]]+add([[:space:]]|$)'
match=$(printf '%s' "$plain" | grep -oE "$re" | head -n 1)
[ -n "$match" ] || exit 0

# The repo: the -C path when there is one, else the session's cwd.
dir=$(printf '%s' "$match" | sed -nE 's/.*[[:space:]]-C[[:space:]]+("([^"]*)"|'"'"'([^'"'"']*)'"'"'|([^[:space:]]+)).*/\2\3\4/p' | sed 's#\\#/#g')
case "$dir" in
  "") dir=$cwd ;;
  /*|[A-Za-z]:*) ;;
  *) dir="$cwd/$dir" ;;
esac
root=$(git -C "$dir" rev-parse --path-format=absolute --git-common-dir 2>/dev/null) || exit 0
root=${root%/.git}
[ -f "$root/ProjectSettings/ProjectVersion.txt" ] ||
  git -C "$root" cat-file -e HEAD:ProjectSettings/ProjectVersion.txt 2>/dev/null || exit 0

reason="unity-worktrees: $root is a Unity project. Do not use git worktree add, and do not copy the Library. Use: unity vcs git worktree add <branch> <repo-root> --into <repo>.wt/<name> --seed cache --no-register -y --non-interactive"
printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"%s"}}\n' \
  "$(printf '%s' "$reason" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g')"
exit 0
