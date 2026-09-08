# QA Analyst review — RoomLens v3 milestone package

Reviewer persona: QA Analyst (verify every claim; entry/exit coverage; caption/frame accuracy).
Date: 2026-09-07. Scope reviewed: `docs/milestones.md`, `docs/business-plan.md`,
`docs/videos/v3-presentation-plan.md`, spot-checked against `docs/evidence/`
(`test-run-2026-09-07.log`, `engine-output-2026-09-07.log`, `room-asha-original.jpg`,
`viz-asha-aria-chair.jpg`, `viz-marathi-user-aria-chair.jpg`), `docs/SCALE.md`,
and `git log`.

**Verdict: SHIP**

## Blocker findings

None.

## Major findings

None.

## Minor findings

### m1 — locale key count is 87, not 85, in two places

- **The claim:** `docs/business-plan.md` §1: *"English, Spanish, Hindi full parity (85 keys each,
  tested)"*; the v3 presentation plan §3 claim map repeats *"en/es/hi full parity (85 keys)"*.
- **Where it appears:** `docs/business-plan.md` §1, line ~31; `docs/videos/v3-presentation-plan.md` §3.
- **The evidence checked:** `locales/en.json`, `locales/es.json`, `locales/hi.json` each contain
  **87** keys (measured via JSON parse); `locales/mr.json` holds 46 (partial, as claimed).
  `test_key_parity` is PASSED in the test log, so the parity statement is true — only the
  hard-coded count is stale by two keys (likely added since the number was first written).
- **Expectation violated:** exact numbers in the package must match the repo. Cosmetic:
  update "85" → "87" in both files (or cite `test_key_parity` instead of a count).

## What verified cleanly (for the record)

- **Test-count claims match evidence exactly.** The claim map cites "92 tests pass, 1 skipped
  (Postgres smoke needs live DB)" — the log's last line reads
  `================== 92 passed, 1 skipped, 2 warnings in 10.99s ==================` and the
  single skip is `test_postgres_schema_and_roundtrip SKIPPED (DATABA…)` — the no-DATABASE_URL
  skip the package discloses. No stale figures from v2 leak into v3 narrated claims.
- **Scale claim is properly qualified.** The plan's strongest performance evidence — "~35
  webhook req/s, 0 failures, single worker" — matches `docs/SCALE.md`'s measured table exactly
  (4,183 POSTs, 0 failures, ~35 req/s, 50 users / 2 min). The v2 script's over-claim
  ("scaling is just adding workers") is killed and replaced with "multi-worker uvicorn — Not
  tested" (SCALE.md line 57). The claim map's row on this point is honest.
- **Walkthrough frames trace to real engine output.** The engine-output log header states all
  text came from `src/state_machine.process_incoming` over the fake adapters ("same code path
  as production, sans network") — matching the plan's §1 "must say" line. Spot-checked verbatim:
  Marathi `"✅ भाषा बदलली."` present; quote renderings `Aria Chair × 1 — $189.00` (en) and
  `Aria Chair × 1 — ₹189.00` (mr) from the same `subtotal_cents: 18900` row (§7); both render
  JPGs and the input room photo exist in `docs/evidence/`. `test_video_frame_extracted_and_accepted`
  is PASSED, so the plan's conditional keep/cut note on the video-frame convenience claim is
  moot — it can keep with the test-log citation.
- **Honest-boundary statements are evidence-backed.** "Preset-based, not AR" — engine-output §7
  shows `placements: [{'product_id': 3, 'preset': 'floor-center', 'scale': 1.0}]` and the
  business plan's "Honest product boundary" lists the actual limitations (no plane detection, no
  depth, no guaranteed scale). "No background removal" matches the A22 patch and `src/media.py`.
  Synthetic-media disclosure (A4) is present in the plan at the viz step and the closing card.
- **Business-plan labeling is disciplined.** Every §6 table row is labeled assumption; lead-fee
  pricing is explicitly "TBD from pilot data" rather than invented; India and US are modeled
  separately (per the milestones requirement); the "binding unknowns" (contact→consultation
  conversion, Meta per-conversation cost, platform-observed conversion event) are named as
  unknowns, not filled in. The docker-compose claim ("one Python container + PostgreSQL 16")
  matches `docker-compose.yml` (`postgres:16-alpine`).
- **Milestones metrics are measurable / MVP gates falsifiable.** 20+ real-room visualizations,
  ≥70% photo→preview completion, ≥15% prospect→designer contact (explicitly labeled assumption),
  ≥1 paid consultation attributed — all countable, all have clear fail states. The plan
  correctly carries the milestones "Known gaps" (synthetic fixtures, no monetization capture,
  partial Marathi) verbatim into the disclosure card; none contradict `main`.
- **Commit citations check out:** `1525ccb` (nickname/currency) and `a764799` (how-to/FAQ)
  both exist on `main`.

## What would be nice (non-blocking)

1. Correct "85 keys" → "87" in `docs/business-plan.md` §1 and the v3 plan §3 claim map (m1).
