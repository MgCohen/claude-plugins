#!/usr/bin/env sh
# Start a background Claude Code session with Remote Control on, then print its id and claude.ai link.
# Usage: spawn.sh <name> <cwd> <permission-mode> <brief-file>
set -eu

name="$1"
cwd="$2"
mode="$3"
brief="$4"

if [ ! -f "$brief" ]; then
  echo "error: brief file not found: $brief" >&2
  exit 1
fi

case "$mode" in
  default|acceptEdits|plan|auto|dontAsk) ;;
  *) echo "error: permission mode not allowed: $mode" >&2; exit 1 ;;
esac

cd "$cwd"
out=$(claude --bg --remote-control "$name" -n "$name" --permission-mode "$mode" "$(cat "$brief")" 2>&1)
id=$(printf '%s\n' "$out" | sed -n 's/.*backgrounded · \([0-9a-f]*\) ·.*/\1/p' | head -n 1)

if [ -z "$id" ]; then
  echo "error: session did not start" >&2
  printf '%s\n' "$out" >&2
  exit 1
fi

# The Remote Control link shows in the session output after a few seconds.
link=""
i=0
while [ -z "$link" ] && [ "$i" -lt 30 ]; do
  sleep 2
  i=$((i + 2))
  link=$(claude logs "$id" 2>/dev/null | grep -o 'https://claude.ai/code/session_[A-Za-z0-9]*' | head -n 1 || true)
done

echo "id: $id"
echo "name: $name"
echo "link: ${link:-not found yet; run: claude logs $id}"
echo "attach: claude attach $id"
echo "desktop: claude --desktop --resume $id"
