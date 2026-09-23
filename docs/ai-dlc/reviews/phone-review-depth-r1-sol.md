# Codex Sol review, round 1 — NOT RUN (sandbox), 2026-09-22

`codex exec -m gpt-5.6-sol` exited 1 before reading the spec: "failed to initialize in-process
app-server client: Operation not permitted (os error 1)". That is the nested-Seatbelt EPERM the
sandbox produces for every Codex launch here (see `~/.claude/references/codex.md`), not an auth
failure — `~/.codex/auth.json` exists and was copied. Per the fail-open rule the round proceeded with
the Claude `refuter` alone and is labelled same-family in the ledger. A cross-family pass needs a plain
terminal: run the recipe in `~/.claude/skills/ai-org/reference/REGISTRY.md` against
`docs/ai-dlc/specs/phone-review-depth.md` and adjudicate its findings into the ledger as a new round.
