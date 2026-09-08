# Re-review sign-off — QA Analyst (v3 board-review round)

**Date:** 2026-09-07. **Re-reviewer:** QA Analyst hat (subagent, no fixes made).
**Repo state:** `main` at `deb736f` (presentation plan); code fixes at `d235d36`,
doc fixes at `b8e5e6b`.
**Method:** read each changed line against TRIAGE.md acceptance criteria;
ran the test suite myself (`.venv/bin/pytest tests/` → **97 passed, 1 skipped**;
`ruff check src tests` → clean). A fix I could not verify against the repo
is recorded as rejected, not passed.

## Overall sign-off: **CHANGES STILL NEEDED**

31 of 32 accepted fixes confirmed against the repo. F-06 is partially rejected:
the gate move, deadline, disclosure, and risk update are all verified in the
docs, but two of the triage's explicit criteria — a **named owner** and an
**implemented + tested deletion path** — are not present anywhere. The deletion
"path" today is a procedure doc (`docs/how-to/media-retention.md`), not code,
and has no tests. The gate language says these must exist before the first
paid pilot, which is the right shape, but the fix as specified is not complete.

## Per-fix-ID table

| Fix ID | Verdict | One-line evidence |
|---|---|---|
| F-01 | confirmed | `business-plan.md:46`, ARCHITECTURE i18n table, TROUBLESHOOTING, and plan claim map now say "87 keys"; `python -c` JSON count: en/es/hi = 87, mr = 46 (matches claim-map partial note) |
| F-02 | confirmed | `SCALE.md:31-35` states the 2026-09-05 run measured text + download-failure image traffic, render path "unmeasured"; fixture seeding (`ROOMLENS_SEED_LOADTEST_MEDIA` in `src/main.py`, wired in `loadtest.yml`) added; plan claim-map row 8 repeats the qualified claim |
| F-03 | confirmed | `ARCHITECTURE.md:163` new "Deliberate simplifications / honest limits" section: unthrottled campaign loop (no rate control, no receipts, no retry) + signature validation not implemented |
| F-04 | confirmed | `ARCHITECTURE.md:53-57` names the silent-drop consequence (200 → Meta won't retry → user gets no reply, no dead-letter); `loadtest.yml:62-71` greps `/tmp/uvicorn.log` for `[roomlens] handler error` and fails the run |
| F-05 | confirmed | milestones Known gap #4 (`milestones.md:27-30`) + MVP in-scope item #6 (`:51-52`); plan Transitions carries the gating sentence (`:174-176`) and §6 Ask states the condition out loud (`:261-262`) |
| F-06 | **REJECTED (partial)** | Gate moved to MVP "what must be true" (`:77-81`), deadline "before first paid pilot", spoken Meta-visibility disclosure in Transitions (`:178-181`), business-plan risk 6 updated — **but** no named owner is stated anywhere and no implemented/tested deletion code path exists (procedure doc only, zero tests) |
| F-07 | confirmed | `milestones.md:83-85` backup/restore before first paid pilot; `TROUBLESHOOTING.md:100-114` documents rehearsed-restore drill + media-ref integrity check |
| F-08 | confirmed | v1.2 growth gate "Concurrent-render load test" (`milestones.md:107-109`); business-plan §6 sensitivity row for 2+ window funnels (`:347-350`); spoken Transitions disclosure (`:182-184`) |
| F-09 | confirmed | Pilot ops floor in milestones (`:86-89`: alert on handler errors, named human in business hours); startup self-check in `src/main.py:90-96` fails loudly if `ENABLE_VIDEO_CLIPS` set and ffmpeg absent (`config.py:30`); spoken disclosure in Transitions (`:185-188`) |
| F-10 | confirmed | v1.2 growth gates include "Attribution-integrity check" — spot-audit vs platform-observed signals; lead-fee cannot be selected until the observed event is source of truth (`milestones.md:100-103`) |
| F-11 | confirmed | `DEPLOYMENT.md:80-85`: 90-day rotation cadence + one named human holds Meta app admin + separate pilot Meta app |
| F-12 | confirmed | Transitions spoken line: "Opt-outs are currently unauthenticated — … until signature validation lands" (plan `:189-191`) |
| F-13 | confirmed | Plan §2 beat 5 (`:149-151`) and build notes (`:339-342`): render pass must show Marathi frames verbatim, never "clean up" fallback English |
| F-14 | confirmed | Plan §2 beat 4 (`:135-144`): prospect `1` → quote → confirm → order placed with payment line → tracking → designer status update; evidence logs `docs/evidence/engine-conversion-beat-2026-09-07.log` + `-mr-` log exist and contain the real localized output |
| F-15 | confirmed | Plan §2 now schedules exactly **5 beats** (`:113-115`), EN+MR merged into one flow + one held Marathi proof frame (`:145-151`) |
| F-16 | confirmed | `milestones.md:92` v1.2a (observed conversion + lead-fee plumbing + CRM lite + reviews, nothing conditional) vs v1.2b gated on explicit board decision for take-rate |
| F-17 | confirmed | MVP in-scope #4 (`milestones.md:41`): "consultation request + lead handoff", with the no-scheduling clarification |
| F-18 | confirmed | `milestones.md:134-139` "Still open (v3 round)" now lists the board review itself as the open item |
| F-19 | confirmed | `src/pricing.py:46-50` locale-keyed labels; executed: mr → "एकूण — ₹189.00", hi → "कुल — ₹189.00"; unit test `test_quote_total_label_localized` passes; evidence log contains "एकूण" |
| F-20 | confirmed | `src/pricing.py:92-100` `order_status_label()`; executed: mr → "ऑर्डर डिझायनरला पोहोचली"/"तयार होत आहे"/"डिलिव्हरीसाठी निघाली"/"डिलिव्हरी झाली"/"रद्द झाली" (prospect-facing, no raw English); wired in `prospect.py:282`, `designer.py:387`, `designer.py:426` |
| F-21 | confirmed | `mr.json` `p_no_open_orders` now reads "…कोणतीही **चालू ऑर्डर** नाही" — no "उघडी ऑर्डर" anywhere |
| F-22 | confirmed | `p_order_placed` carries the payment line in all four locales (mr: "💳 पैसे डिझायनरला थेट द्या — अ‍ॅप मध्ये पैसे घेत नाही."); verified in `mr.json`, `en.json` diff, and both evidence logs |
| F-23 | confirmed | Plan §2 (`:87-93`): opening frames carry "Illustrative preview, not to scale — not AR" and intro stakes the value on the funnel; viz JPGs not regenerated/retouched (per D-01) |
| F-24 | confirmed | mr `d_studio_adjust` "परफेक्ट" → "छान!"; `d_cat_name_ask`/`d_cat_photo_ask`/`d_catalog`/`d_studio_pick_product` use "वस्तू"; `p_photo_ok` also updated to "छान" |
| F-25 | confirmed | `business-plan.md:303` lead-fee table prints ₹45–515 / −$4 to +$52 with the recomputed note naming the negative US tail; plan §4 on-screen ranges match verbatim |
| F-26 | confirmed | business-plan §2 (`:110-111`, `:165-167`) states the boundary reversal + counsel sign-off per market as precondition; plan §4 presents the asymmetry, not the symmetric "two models" frame |
| F-27 | confirmed | Decision rule with numeric thresholds (`:114-119`: median project ≥ ₹2,00,000 / ≥ $8,000 + counsel → take-rate; else lead-fee ≤ 20% of measured consult fee) + CAC estimate (`:124-129`: onboarding-labor proxy 4–8 hrs, must log actual hours) |
| F-28 | confirmed | `business-plan.md:317-324` take-rate table prints the true envelope −₹15,000 to ₹73,000 (IN) / −$750 to $3,650 (US) with the pairing note |
| F-29 | confirmed | `business-plan.md:450-481` honest moat section: no tech moat, structural disintermediation leak named, under-reporting tolerance quantified (15% under-reporting wipes out the mid-corner contribution), take-rate/escrow as the anti-disintermediation answer |
| F-30 | confirmed | ≥3 paid consultations per pilot designer + cross-check vs receipts (`:429`), directional WTP probe (`:430`, `milestones.md:64-65`), consult-fee input reliability warning (`:433`), "demand validation, not revenue" label (`:416-419`) |
| F-31 | confirmed | "The decision is made per market" stated in one line (`business-plan.md:121`) |
| F-32 | confirmed | `milestones.md:18`: "Tests passing (97 passed, 1 skipped — 2026-09-07); Ruff clean; CI green." — matches my own run today (97 passed, 1 skipped) |

## What remains

- **F-06 completion:** name an owner and land + test the deletion path
  (the `docs/how-to/media-retention.md` procedure as implemented code with
  tests) — or write an explicit reason if deliberately held to pre-pilot.
- D-01 (rejected with reason) and D-02 (deferred with reason) unchanged.
