## What this PR does

<!-- One or two sentences. Link the issue if there is one: Fixes #123 -->

## Checklist

- [ ] Tests added/updated for the new behavior (`pytest` passes: 69 passed baseline)
- [ ] `postgres`-marked tests considered — ran with `DATABASE_URL` if schema or queries changed
- [ ] `ruff check src tests` is clean
- [ ] Locale parity: if user-facing text changed, the key exists in **all three** locale files (`en`/`es`/`hi`, 85 keys each) — `pytest tests/test_locales.py` passes
- [ ] Docs updated if behavior, endpoints, env vars, or scale numbers changed
- [ ] No invented benchmark numbers — only measured figures from `docs/SCALE.md`
- [ ] No secrets, tokens, phone numbers, or credentials in code, fixtures, or this description
- [ ] Honest-limits check: no AR claims, no promised features that aren't in the code

## How to test

<!-- Commands or chat transcript a reviewer can follow to verify -->
