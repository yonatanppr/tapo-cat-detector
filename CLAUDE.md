## Writing

Write docs, comments, and commit messages short and plain. Only write prose when a reader needs it: don't add READMEs, summaries, or design notes nobody asked for. Code comments say why, not what. `scripts/prose_guard.py` blocks common AI-writing tells and markdown files over 200 lines. It runs after every Claude edit and in the git `pre-commit` and `commit-msg` hooks. When it fires, rewrite the text (the `humanizer` skill helps); don't just swap words. After cloning, enable the git hooks with `git config core.hooksPath .githooks`.

## Agent skills

### Issue tracker

Issues live in GitHub Issues for `yonatanppr/tapo-cat-detector`, managed with the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

Default vocabulary: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: one `GLOSSARY.md` and `docs/adr/` at the repo root. See `docs/agents/domain.md`.
