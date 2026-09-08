# Product Manager review — RoomLens v3 milestone package

Reviewer persona: Product Manager (the user's first hour).
Scope: `docs/milestones.md`, `docs/business-plan.md`,
`docs/videos/v3-presentation-plan.md`, `README.md`, `docs/how-to/`.
Reviewers never fix — findings only.

## Verdict: NEEDS WORK

---

## Major

### M1. The walkthrough stops before the MVP's conversion moment — no order confirm, no consultation request, no designer-side order handling

- **Ref:** `docs/videos/v3-presentation-plan.md` §2 (Walkthrough, target 6:00);
  `docs/milestones.md` MVP (goal + done criteria).
- **Expectation violated:** PM rubric (b) — the walkthrough must cover the
  true day-one flows (first order / first visualization) completely. The
  first visualization is shown completely; the first *order* is skipped.
- **Finding:** §2's purpose ends the loop at "prospect receives the preview →
  prospect responds" and lists the four prospect options ("1. Order it",
  "2. Change the placement", "3. Change the product", "4. Talk to the
  designer") without walking any of them. But the MVP's goal is literally
  "First paid consultation," and its done criteria are ≥15%
  prospect→designer contact (**assumption**) and ≥1 paid consultation
  attributed. The mechanics exist and are documented —
  `docs/how-to/first-visualization.md` Scene 5 (reply `1` → quote → confirm)
  and `docs/how-to/designer-onboarding.md` Scene 5 (order queue, pick order,
  update status) — but the plan never schedules them on screen. The video's
  own §4 business section argues "the pilot measures demand, not plumbing"
  and §6's ask asks the board to approve a funnel the walkthrough never
  shows converting. A pitch whose walkthrough stops one tap before the MVP's
  own money moment leaves the board unable to evaluate the conversion loop
  the whole milestone is named for.
- **Required:** extend §2 (see M2 for budget) to walk one conversion beat
  end-to-end: prospect replies `1` → quote → confirm (or `4` → "talk to the
  designer" tap + designer notification), plus the designer's order-queue
  status update. This is the one beat that proves the MVP is a *commerce*
  loop, not a render demo.

### M2. Eight beats in 6:00 — the flagship section repeats the v2 compression it claims to fix

- **Ref:** `docs/videos/v3-presentation-plan.md` §2 items 1–8.
- **Expectation violated:** the plan's own §2 framing — "the pacing fix is
  structural, not cosmetic" and "~2.2 min/section." Also the v2 critique
  (plan §1: `script-first-visualization.md` was "Rushed — seven scenes in 5
  minutes (0:42/scene)").
- **Finding:** §2 schedules eight distinct beats in 6:00 (designer
  onboarding, catalog add, English prospect flow, Marathi prospect flow,
  studio placement, localized delivery, quote/DB records, quality gate) —
  ~45 seconds per beat, i.e. *tighter* per-beat than the v2 script the plan
  criticizes for rushing at 0:42/scene. The pacing rules (hold chat frames
  until narration finishes; two preview deliveries held ≥30 s each) are good
  and should stay, but the arithmetic doesn't leave room for them across
  eight beats plus the missing conversion beat (M1). Two full prospect flows
  (English + Marathi) is the obvious compression: the Marathi strings are
  required as proof of locale parity, but the full Marathi *flow* duplicates
  the English flow's structure — show the English flow complete and the
  Marathi flow as a held localization frame, not two complete flows.
- **Required:** cut §2 to 5–6 beats max (merge the two prospect flows into
  one flow + one held Marathi proof frame) and give the recovered ~2 minutes
  to the M1 conversion beat.

### M3. v1.2 bundles a conditional, company-sized escrow build with unrelated features — un-sizeable as one milestone

- **Ref:** `docs/milestones.md` v1.2 ("Monetizable marketplace" — In scope).
- **Expectation violated:** milestone discipline — a milestone must be
  committable regardless of which measured branch the pilot data takes.
- **Finding:** the in-scope list combines (a) "payment/escrow rail
  implemented after an explicit decision — take-rate vs qualified-lead fee,"
  (b) customer reviews, (c) style quiz + saved boards, (d)
  perspective/lighting correction improvements, (e) designer CRM lite. Item
  (a) alone is a licensing/KYC/dispute-handling project — the business plan
  (`docs/business-plan.md` §3, "Where it breaks") says operating escrow
  brings licensing, KYC, dispute handling, and settlement risk (India PA/PG,
  US money-transmitter considerations), and that "10–15% looks generous
  until one dispute consumes it." And (a) is *conditional*: if pilot data
  picks the qualified-lead fee, the escrow rail is never built — so the
  milestone's largest work item may evaporate at the decision gate, while
  the remaining items (quiz, CRM, reviews) are three independent bets that
  share no shipping dependency with it. You cannot staff, budget, or sign
  off on a milestone whose biggest component might not exist.
- **Required:** split. v1.2a = platform-observed conversion event + lead-fee
  plumbing + CRM lite + reviews (the lead-fee path and shared tooling);
  v1.2b = escrow rail, gated on an explicit board decision *for* the
  take-rate model from measured conversion data. Style quiz / saved boards
  should be their own optional v1.3, not bundled into either monetization
  path.

## Minor

### m1. MVP "Consultation booking" over-labels a notify-tap

- **Ref:** `docs/milestones.md` MVP in scope #4 ("Consultation booking + lead
  handoff with designer contact"); `docs/videos/v3-presentation-plan.md` §4
  non-goals ("The booking tap writes an order row and notifies the
  designer").
- **Expectation violated:** accurate naming — the product behavior is a tap
  that writes an order row and notifies the designer; there is no time-slot,
  calendar, or scheduling step ("booking" implies a booked slot). This is
  fine for MVP, but the milestone should call it what it is to prevent the
  pilot team (and the board) from over-reading the feature.
- **Fix:** rename to "consultation request + lead handoff" in milestones.md
  MVP in scope #4.

### m2. Stale "Still open (v3 round)" in milestones.md

- **Ref:** `docs/milestones.md`, final section ("Still open (v3 round)").
- **Expectation violated:** document currency — the section lists
  `docs/business-plan.md` and the v3 pitch video as open items, but both
  artifacts exist and are dated 2026-09-07 (business-plan.md v1;
  `docs/videos/v3-presentation-plan.md`). Same staleness pattern as the
  BiteFlow repo's milestones doc.
- **Fix:** update the section to reflect what's actually still open (board
  review itself).

---

## Rubric coverage summary

- **(a) 60-second clarity — PASS.** The §1 intro states the problem
  (designers lose sales when prospects can't picture furniture in their own
  room), the product category, the zero-client thesis, who pays, and the
  honest boundary ("2D preset-based compositing at fixed anchors — explicitly
  not AR, and we never present it as AR") before any chat or terminal
  appears. This is the strongest intro of the two repos' packages.
- **(b) Day-one flows — MIXED.** The designer's first-day flow (onboarding →
  studio name → catalog add with the honest no-background-removal line →
  room notification → preset placement → adjust → send) and the prospect's
  first visualization (hello → pick studio → nickname → photo → quality gate
  → preview → four options, in English and Marathi) are both complete and
  paced by the hold-until-narration rule — good onboarding-friction coverage.
  But the first *order* / first *consultation request* is never walked (M1).
- **(c) Pacing — MIXED.** Section totals (2 + 6 + 1.5 + 2.5 + 1 + 1 ≈ 14 min)
  sit inside the 13–15 min target; §3 (Transitions) correctly gives each
  known gap a spoken sentence instead of a checklist flash; §4 (Business
  model) budgets the money-flow diagram, the two v1.2 candidates, and the
  India/US segmentation well. The sag/rush is inside the flagship
  walkthrough (M2).
- **(d) Milestones — MIXED.** MVP "First paid consultation" is appropriately
  minimal: real-photo quality bar (20+ photos pre-pilot) attacks the #1
  expectation risk directly, the honest "not AR" framing is in every chat,
  payment stays explicitly off-platform, and the out-of-scope list (payment/
  escrow, AR, 3D, reviews) is correctly drawn. v1.2's *gates* properly
  follow from measured data (contact→booking measured and stable, 90-day
  designer retention, unit economics per market, never blended). But v1.2's
  *scope* bundles a conditional escrow build with unrelated features (M3).
