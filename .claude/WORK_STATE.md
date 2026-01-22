# Work State

**Last updated:** 2025-01-22 (evening)
**Session:** Phases 1-4 complete. Stenographer working with Qwen 72B.

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

### Phase 4: Feedback Commands (Completed)

| Step | Status | Notes |
|------|--------|-------|
| Create log-useful.sh | ✅ Done | Appends to WE.md "Valuable Tangents" |
| Create log-wrong.sh | ✅ Done | Appends to SELF.md "Failures I've demonstrated" |
| Test both scripts | ✅ Done | Verified correct insertion |

**Note:** Scripts are callable directly. No artifact file loading required.

### Phase 3: Stenographer (Completed)

| Step | Status | Notes |
|------|--------|-------|
| Discover session files | ✅ Done | ~/.claude/projects/<project>/<session>.jsonl |
| Create extract-transcript.sh | ✅ Done | Parses JSONL, outputs user/assistant conversation |
| Create stenographer.sh | ✅ Done | Uses Qwen 72B with tuned prompt |
| Pull Qwen 72B | ✅ Done | 47GB model loaded |
| Test with Qwen | ✅ Done | Clean structured output with simplified prompt |

**Model decision:** Qwen2.5 72B chosen for long-context handling and structured output. Larger model now → better training data → fine-tune smaller model later.

### Phases 5, 6 — NOT STARTED

---

## What Changed This Session

### Previous session:
1. Cloned claude-sidekick to `~/Development/claude-sidekick`
2. Built it with `npm install && npm run build`
3. Added mcpServers config to `~/.claude/settings.json` (wrong location)
4. Created `~/.claude/scripts/load-we-frame.sh`
5. Added SessionStart hook to `~/.claude/settings.json`

### Previous session (Jan 22 morning):
1. Verified WE.md frame loading works ✅
2. Discovered sidekick MCP not loading — not in /mcp list
3. Found root cause: MCP servers go in `~/.claude.json`, not `~/.claude/settings.json`
4. Also needed `"type": "stdio"` field in config
5. Fixed via CLI: `claude mcp add --transport stdio sidekick -- node /Users/toddmarshall/Development/claude-sidekick/dist/index.js`
6. Config now correctly in `~/.claude.json` under project scope

### This session:
1. Loaded WORK_STATE.md — confirmed sidekick MCP now shows tools
2. Tested `ollama_list_models` ✅ — sees mistral:7b-instruct, gemma-3-27b, gpt-oss:20b
3. Tested `ollama_chat` ✅ — Mistral responded correctly
4. **Phase 1 complete**
5. Symlinked SELF.md, TODD.md, WE.md to ~/.claude/
6. Created ~/.claude/scripts/memory-server.sh
7. Tested memory queries — both passed
8. **Phase 2 complete**
9. Created log-useful.sh and log-wrong.sh (append-only, no file reads)
10. Tested both scripts — entries inserted correctly
11. **Phase 4 complete**
12. Discovered Claude Code stores full transcripts in ~/.claude/projects/
13. Created extract-transcript.sh — parses session JSONL
14. Created stenographer.sh — feeds transcript to Mistral
15. Tested pipeline — works, output quality needs tuning
16. **Phase 3 core complete**
17. Discussed fine-tuning strategy: large model (Qwen 72B) generates quality data now, fine-tune small model later
18. Evaluated models: DeepSeek R1 (reasoning overhead unnecessary), Llama 3.3 (safe default), Qwen (best for structured extraction + long context)
19. Decided on Qwen2.5 72B — pulling now (~47GB)
20. Updated stenographer.sh to use Qwen (with env var override)
21. Discussed cross-session summarization — high value, low effort to add later
22. Pulled Qwen 72B (~47GB)
23. Tested stenographer with Qwen — initial prompt too verbose
24. Tuned prompt — simpler "Output ONLY these sections" works well
25. **Phase 3 complete**

---

## Next Actions

1. **Add cross-session support** — Summarize multiple sessions together
2. **Add update-state.sh** — Merge stenographer output into WORK_STATE.md
3. **Create /stenographer skill** — Invoke via command
4. **Phase 5** — Fine-tuning prep (accumulate quality data first)

---

## Files Modified

- `~/.claude/settings.json` — Has hooks config (mcpServers entry there is ignored)
- `~/.claude.json` — Now has correct sidekick MCP config for claude-collaboration project
- `~/.claude/scripts/load-we-frame.sh` — Created (previous session)
- `~/.claude/SELF.md` — Symlink → ./artifacts/SELF.md
- `~/.claude/TODD.md` — Symlink → ./artifacts/TODD.md
- `~/.claude/WE.md` — Symlink → ./artifacts/WE.md
- `~/.claude/scripts/memory-server.sh` — Memory query script (this session)
- `~/.claude/scripts/log-useful.sh` — Append to WE.md (this session)
- `~/.claude/scripts/log-wrong.sh` — Append to SELF.md (this session)
- `~/.claude/scripts/extract-transcript.sh` — Parse session JSONL (this session)
- `~/.claude/scripts/stenographer.sh` — Summarize transcript via Mistral (this session)

---

## Key Discovery

**MCP server config location matters:**
- `~/.claude/settings.json` → permissions, hooks, plugins (NOT mcpServers)
- `~/.claude.json` → mcpServers (project-scoped under `projects.<path>.mcpServers`)
- `.mcp.json` in project root → team-shared MCP servers

**CLI is cleanest approach:** `claude mcp add --transport stdio <name> -- <command> [args]`

**Session transcripts already exist:**
- Location: `~/.claude/projects/<project-path-with-dashes>/<session-id>.jsonl`
- Contains: user messages, assistant responses, tool calls, thinking, progress events
- Format: JSONL with `type` field (user, assistant, progress, etc.)
- No capture needed — just parse existing files

**Fine-tuning strategy (decided this session):**
- Use large model (Qwen 72B) now for high-quality extraction
- Accumulate quality summaries as training data
- Later: fine-tune small model (Mistral 7B) on accumulated data
- Result: fast, personalized model that learned from quality examples

**Model evaluation:**
- DeepSeek R1: reasoning overhead unnecessary for summarization
- Llama 3.3 70B: safe default, but no specific advantage
- Qwen2.5 72B: ✅ chosen — best at structured output + long context
