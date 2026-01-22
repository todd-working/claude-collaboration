# Work State

**Last updated:** 2026-01-22 (late evening)
**Session:** Insight extractor added. Context size bug fixed.

---

## Current Progress

### Phase 1: Foundation (Completed)

| Step | Status | Notes |
|------|--------|-------|
| Install Ollama | ✅ Done | v0.14.3, running |
| Pull Mistral-7B | ✅ Done | mistral:7b-instruct (4.4GB) |
| Install claude-sidekick | ✅ Done | ~/Development/claude-sidekick |
| Configure MCP server | ✅ Fixed | Was in wrong file; used CLI to add correctly |
| Create SessionStart hook | ✅ Done | ~/.claude/scripts/load-we-frame.sh |
| Test WE.md frame loading | ✅ Working | Frame appears in session start |
| **Test sidekick tools** | ✅ Done | ollama_list_models, ollama_chat both working |

### Phase 2: Memory Layer (Completed)

| Step | Status | Notes |
|------|--------|-------|
| Symlink artifacts to ~/.claude/ | ✅ Done | SELF.md, TODD.md, WE.md |
| Create memory-server.sh | ✅ Done | ~/.claude/scripts/memory-server.sh |
| Test memory queries | ✅ Done | Both test queries returned accurate answers |
| Add ask_memory MCP tool | ⏭️ Skipped | Can use sidekick's ollama_chat directly |

### Phase 3: Stenographer (Completed)

| Step | Status | Notes |
|------|--------|-------|
| Discover session files | ✅ Done | ~/.claude/projects/<project>/<session>.jsonl |
| Create extract-transcript.sh | ✅ Done | Parses JSONL, outputs user/assistant conversation |
| Create stenographer.sh | ✅ Done | Uses Qwen 72B, 32K context via API |
| Create insight-extractor.sh | ✅ Done | Harsh prompt for failures/patterns |
| Pull Qwen 72B | ✅ Done | 47GB, keep loaded with --keepalive 24h |
| Fix context size | ✅ Done | Default 4096 was truncating; now uses 32K |

### Phase 4: Feedback Commands (Completed)

| Step | Status | Notes |
|------|--------|-------|
| Create log-useful.sh | ✅ Done | Appends to WE.md "Valuable Tangents" |
| Create log-wrong.sh | ✅ Done | Appends to SELF.md "Failures I've demonstrated" |
| Test both scripts | ✅ Done | Verified correct insertion |

### Phases 5, 6 — NOT STARTED

---

## What Changed This Session

### This session (continuation):
1. Committed Phases 1-4 to both repos (v0.2.0)
2. Ran stenographer — showed output is facts, not insights
3. Todd asked "where are the insights?" — identified gap
4. Created insight-extractor.sh with harsh prompt for failures/patterns
5. Iterated on prompt: generic → specific quotes → harsh criticism
6. **Major bug found:** Default 4096 context was truncating 2000+ line transcripts to ~5%
7. Spent 20 min tuning prompts without checking if model saw full input
8. Logged failure to SELF.md via log-wrong.sh
9. Fixed scripts to use Ollama API with num_ctx=32768
10. Tested insight-extractor with full context — works correctly
11. Committed fix (PR #9)

---

## Next Actions

1. **Add cross-session support** — Summarize multiple sessions together
2. **Add update-state.sh** — Merge stenographer output into WORK_STATE.md
3. **Create /stenographer skill** — Invoke via command
4. **Phase 5** — Fine-tuning prep (accumulate quality data first)

---

## Files Modified

- `~/.claude/scripts/stenographer.sh` — Now uses API with 32K context
- `~/.claude/scripts/insight-extractor.sh` — New, extracts failures/patterns
- `~/.claude/SELF.md` — Logged context size failure

---

## Key Discoveries

**Context size matters:**
- Ollama default context is 4096 tokens
- 2000+ line transcript needs ~60K-80K tokens
- Default was truncating input to ~5%
- Fix: Use API with `num_ctx: 32768` (or higher)
- `ollama run` doesn't support --ctx-size flag; must use API

**Qwen keepalive:**
- Model unloads after 5 min idle by default
- Keep loaded: `ollama run qwen2.5:72b --keepalive 24h`
- 128GB Mac can easily hold 47GB model in GPU

**Insight extraction vs state extraction:**
- Stenographer extracts facts: what happened, files changed, next actions
- Insight extractor finds failures: where Claude was wrong, wasted time, user had to repeat
- Different prompts for different purposes

**Failure logged:**
- Spent 20 min tuning prompts without verifying model could see full input
- Optimized the wrong thing
- Lesson: Check system works before tuning it
