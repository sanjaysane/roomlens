# Board Director Review — v3 Milestone Package (RoomLens)

**Verdict: SHIP**

Method: read `docs/milestones.md`, `docs/business-plan.md`,
`docs/videos/v3-presentation-plan.md`; verified every public-facing claim
against `docs/evidence/*` (test-run-2026-09-07.log, engine-output-2026-09-07.log,
viz JPGs), `locales/*.json`, `docs/SCALE.md`, and git state on `main`. This is
the cleanest of the two v3 packages: the not-AR boundary, the money path, and
the assumption labeling are all explicit, and the video plan's claim-to-evidence
map checks out against the repo with one small exception (minor m1 below).
No blockers.

---

## Claim-audit table

| # | Claim (as a viewer would hear/read it) | Location | Evidence | Verdict |
|---|---|---|---|---|
| 1 | "92 tests pass, 1 skipped (Postgres smoke needs live DB)" | v3-presentation-plan.md §3 claim map | test-run-2026-09-07.log last line: `92 passed, 1 skipped … in 10.99s`; the skip is `test_postgres_schema_and_roundtrip SKIPPED (DATABA…)` | **supported** |
| 2 | Onboarding/catalog/prospect/studio flows are "real engine output on the production code path" | v3 plan §2 §1 must-say + §3 | engine-output-2026-09-07.log header: "All text below came from `src/state_machine.process_incoming` over the fake adapters (**same code path as production, sans network**)" | **supported** — the "sans network" qualifier is present, unlike BiteFlow's looser intro line |
| 3 | Composite renders are real engine output (sample photos disclosed) | v3 plan §1–§3 | `viz-asha-aria-chair.jpg`, `viz-marathi-user-aria-chair.jpg`, `room-asha-original.jpg` all present in `docs/evidence/`; disclosure caption "Demo uses sample room & product photos" in the plan | **supported** |
| 4 | "2D preset-based compositing at fixed anchors — explicitly not AR, never presented as AR" | milestones.md; business-plan.md "Honest product boundary"; v3 plan §1 must-say, §3 card, non-goal #1 | engine-output §7: `placements: [{'preset': 'floor-center', 'scale': 1.0}]`; tests `test_each_preset_renders_valid_jpeg[…]`; business plan: "No plane detection, no depth estimation, no perspective reconstruction, no guaranteed real-world scale" | **supported** — the not-AR boundary is the most thoroughly evidenced claim in either repo |
| 5 | "~35 webhook req/s, 0 failures, single worker (50 users, 2 min)" | v3 plan §3 | `docs/SCALE.md` measured table: 4,183 POSTs, 0 failures, ~35 req/s; "Honest limits" §: multi-worker NOT tested | **supported** — and the plan kills the v2 "scaling is just adding workers" line (non-goal #4) |
| 6 | "In this build the platform takes no commission: the tap writes an order row and notifies the designer; the designer is paid directly, off-platform" | v3 plan §4 must-say; milestones gap #2 "No monetization capture"; business-plan.md §1–§2 | business-plan §2 money-flow diagram: designer → platform "nothing in MVP"; review-loop CHANGELOG A1/A2 (v1 commission claim killed and stays dead) | **supported** |
| 7 | v1.2 candidates: "qualified-lead fee (TBD) OR 10–15% take-rate via escrow — decision from measured data, not before" | v3 plan §4; business-plan.md §2–§3 | milestones v1.2: choice "take-rate vs qualified-lead fee"; 10–15% labeled **assumption**; lead fee "TBD from pilot data" | **supported** — no numbers-as-facts (non-goal #2) |
| 8 | "Backend saves the raw photo as-is — no background removal" | v3 plan §2 §2, §3 | 2026-09-06 surgical narration patch (CHANGELOG A22); `src/media.py` seams | **supported** |
| 9 | "Dark/blurry/small photos trigger a polite retake, never a misleading overlay" | v3 plan §2 §8 | tests `test_dark_photo_triggers_retake`, `test_blurry_photo_triggers_retake`, `test_small_photo_triggers_retake` all in the test log | **supported** |
| 10 | "en/es/hi full parity (85 keys each, tested); Marathi partial with English fallback" | business-plan.md §1; v3 plan §3 | `locales/`: en=87, es=87, hi=87 keys (full parity ✓), mr=46 keys (partial ✓); `test_key_parity` passes | **needs disclosure** — parity claim is true, but the number is 87, not 85 (see m1) |
| 11 | "USD for English viewers (real engine behavior)" | v3 plan §1 cross-cutting; §3 | engine-output §7: same quote rendered `$189.00` (en) / `₹189.00` (mr) | **supported** |
| 12 | Milestones are a **proposal, not yet board-reviewed**; business plan is a **draft for board review**; video §6 Ask requests *approval* of scope | milestones.md header; business-plan.md header; v3 plan §6 | Labels at the top of both docs; Ask phrased as first approval | **supported** — (c) satisfied |
| 13 | India and US modeled separately, "never blended" | milestones v1.2; business-plan.md §6; v3 plan §4 | §6 unit-economics tables are separate India/US columns with per-market assumptions | **supported** |
| 14 | Media-liability risk (retention/deletion policy needed by v1.2) | business-plan.md §7 risk 6 | `docs/how-to/media-retention.md` covers mechanics; policy flagged as "what must be true" | **supported** — risk named, not hidden |
| 15 | No Meta rate-card numbers quoted anywhere | v3 plan non-goal #5 | Confirmed absent across all three docs | **supported** |

---

## Blockers

None.

---

## Major findings

None. (The package's disclosure discipline holds: every hard question the
v1/v2 rounds fought over — commission contradiction, money-movement
implication, synthetic inputs, background removal, "by hand" placement
language, the "just add workers" scale line — is addressed in the plan
with evidence pointers.)

---

## Minor findings

- **m1 — "85 keys" is stale; the real count is 87.** `business-plan.md` §1
  and the v3 plan's claim-to-evidence map (§3) both say en/es/hi full parity
  at "85 keys each." `locales/*.json`: en=87, es=87, hi=87 (full parity ✓),
  mr=46 (partial ✓). The *parity* claim is true and tested
  (`test_key_parity` passes); only the hard number is wrong — classic
  count-drift after keys were added. **Fix:** change "85 keys" to "87 keys"
  in both places, or drop the count and cite `test_key_parity` instead of a
  number. Expectation violated: claim audit — the docs' own standard is
  that numbers are never presented as facts unless they check out; this one
  doesn't.
- **m2 — Webhook-signature gap is disclosed in the video plan but not in
  milestones' Known gaps.** The v3 plan's §3 Transition card carries
  "webhook signature validation not implemented" as a review-carried item,
  and the v2 videos' closing cards say so — but `docs/milestones.md` Known
  gaps (synthetic fixtures / no monetization capture / Marathi partial)
  doesn't list it. It's not a contradiction — the plan is transparent about
  it being a review-carried addition — but a board member reading only
  milestones won't see a security gap the video will spend spoken time on.
  **Fix:** add it as Known gap #4 in milestones (one line, mirroring
  BiteFlow's gap #2) so both docs list the same gaps.
- **m3 — Milestones say "Tests passing; Ruff clean; CI green" without a
  count.** Not a discrepancy (the evidence and video plan agree on 92/1),
  but BiteFlow's milestones carry a count while RoomLens's don't — cosmetic
  inconsistency across the two v3 packages. Consider adding "(92 passed,
  1 skipped — 2026-09-07)" for parity. Trivial.

---

## Rubric answers

1. **Claim audit.** All material claims trace to evidence: test counts,
   engine-output header, viz JPGs, SCALE.md measured table, locale JSON
   files, the v1→v2 changelog decisions. Only m1 (85→87 keys) fails a
   strict check, and it's a count-drift nit, not a substance gap.
2. **Public-embarrassment test.** The journalist's and the competitor's
   questions are answered before they're asked: not-AR (said up front in
   the intro, repeated on the transition card, enforced as non-goal #1 —
   the "placing the furniture by hand" v2 line is explicitly corrected);
   money never touches the platform (spoken must-say, diagrammed);
   synthetic inputs (on-mic at the viz step + closing card); real-photo
   quality unproven (gap #1, and the pilot's first job is the 20+ real
   photos). The escrow-licensing paragraph is labeled **inference, needs
   counsel** — a regulator reading it finds candor, not a legal opinion
   dressed as one.
3. **Disclosure sufficiency.** Required disclosures (b) all present: not-AR
   framing is carried from the intro through the summary; "money never
   touches the platform" is the §4 must-say; pilot-scale limits are
   structural (every §6 row labeled assumption, India/US never blended,
   the binding unknowns named on screen). Nothing material lives only in
   a sidecar.
4. **Milestones-as-proposal honesty (c).** Satisfied: proposal/draft
   labels at the top of both docs; the §6 Ask seeks a first approval of
   scope and done criteria, never implying prior board review.
5. **The word "AI."** Absent from all three docs — "Pillow/NumPy
   compositing" and "state machine" remain the vocabulary. Keep it that
   way.
