# Escapes — poker-coach

| ID | Found | Defect | Path | Commits | Category | Question that should have caught it | Asked? | Promoted to |
|----|-------|--------|------|---------|----------|-------------------------------------|--------|-------------|
| E1 | 2026-09-25, by the blind review of the project owner's 200 hands | a straight or better the board makes alone is classed as a monster | reviewed | `7718c0d` (PR #30) → fix: `PR #244` | logic bug | does the hand class credit the bot for cards that play for everyone? | no | the unit tests in `backend/tests/test_board_made_hands.py` |
