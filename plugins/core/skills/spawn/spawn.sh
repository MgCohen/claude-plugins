#!/usr/bin/env sh
# Start a separate Claude Code session.
#
# Usage:
#   spawn.sh desktop    <name> <cwd> <permission-mode>
#   spawn.sh background <name> <cwd> <permission-mode> <brief-file>
#
# desktop:    makes the session with one short headless turn, then opens it in
#             the Claude desktop app. The desktop app owns the session, so it
#             keeps Remote Control connected. The caller turns Remote Control on
#             and sends the brief with the desktop session tools.
# background: runs the brief in a CLI background job with Remote Control on.
#             Remote Control stops when the job process stops, and nothing
#             connects it again. Use it only when the desktop tools are missing.
set -eu

kind="${1:-}"
name="${2:-}"
cwd="${3:-}"
mode="${4:-}"

if [ -z "$kind" ] || [ -z "$name" ] || [ -z "$cwd" ] || [ -z "$mode" ]; then
  echo "usage: spawn.sh desktop|background <name> <cwd> <permission-mode> [brief-file]" >&2
  exit 1
fi

case "$kind" in
  desktop|background) ;;
  *) echo "error: unknown kind: $kind (use desktop or background)" >&2; exit 1 ;;
esac

case "$mode" in
  default|acceptEdits|plan|auto|dontAsk) ;;
  *) echo "error: permission mode not allowed: $mode" >&2; exit 1 ;;
esac

cd "$cwd"

case "$kind" in
  desktop)
    if ! command -v powershell.exe >/dev/null 2>&1; then
      echo "error: desktop mode needs Windows (powershell.exe). Use background mode." >&2
      exit 1
    fi
    id=$(powershell.exe -NoProfile -Command "[guid]::NewGuid().ToString()" | tr -d '\r\n')
    first="This session was made by the core:spawn skill. The brief comes in the next message. Reply only: Ready."
    if ! claude -p --session-id "$id" -n "$name" --permission-mode "$mode" "$first" >/dev/null 2>&1; then
      echo "error: the first headless turn failed (is the folder trusted?)" >&2
      exit 1
    fi
    # `claude --desktop` refuses a shell without a terminal, so start it from PowerShell.
    wincwd=$(cygpath -w "$(pwd)" 2>/dev/null || pwd)
    powershell.exe -NoProfile -Command "Start-Process -FilePath claude -ArgumentList '--desktop','--resume','$id' -WorkingDirectory '$wincwd' -WindowStyle Hidden"
    echo "id: $id"
    echo "desktop session: local_$id"
    echo "name: $name"
    ;;

  background)
    brief="${5:-}"
    if [ ! -f "$brief" ]; then
      echo "error: brief file not found: $brief" >&2
      exit 1
    fi
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
    echo "desktop: claude --desktop --resume <full session id from claude agents --json>"
    ;;
esac
