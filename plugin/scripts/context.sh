#!/bin/sh
# Prints context files as hook JSON: context.sh <HookEvent> [--r-only] <file>...
# --r-only prints nothing unless the session started in an R package.
event=$1; shift
if [ "$1" = "--r-only" ]; then
  shift
  [ -f "${CLAUDE_PROJECT_DIR:-.}/DESCRIPTION" ] || exit 0
fi
awk -v ev="$event" '
  BEGIN { printf "{\"hookSpecificOutput\":{\"hookEventName\":\"%s\",\"additionalContext\":\"", ev }
  { gsub(/\r/, ""); gsub(/\\/, "\\\\"); gsub(/"/, "\\\""); gsub(/\t/, "\\t"); printf "%s\\n", $0 }
  END { printf "\"}}" }
' "$@"
