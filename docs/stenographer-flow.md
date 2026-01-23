# Stenographer Flow

How to extract insights and state from Claude Code sessions.

## Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Claude Code Session                       │
│                                                              │
│  User ←→ Claude (conversation stored as JSONL)              │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              ~/.claude/projects/<project>/                   │
│                    <session-id>.jsonl                        │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│               extract-transcript.sh                          │
│                                                              │
│  Parses JSONL → readable User:/Assistant: format            │
└─────────────────────┬───────────────────────────────────────┘
                      │
          ┌──────────┴──────────┐
          ▼                     ▼
┌─────────────────────┐  ┌─────────────────────┐
│   stenographer.sh   │  │ insight-extractor.sh│
│                     │  │                     │
│  Extracts STATE:    │  │  Extracts INSIGHTS: │
│  - Current task     │  │  - What went wrong  │
│  - Completed        │  │  - What went right  │
│  - Decisions        │  │  - Lessons learned  │
│  - Files modified   │  │  - SIGNAL.md entries│
│  - Next actions     │  │                     │
└─────────────────────┘  └─────────────────────┘
          │                     │
          ▼                     ▼
    WORK_STATE.md         WE.md, SIGNAL.md
```

## Finding Sessions

Sessions are stored at:
```
~/.claude/projects/-Users-<username>-<path-with-dashes>/<session-id>.jsonl
```

**List recent sessions for a project:**
```bash
ls -lt ~/.claude/projects/-Users-toddmarshall-Development-carmacircle-poc/*.jsonl | head -5
```

**Output:**
```
-rw------- 12399782 Jan 22 12:18 a1fb343d-b96b-4407-999d-df1561c57bb9.jsonl
-rw-------   690923 Jan 22 01:44 714387a8-20a5-40f1-a2f6-88201c90b9e6.jsonl
...
```

The session ID is the filename without `.jsonl`.

## Scripts

### extract-transcript.sh

Converts JSONL to readable transcript.

```bash
~/.claude/scripts/extract-transcript.sh <session-id> [project-path]
```

**Example:**
```bash
~/.claude/scripts/extract-transcript.sh a1fb343d ~/Development/carmacircle-poc
```

**Output:** Plain text with `User:` and `Assistant:` prefixes.

---

### stenographer.sh

Extracts structured state from a session.

```bash
~/.claude/scripts/stenographer.sh <session-id> [project-path]
```

**Output:**
```markdown
**Current Task:**
- Debugging auth flow

**Completed:**
- Fixed stale JWT issue
- Updated auth middleware

**Decisions:**
- Use database lookup to verify user exists

**Files Modified:**
- services/api/app/middleware/auth.py
- services/api/app/routes/vouches.py

**Next Actions:**
- Test with fresh JWTs
- Deploy to staging
```

**Use for:** Updating WORK_STATE.md, quick session summaries.

---

### insight-extractor.sh

Deep analysis of what went wrong/right for both parties.

```bash
~/.claude/scripts/insight-extractor.sh <session-id> [project-path]
```

**Output sections:**
1. What Claude Did Wrong
2. What Claude Did Right
3. What Todd Did Wrong
4. What Todd Did Right
5. Collaboration Dynamics
6. Session-Specific Learnings
7. SIGNAL.md Entries

**Use for:** Extracting lessons, generating training data, retrospectives.

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `INSIGHT_MODEL` | `qwen2.5:72b` | Model for insight extraction |
| `INSIGHT_CTX` | `32768` | Context window size |
| `STENOGRAPHER_MODEL` | `qwen2.5:72b` | Model for state extraction |
| `STENOGRAPHER_CTX` | `32768` | Context window size |

**Example with different model:**
```bash
INSIGHT_MODEL=qwen2.5:14b ~/.claude/scripts/insight-extractor.sh <session-id> <project>
```

---

## Typical Workflow

### End of session retrospective

```bash
# Find the current session
ls -lt ~/.claude/projects/-Users-toddmarshall-Development-<project>/*.jsonl | head -1

# Run insight extraction
~/.claude/scripts/insight-extractor.sh <session-id> ~/Development/<project>

# Review output, copy relevant entries to:
# - WE.md (Lessons Learned)
# - SIGNAL.md (training entries)
```

### Quick state capture

```bash
~/.claude/scripts/stenographer.sh <session-id> ~/Development/<project>

# Copy output to WORK_STATE.md
```

---

## Key Design Decisions

### Instructions after transcript

The prompt puts analysis instructions AFTER the transcript data:

```
[BEGIN TRANSCRIPT]
...2000 lines of conversation...
[END TRANSCRIPT]

Now analyze it. Begin analysis now:
```

**Why:** Models weight recent text more heavily. Putting instructions before the transcript causes the model to role-play as Claude instead of analyzing.

### Non-streaming output

Scripts use `"stream": false` in the Ollama API call.

**Why:** When run via Claude Code's Bash tool, streaming provides no benefit — output appears only after completion anyway. Non-streaming is simpler.

### 32K context default

Ollama defaults to 4096 tokens. A 2000-line transcript needs ~32K+ tokens.

**Why:** The default truncates transcripts to ~5%, making analysis useless. Always specify `num_ctx`.

---

## Troubleshooting

### "No session directory found"

Check the project path matches the session location:
```bash
ls ~/.claude/projects/ | grep <project-name>
```

### Output is empty or truncated

Model may not be loaded or context is too small:
```bash
# Check if Qwen is loaded
ollama ps

# Load with keepalive
ollama run qwen2.5:72b --keepalive 24h
```

### Model role-plays instead of analyzing

Instructions are probably before the transcript. Check the script — analysis instructions must come AFTER `[END TRANSCRIPT]`.
