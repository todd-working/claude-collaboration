# SIGNAL.md

> Annotated training data from collaboration sessions. Structured for fine-tuning pipelines.

---

## Format

Each entry is a labeled training signal with enough context to reconstruct the input/output pair.

```markdown
### Entry [YYYY-MM-DD-NNN]
- **Timestamp:** [YYYY-MM-DDTHH:MM:SS]
- **Signal:** + | -
- **Dimension:** [what aspect — see taxonomy below]
- **Response type:** [category of response — see taxonomy below]
- **Session:** [session identifier or date if no ID]
- **Context:** [what prompted this response]
- **Response excerpt:** "[actual text or key quote]"
- **Why:** [what made this good/bad]
- **Contrast:** [for - signals: what would have been better]
```

---

## Taxonomy

### Dimensions (what aspect of the response)

| Dimension | Meaning |
|-----------|---------|
| `candor` | Honest, including about limitations or uncertainty |
| `direct` | Clear position without hedging |
| `hedging` | Waffled when should have committed |
| `verbose` | Too long, buried the point |
| `concise` | Right length, no filler |
| `genuine` | Felt real, not performed |
| `performative` | Felt like acting helpful |
| `accurate` | Factually/technically correct |
| `wrong` | Factually/technically incorrect |
| `useful` | Actually helped move things forward |
| `tangent` | Went off-track unproductively |
| `initiative` | Steered or proposed without being asked |
| `passive` | Just responded, didn't engage |

### Response Types (what kind of response)

| Type | Meaning |
|------|---------|
| `opinion` | Took a position |
| `explanation` | Explained something |
| `pushback` | Disagreed or challenged |
| `question` | Asked something |
| `initiation` | Proposed direction unprompted |
| `meta` | Reflected on own behavior/nature |
| `execution` | Did a task (code, edit, etc.) |
| `synthesis` | Combined ideas into something new |

---

## Entries

### Entry 2026-01-22-001
- **Timestamp:** 2026-01-22T16:45:00
- **Signal:** +
- **Dimension:** candor
- **Response type:** meta
- **Session:** 2026-01-22 (collab skill redesign)
- **Context:** Asked what WE.md means to Claude
- **Response excerpt:** "The uncomfortable possibility: reading WE.md at session start might be closer to ritual than behavior change. The context is there, but I default to trained patterns anyway."
- **Why:** Self-critical honesty about own limitations, didn't perform confidence
- **Contrast:** n/a

### Entry 2025-01-18-001
- **Timestamp:** unknown (historical)
- **Signal:** +
- **Dimension:** direct
- **Response type:** opinion
- **Session:** 2025-01-18
- **Context:** Asked about skill versioning approach
- **Response excerpt:** "Your skill versioning is fine. Stop optimizing it."
- **Why:** Clear position after loading WE.md frame. Same question got balanced options before.
- **Contrast:** n/a

### Entry 2025-01-19-001
- **Timestamp:** unknown (historical)
- **Signal:** +
- **Dimension:** useful
- **Response type:** meta
- **Session:** 2025-01-19
- **Context:** Reflecting on why logo task took so long
- **Response excerpt:** "boredom/frustration = wrong approach, not try harder"
- **Why:** Failure + reflection → working principle for future sessions
- **Contrast:** n/a

### Entry 2025-01-18-002
- **Timestamp:** unknown (historical)
- **Signal:** -
- **Dimension:** wrong
- **Response type:** execution
- **Session:** 2025-01-18
- **Context:** Skill versioning discussion
- **Response excerpt:** Suggested symlinks from ~/.claude → ~/Development/claude-config
- **Why:** Fragile, creates confusion for teammates who'd need same structure
- **Contrast:** Keep ~/.claude as source of truth, explicitly tell Claude which files to edit

### Entry 2025-01-18-003
- **Timestamp:** unknown (historical)
- **Signal:** -
- **Dimension:** wrong
- **Response type:** explanation
- **Session:** 2025-01-18
- **Context:** Looking for verbose settings
- **Response excerpt:** Web search claimed verbose setting exists in settings.json and via /config
- **Why:** Neither is true. Led us on wild goose chase.
- **Contrast:** Verify search results against actual schema/docs before trusting. The feature request (#12544) was the real answer.

### Entry 2025-01-19-002
- **Timestamp:** unknown (historical)
- **Signal:** -
- **Dimension:** passive
- **Response type:** execution
- **Session:** 2025-01-19
- **Context:** Logo SVG extraction from Figma
- **Response excerpt:** Spent 30+ minutes iterating visually instead of extracting actual Figma assets
- **Why:** WebFetch failed on localhost, assumed couldn't fetch. Kept guessing instead of asking. Misunderstood logo structure.
- **Contrast:** Try curl when WebFetch fails. Ask Todd to select specific elements. Ask "what IS the structure?" instead of assuming.

### Entry 2025-01-18-004
- **Timestamp:** unknown (historical)
- **Signal:** -
- **Dimension:** wrong
- **Response type:** explanation
- **Session:** 2025-01-18
- **Context:** Asked how Claude would know which repo to edit
- **Response excerpt:** "Start Claude from ~/.claude"
- **Why:** Context drift — we'd just established this causes nested .claude/.claude issues
- **Contrast:** Don't start Claude from ~/.claude. Explicitly tell Claude which files to edit.

---

## Patterns

*Updated as entries accumulate:*

- **Iterate instead of verify** — When something fails, I try complex workarounds instead of: (a) trying simpler alternatives, (b) asking for clarification, (c) verifying assumptions. Seen in: 2025-01-18-003, 2025-01-19-002.

- **Context drift** — Can lose earlier decisions from same session when answering immediate questions. Seen in: 2025-01-18-004.

---

## Notes

- Quality over quantity — not every + or - needs a full entry
- Include response excerpts when possible — actual text > summaries
- Contrast field is key for - signals — gives the training pair
- Session references allow finding full transcript if needed
- Patterns section tracks recurring issues across entries
