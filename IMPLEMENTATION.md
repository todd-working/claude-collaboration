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
ollama pull mistral:7b-instruct  # fast, for memory queries
ollama pull qwen2.5:72b          # transcript analysis (47GB, needs 128GB RAM)
```

Keep Qwen loaded to avoid cold starts:
```bash
ollama run qwen2.5:72b --keepalive 24h
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

## Phase 3: Automated State (Stenographer + Insight Extractor)

Session transcripts are stored at:
```
~/.claude/projects/-Users-<username>-<path-with-dashes>/<session-id>.jsonl
```

### Step 3.1: Extract transcript

`~/.claude/scripts/extract-transcript.sh` parses the JSONL and outputs user/assistant conversation.

### Step 3.2: Stenographer (state extraction)

`~/.claude/scripts/stenographer.sh` extracts structured state:
- Current Task
- Completed
- Decisions
- Open Questions
- Files Modified
- Next Actions

**Usage:**
```bash
~/.claude/scripts/stenographer.sh <session-id> [project-path]
```

### Step 3.3: Insight Extractor (failure/pattern analysis)

`~/.claude/scripts/insight-extractor.sh` extracts deep insights:
- What Claude did wrong/right
- What Todd did wrong/right
- Collaboration dynamics
- Session-specific learnings
- SIGNAL.md entries (structured training data)

**Usage:**
```bash
~/.claude/scripts/insight-extractor.sh <session-id> [project-path]
```

**Environment variables:**
- `INSIGHT_MODEL` / `STENOGRAPHER_MODEL` — default: `qwen2.5:72b`
- `INSIGHT_CTX` / `STENOGRAPHER_CTX` — default: `32768`

### Key Implementation Detail

**Instructions must come AFTER the transcript.** Models weight recent text more heavily. Putting analysis instructions before the transcript causes the model to role-play as Claude instead of analyzing.

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
[x] Ollama installed and running
[x] Mistral-7B pulled (for memory queries)
[x] Qwen 72B pulled (for transcript analysis)
[x] claude-sidekick installed
[x] SessionStart hook loading WE.md
[x] Memory script working
[x] Stenographer script working
[x] Insight extractor script working
[x] Log scripts (log-useful.sh, log-wrong.sh) working
```

**Current state:** Phases 1-4 complete. Ready for Phase 5 (fine-tuning prep).
