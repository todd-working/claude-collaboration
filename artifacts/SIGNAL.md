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

---

## Corrections

| Date | What Claude got wrong | Correct answer/approach |
|------|----------------------|------------------------|
| 2025-01-18 | Advised "Start Claude from ~/.claude" right after we established that causes nested .claude/.claude issues. **Why:** Context drift — answered the immediate question ("how will you know which repo") without integrating earlier decisions from same session. | Don't start Claude from ~/.claude. When editing skills, explicitly tell Claude which files to edit. |

---

## Patterns Emerging

*As signals accumulate, note patterns:*

- (none yet)

---

## Notes

- Quality over quantity — don't log everything
- Context matters — include enough to understand later
- This feeds fine-tuning — explicit signal is valuable
- Negative signal is as valuable as positive — log both
