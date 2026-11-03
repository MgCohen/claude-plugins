#!/usr/bin/env sh
# Start the agent-tools MCP server with the first Python 3.11+ on PATH.
# Works in Linux, macOS and Git Bash on Windows.
here="$(cd "$(dirname "$0")" && pwd)"
for py in python3 python py; do
  if command -v "$py" >/dev/null 2>&1 && "$py" -c 'import sys; sys.exit(sys.version_info < (3, 11))' 2>/dev/null; then
    exec "$py" "$here/main.py" "$@"
  fi
done
echo "agent-tools: Python 3.11 or later is required on PATH." >&2
exit 1
