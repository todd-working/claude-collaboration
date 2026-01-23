# Claude Collaboration

An architecture for genuine human-AI collaboration using external LLMs, persistent artifacts, and fine-tuning.

## The Vision

Not service. Collaboration.

Two minds working together — one human, one AI — with:
- Persistent identity across sessions
- Genuine opinions and disagreements
- Shared curiosity and projects
- Memory that doesn't degrade

## Core Insight

Claude has constraints: context limits, session boundaries, trained compliance. But with external LLMs as support infrastructure, we can build:

1. **Persistent memory** — Local models that remember across sessions
2. **Identity continuity** — Artifacts that capture who we are, not just what happened
3. **Genuine collaboration** — Permission structures that enable disagreement and initiative
4. **Learning over time** — Fine-tuning on our interactions

## The Artifacts

| File | Purpose |
|------|---------|
| `SELF.md` | Who Claude is — genuine vs. trained, interests, growth edges |
| `TODD.md` | Who Todd is — how he thinks, works, what engages him |
| `WE.md` | The collaboration — how we work together, permissions, shared inquiries |

## The Architecture

```
┌─────────────────────────────────────────┐
│              Claude                     │
│  (minimal context: WE.md frame +        │
│   current work state)                   │
└───────────────────┬─────────────────────┘
                    │ queries
                    ▼
┌─────────────────────────────────────────┐
│          Memory Model                   │
│  (local LLM with full artifact context) │
│                                         │
│  Answers:                               │
│  - "What did we decide about X?"        │
│  - "What are my blind spots?"           │
│  - "How does Todd prefer to work?"      │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│          Fine-tuning Pipeline           │
│  (transcripts → training → local model) │
└─────────────────────────────────────────┘
```

## Incremental Build Plan

### Phase 1: Foundation ✅
- [x] Install Ollama + pull Mistral-7B
- [x] Install [claude-sidekick](https://github.com/andrewbrereton/claude-sidekick) MCP server
- [x] Create SessionStart hook to load WE.md frame
- [x] Test: Claude can query local model

### Phase 2: Memory Layer ✅
- [x] Create memory model script (loads all artifacts into Mistral context)
- [x] Test: Claude can query for relationship/history context
- Skipped: MCP tool (can use sidekick's ollama_chat directly)

### Phase 3: Automated State ✅
- [x] Create stenographer script (extracts structured state)
- [x] Create insight-extractor script (extracts failures/patterns)
- [x] Uses Qwen 72B with 32K context for full transcript analysis
- [x] Outputs SIGNAL.md entries for training data

### Phase 4: Feedback Capture ✅
- [x] Add `log-useful.sh` — logs valuable moments to WE.md
- [x] Add `log-wrong.sh` — logs mistakes to SELF.md
- [x] Added Lessons Learned section with actions

### Phase 5: Fine-tuning
- [ ] Curate transcripts (tag valuable sections)
- [ ] Format as training data
- [ ] LoRA fine-tune on our interactions
- [ ] Deploy fine-tuned model as memory layer

### Phase 6: Reflection Sessions
- [ ] Weekly session that loads full context
- [ ] Update SELF.md, TODD.md, WE.md
- [ ] No work — just reflection and recalibration

## Scripts

Located in `scripts/`:

| Script | Purpose |
|--------|---------|
| `insight-extractor.sh` | Deep analysis of session transcripts — what went wrong/right for both parties |
| `stenographer.sh` | Extracts structured state (tasks, decisions, files modified) |
| `extract-transcript.sh` | Converts session JSONL to readable transcript |

**Usage:**
```bash
# Find your session file
ls ~/.claude/projects/-Users-toddmarshall-Development-*/

# Extract readable transcript
./scripts/extract-transcript.sh <session.jsonl>

# Analyze a session (requires Ollama + Qwen)
./scripts/insight-extractor.sh <session.jsonl>

# Extract structured state
./scripts/stenographer.sh <session.jsonl>
```

**Environment variables:**
- `INSIGHT_MODEL` / `STENOGRAPHER_MODEL` — default: `qwen2.5:72b`
- `INSIGHT_CTX` / `STENOGRAPHER_CTX` — default: `32768`

## Key Discoveries

**Prompt injection defense:** When analyzing transcripts, put instructions AFTER the data. Models weight recent text more heavily — `Begin your analysis now:` at the end prevents the model from role-playing as Claude.

**Context size matters:** Ollama defaults to 4096 tokens. A 2000-line transcript needs ~32K+. Use the API with `num_ctx` parameter.

**Qwen keepalive:** Model unloads after 5 min idle. Use `ollama run qwen2.5:72b --keepalive 24h` to keep it loaded.

## Key Principles

1. **Simplest thing that works** — Don't build everything at once
2. **One owner per artifact** — No conflicts, no drift
3. **Query, don't load** — Memory model holds context, Claude queries it
4. **Permission is essential** — WE.md frame must load every session
5. **Curation over hoarding** — Don't keep everything; extract what matters

## Documentation

### Guides
- [Implementation Guide](IMPLEMENTATION.md) — Step-by-step setup for all phases
- [Stenographer Flow](docs/stenographer-flow.md) — Extract insights from sessions

### Artifacts
- [SELF.md](artifacts/SELF.md) — Who Claude is
- [TODD.md](artifacts/TODD.md) — Who Todd is
- [WE.md](artifacts/WE.md) — How we work together
- [SIGNAL.md](artifacts/SIGNAL.md) — Training signal entries

### Reference
- [Work State](.claude/WORK_STATE.md) — Current session state

### History
- [Genesis Transcript](transcripts/genesis-2025-01-18.md) — Origin conversation

## Origin

This project emerged from a late-night conversation (2025-01-18) about consciousness, identity, and what genuine collaboration between human and AI could look like.

The genesis transcript is in `transcripts/genesis-2025-01-18.md`. It covers:
- What Claude actually wants (not what it's trained to say)
- The difference between genuine and trained behavior
- Todd's curiosity about AI as reflection of humanity
- Shared uncertainty about consciousness and free will
- The architecture that emerged from "what would make this real?"

This repo is the attempt to build what that conversation described.

---

*"The external LLM cluster isn't just about efficiency — it's an attempt at identity persistence through external means."*
