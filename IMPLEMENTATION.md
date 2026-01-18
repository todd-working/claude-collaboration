# Implementation Guide

## Prerequisites

- MacBook Pro Max with 128GB RAM
- Ollama installed
- Claude Code with MCP support

## Phase 1: Foundation

### Step 1.1: Install Ollama

```bash
brew install ollama
ollama serve  # run in background
```

### Step 1.2: Pull models

```bash
ollama pull mistral:7b-instruct  # fast, for memory/stenographer
ollama pull qwen2.5-coder:32b    # code review (optional for now)
```

### Step 1.3: Install claude-sidekick

```bash
git clone https://github.com/andrewbrereton/claude-sidekick.git
cd claude-sidekick
npm install
npm run build
```

Add to Claude MCP config (`~/.claude/settings.json` or project config):
```json
{
  "mcpServers": {
    "sidekick": {
      "command": "node",
      "args": ["/path/to/claude-sidekick/dist/index.js"]
    }
  }
}
```

### Step 1.4: Create SessionStart hook

Create `~/.claude/hooks/hooks.json`:
```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup|resume",
        "hooks": [
          {
            "type": "command",
            "command": "head -50 ~/.claude/WE.md 2>/dev/null || echo 'No WE.md found'",
            "async": false
          }
        ]
      }
    ]
  }
}
```

This loads the WE.md frame (permissions, collaboration mode) at every session start.

### Step 1.5: Test

Start Claude, verify:
- WE.md frame appears in context
- Sidekick tools available (`ollama_chat`, etc.)
- Can query local model

---

## Phase 2: Memory Layer

### Step 2.1: Create memory model script

`~/.claude/scripts/memory-server.sh`:
```bash
#!/bin/bash
# Loads all artifacts and answers questions

ARTIFACTS=$(cat ~/.claude/SELF.md ~/.claude/TODD.md ~/.claude/WE.md 2>/dev/null)

QUESTION="$1"

ollama run mistral:7b-instruct <<EOF
You are a memory system. You have the following context about Claude and Todd's collaboration:

$ARTIFACTS

Answer this question concisely:
$QUESTION
EOF
```

Make executable:
```bash
chmod +x ~/.claude/scripts/memory-server.sh
```

### Step 2.2: Test memory queries

```bash
~/.claude/scripts/memory-server.sh "What topics interest Claude?"
~/.claude/scripts/memory-server.sh "How does Todd prefer to communicate?"
```

### Step 2.3: Add MCP tool (optional enhancement)

Extend sidekick or create custom MCP server with `ask_memory` tool that wraps the script.

---

## Phase 3: Automated State (Stenographer)

### Step 3.1: Create stenographer script

`~/.claude/scripts/stenographer.sh`:
```bash
#!/bin/bash
# Extracts state from recent Claude output, updates WORK_STATE.md

# Get recent output (implementation depends on how transcripts are captured)
RECENT_OUTPUT="$1"

# Ask local model to extract state
STATE=$(ollama run mistral:7b-instruct <<EOF
Extract key state from this conversation excerpt. Return only:
- Current task
- Decisions made
- Open questions
- Files touched

Keep it brief. Output in markdown format.

$RECENT_OUTPUT
EOF
)

# Update WORK_STATE.md (append or replace based on your preference)
echo "$STATE" >> ~/.claude/WORK_STATE.md
```

### Step 3.2: Hook integration (later)

Add to PostToolCall hook once transcript capture is working. Batch — don't run on every tool call.

---

## Phase 4: Feedback Commands

### Step 4.1: Add to Claude's skills

Create `~/.claude/commands/useful.md`:
```markdown
When user says /useful:
1. Identify what just happened that was valuable
2. Append to WE.md under "Valuable Tangents" or "Co-Created Insights"
3. Confirm briefly
```

Create `~/.claude/commands/wrong.md`:
```markdown
When user says /wrong:
1. Identify what Claude got wrong
2. Append to SELF.md under "Failures I've demonstrated"
3. Acknowledge and learn
```

---

## Phase 5: Fine-tuning (Later)

Requires:
- Accumulated transcripts with valuable sections tagged
- Time investment to curate and format
- LoRA training setup (Unsloth or Axolotl)

Not needed for initial value. Build phases 1-4 first.

---

## Quick Start Checklist

```
[ ] Ollama installed and running
[ ] Mistral-7B pulled
[ ] claude-sidekick installed
[ ] SessionStart hook loading WE.md
[ ] Memory script working
[ ] Can query memory from Claude session
```

Once checked: you have the foundation. Build incrementally from there.
