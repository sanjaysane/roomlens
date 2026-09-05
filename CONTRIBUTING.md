# Contributing

## Dev setup

```bash
git clone <repo> && cd roomlens
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # leave values empty: fakes kick in
```

With no env vars the app boots with in-memory fakes (fake DB, fake WhatsApp,
local media dir) — no credentials needed to hack on conversation flows.

For the real stack: `docker compose up --build` (postgres:16-alpine with the
schema auto-applied), or set `DATABASE_URL` to a local PostgreSQL and run
`uvicorn src.main:app --port 8000`.

## Tests

```bash
pytest                    # full suite
pytest -m "not postgres"  # skip the real-PostgreSQL test
DATABASE_URL=postgresql://roomlens:secret@localhost:5432/roomlens pytest
```

- **69 passed, 1 skipped** is the baseline (the skip is the `postgres`-marked
  test without `DATABASE_URL`).
- The `postgres` marker (`pytest.ini`) flags tests needing a real database;
  CI applies `sql/schema.sql` and runs them against a postgres:16 service.
- Coverage gate: `--cov-fail-under=70` in CI.

## Lint

```bash
ruff check src tests
```

CI runs ruff on both `src` and `tests`; keep it clean (zero warnings).

## Locale parity rule

`locales/en.json`, `locales/es.json`, `locales/hi.json` must each have **exactly
85 keys**, and the key sets must be identical. `tests/test_locales.py` enforces
parity. **When you add a message key, add it to all three languages in the same
PR** — a missing key fails CI. If you can't translate accurately, add the key
with the English text and flag it for a native speaker in the PR description.

## PR expectations

- Tests for new behavior (unit or flow-level; the `FakeDatabase` /
  `FakeWhatsAppClient` doubles make flow tests cheap — see `tests/test_flows.py`).
- `ruff check src tests` clean.
- Locale parity maintained if you touched user-facing text.
- Update docs (`docs/`, README) when behavior, endpoints, env vars, or scale
  numbers change. **Never invent benchmark numbers** — only quote measured ones
  (see `docs/SCALE.md`).
- No secrets, tokens, or phone numbers in code, tests, fixtures, or PR
  descriptions.
