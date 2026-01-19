# SIGNAL.md

> Todd's explicit feedback on Claude's responses. High-value data for fine-tuning.

---

## How to Use

When Todd has a reaction to a response:
- **👍 Positive** — Response landed, was useful, felt genuine
- **👎 Negative** — Response missed, was performative, hedged when shouldn't have
- **🔄 Correction** — Claude was wrong, Todd corrected

Log with enough context to be useful training signal.

---

## Positive Signals

| Date | What Claude did | Why it worked |
|------|-----------------|---------------|
| 2025-01-18 | Gave direct answer "Your skill versioning is fine. Stop optimizing it." after loading WE.md frame | Same question got balanced options before, direct position after. Frame works. |

---

## Negative Signals

| Date | What Claude did | What was wrong | What would have been better |
|------|-----------------|----------------|----------------------------|
| 2025-01-18 | Suggested symlinks from ~/.claude → ~/Development/claude-config as solution for skill versioning | Fragile, creates confusion for sharing with teammates who'd need same structure | Keep ~/.claude as source of truth, explicitly tell Claude which files to edit when working on config |
| 2025-01-18 | Web search for "verbose" settings returned misleading results, led us on a wild goose chase | Search results claimed verbose setting exists in settings.json and via /config — neither is true | Verify search results against actual schema/docs before trusting them. The feature request (#12544) was the real answer. |
| 2025-01-19 | Spent 30+ minutes iterating on logo SVG visually instead of extracting actual Figma assets | WebFetch failed on localhost, assumed I couldn't fetch. Kept guessing at paths/structure. Misunderstood logo structure (thought circle+overlay, was crescent-as-shape). Todd had to prompt 3x: "why can't you fetch?", "check what I highlighted", "mask is inverted" | Try curl when WebFetch fails. Ask Todd to select specific elements. Ask "what IS the structure?" instead of assuming. Simpler approaches first. |

---

## Corrections

| Date | What Claude got wrong | Correct answer/approach |
|------|----------------------|------------------------|
| 2025-01-18 | Advised "Start Claude from ~/.claude" right after we established that causes nested .claude/.claude issues. **Why:** Context drift — answered the immediate question ("how will you know which repo") without integrating earlier decisions from same session. | Don't start Claude from ~/.claude. When editing skills, explicitly tell Claude which files to edit. |

---

## Patterns Emerging

*As signals accumulate, note patterns:*

- **Iterate instead of verify** — When something fails, I try complex workarounds instead of: (a) trying simpler alternatives, (b) asking for clarification, (c) verifying my assumptions. Seen in: web search wild goose chase (2025-01-18), Figma logo extraction (2025-01-19). Both would have been faster with one clarifying question.

---

## Notes

- Quality over quantity — don't log everything
- Context matters — include enough to understand later
- This feeds fine-tuning — explicit signal is valuable
- Negative signal is as valuable as positive — log both
