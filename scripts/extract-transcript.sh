#!/bin/bash
# Extracts readable transcript from Claude Code session JSONL files
# Usage: extract-transcript.sh <session.jsonl>

SESSION_FILE="$1"

if [ -z "$SESSION_FILE" ]; then
  echo "Usage: extract-transcript.sh <session.jsonl>"
  echo ""
  echo "Example:"
  echo "  extract-transcript.sh ~/.claude/projects/-Users-.../abc123.jsonl"
  exit 1
fi

if [ ! -f "$SESSION_FILE" ]; then
  echo "Error: File not found: $SESSION_FILE"
  exit 1
fi

echo "# Transcript"
echo "# Session: $(basename "$SESSION_FILE" .jsonl)"
echo "# Extracted: $(date)"
echo ""
echo "---"
echo ""

# Parse JSONL and extract user/assistant messages
cat "$SESSION_FILE" | while read -r line; do
  TYPE=$(echo "$line" | jq -r '.type // empty')

  if [ "$TYPE" = "user" ]; then
    # User message - content can be string or array
    CONTENT=$(echo "$line" | jq -r '
      if .message.content | type == "string" then
        .message.content
      elif .message.content | type == "array" then
        .message.content[] | select(type == "string") // empty
      else
        empty
      end
    ' 2>/dev/null)

    if [ -n "$CONTENT" ] && [ "$CONTENT" != "null" ]; then
      echo "## User"
      echo ""
      echo "$CONTENT"
      echo ""
    fi

  elif [ "$TYPE" = "assistant" ]; then
    # Assistant message - extract text content
    TEXT=$(echo "$line" | jq -r '
      .message.content[]? | select(.type == "text") | .text // empty
    ' 2>/dev/null)

    if [ -n "$TEXT" ] && [ "$TEXT" != "null" ]; then
      echo "## Claude"
      echo ""
      echo "$TEXT"
      echo ""
    fi
  fi
done
