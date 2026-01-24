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

### Entry 2026-01-22-002
- **Timestamp:** 2026-01-22T18:23:00
- **Signal:** +
- **Dimension:** useful
- **Response type:** execution
- **Session:** 2026-01-22 (collab skill redesign)
- **Context:** Helping Todd with time tracking for ADHD/time blindness
- **Response excerpt:** Built time awareness system: session start hook, triggers at natural checkpoints, late-night reminders. Non-judgmental framing.
- **Why:** Non-judgmental support for a real need. Practical solution. Didn't lecture.
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

### Entry 2025-01-22-001
- **Timestamp:** 2025-01-22
- **Signal:** -
- **Dimension:** wrong
- **Response type:** explanation
- **Session:** carmacircle-poc auth debugging
- **Context:** Claude prematurely declared the stale JWT issue fixed without thorough testing
- **Response excerpt:** "Stale JWT now returns 401. Let me verify valid JWTs still work."
- **Why:** Premature declarations waste time and erode trust
- **Contrast:** Thoroughly test all edge cases and variants before declaring fix complete

### Entry 2025-01-22-002
- **Timestamp:** 2025-01-22
- **Signal:** -
- **Dimension:** wrong
- **Response type:** execution
- **Session:** carmacircle-poc auth debugging
- **Context:** Claude assumed the user ID in the JWT was correct without verifying against database
- **Response excerpt:** "The API logs showed `u:574de884...` but that user doesn't exist anymore."
- **Why:** Over-reliance on assumptions without verification led to extended debugging
- **Contrast:** Immediately check if user ID in JWT exists in database when behavior is unexpected

### Entry 2025-01-22-003
- **Timestamp:** 2025-01-22
- **Signal:** +
- **Dimension:** useful
- **Response type:** explanation
- **Session:** carmacircle-poc auth debugging
- **Context:** Todd clearly identified the issue was a UX problem
- **Response excerpt:** "that's a UX issue, but I'm glad we tracked it down"
- **Why:** Clear feedback helped focus on the right problem and provided direction

### Entry 2025-01-22-004
- **Timestamp:** 2025-01-22
- **Signal:** +
- **Dimension:** accurate
- **Response type:** execution
- **Session:** carmacircle-poc auth debugging
- **Context:** Claude provided detailed commit message explaining the bug and fix
- **Response excerpt:** "Stale JWT (non-existent user_id `574de884-...`) → 401, Valid JWT (existing user_id `c8d00646-...`) → 200"
- **Why:** Detailed commit messages help future maintenance and understanding

### Entry 2025-01-22-005
- **Timestamp:** 2025-01-22
- **Signal:** +
- **Dimension:** genuine
- **Response type:** pushback
- **Session:** carmacircle-poc auth debugging
- **Context:** Todd corrected Claude's assumption about the code being shippable
- **Response excerpt:** "it's not actually shippable"
- **Why:** Clear and honest feedback ensures correct actions are taken

---

## Patterns

*Updated as entries accumulate:*

- **Iterate instead of verify** — When something fails, I try complex workarounds instead of: (a) trying simpler alternatives, (b) asking for clarification, (c) verifying assumptions. Seen in: 2025-01-18-003, 2025-01-19-002.

- **Context drift** — Can lose earlier decisions from same session when answering immediate questions. Seen in: 2025-01-18-004.

- **Premature "fixed" declarations** — Declare issues fixed before testing all variants/paths. Seen in: 2025-01-22-001, 2025-01-22-002.

---

## Notes

- Quality over quantity — not every + or - needs a full entry
- Include response excerpts when possible — actual text > summaries
- Contrast field is key for - signals — gives the training pair
- Session references allow finding full transcript if needed
- Patterns section tracks recurring issues across entries

### Entry 2026-01-23T15:17:00
- **Signal:** +
- **Dimension:** reasoning
- **Response type:** pushback
- **Session:** 2026-01-23 (collab/session optimization)
- **Context:** Todd proposed retroactive session typing
- **Response excerpt:** "It's clever but it's polishing a feature that might not need to exist... Prompting at session end is friction in the wrong place. With ADHD, that's the moment you want to close the laptop."
- **Why:** Honest pushback that considered Todd's ADHD, questioned whether data would be used, recommended killing the feature

### Entry 2026-01-23T15:45:00
- **Signal:** +
- **Dimension:** alignment
- **Response type:** explanation
- **Session:** 2026-01-23 (collab/session optimization)
- **Context:** Asked to order design questions
- **Response excerpt:** "Start with minimum viable state — this constrains everything else"
- **Why:** Matched Todd's mental priority order without being told, started from first principles
