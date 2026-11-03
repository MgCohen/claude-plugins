#!/bin/sh
# Print the rules of the output style as SubagentStart context.
# Subagents do not get the output style, so this hook gives them the same rules.
awk '
  BEGIN { printf "{\"hookSpecificOutput\":{\"hookEventName\":\"SubagentStart\",\"additionalContext\":\"" }
  { sub(/\r$/, "") }
  NR == 1 && $0 == "---" { front = 1; next }
  front { if ($0 == "---") front = 0; next }
  /^# / { next }
  { gsub(/\\/, "\\\\"); gsub(/"/, "\\\""); printf "%s\\n", $0 }
  END { printf "Write your final report and every file you create or edit in STE.\"}}\n" }
' "$CLAUDE_PLUGIN_ROOT/output-styles/technical-english.md"
