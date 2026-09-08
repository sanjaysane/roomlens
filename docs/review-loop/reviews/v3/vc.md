# RoomLens — VC Review (v3 milestone package)

Reviewer: Persona #6 (VC). Rubric: monetization, unit economics,
money-movement honesty, moat. Independent review — findings only, no fixes.
Docs read: `docs/milestones.md`, `docs/business-plan.md` (each twice),
`docs/videos/v3-presentation-plan.md` (business-model sections).

**Verdict: NEEDS WORK**

Same pattern as the sibling repo, different failure points: the labeling
discipline is exemplary (assumption/sourced/measured on every number, India
vs US never blended, unknowns named on screen), but re-running the plan's
own arithmetic shows the lead-fee contribution ranges don't close, the
take-rate candidate reverses the package's core money-movement boundary, and
the moat question is never asked. Credit where due: killing the v1
commission narration (CHANGELOG A1/A2) was the right call, and all three
documents are now unanimous that the platform touches no money in MVP.

---

## Blockers

### B1. Lead-fee unit economics don't close — the stated ranges contradict the plan's own assumptions
- Ref: `docs/business-plan.md` §6 (qualified-lead fee table).
- Re-run, India: gross ₹300–600/converted lead. Costs per the plan's own
  lines: conversation cost ₹5–15 × ~7 prospects (1 ÷ 15% contact rate ≈
  6.67 → ~7 ✓) = ₹35–105; attribution/chasing labor ₹50–150. Contribution
  = 600 − 35 − 50 = **₹515** (best) to 300 − 105 − 150 = **₹45** (worst).
  The plan states "≈ ₹150–400". The plan's own assumptions produce a
  wider envelope on both ends.
- Re-run, US: gross $25–60; costs $3.50–14 + $5–15 = $8.50–29. Contribution
  = 60 − 8.50 = **$51.50** (best) to 25 − 29 = **−$4.00** (worst). The plan
  states "≈ $10–40" — which hides the material fact that the US low-end
  case is **negative per converted lead**. A VC funding a "volume game"
  (the plan's own words, §6) needs the negative tail on the page, not
  averaged away.
- Expectation violated: the plan promises arithmetic on its own assumptions;
  the printed ranges are narrower than the assumption envelope in both
  markets. Reconcile: either tighten the input assumptions or print the true
  computed ranges (IN ≈ ₹45–515, US ≈ −$4 to +$52). Until this is fixed the
  "volume game" has no verified floor.

### B2. The take-rate candidate reverses the MVP money boundary — the "choice" is asymmetric and un-gated
- Refs: `docs/business-plan.md` §2 (take-rate "via an escrow rail the
  platform operates"), §3 (Model B), §7 risk 3; `docs/milestones.md` v1.2
  ("payment/escrow rail implemented after an explicit decision — take-rate
  vs qualified-lead fee"); `docs/videos/v3-presentation-plan.md` §4.
- Expectation violated: the package's foundational, thrice-repeated position
  is that the platform never touches customer funds ("keeps the platform
  out of payment-licensing territory… deliberately out of the MVP"). The
  lead-fee model preserves that boundary; the take-rate model requires
  operating escrow — holding project funds of ₹1,00,000–5,00,000 (India)
  with licensing (PA/PG guidelines; US money-transmitter), KYC, dispute
  handling, and settlement risk. The plan flags this as risk 3 (correctly
  labeled inference) but the decision is presented — in milestones, plan,
  and video alike — as a symmetric "take-rate vs qualified-lead fee"
  choice with no gate on the asymmetry: there is no requirement for
  counsel sign-off on the custody model *before* the choice is made.
  Doc fix: (1) state plainly that take-rate reverses the money boundary
  while lead-fee preserves it; (2) add counsel sign-off per market as a
  precondition of choosing take-rate, not a post-decision implementation
  detail. A monetization decision that changes the company's regulatory
  posture is not a pricing decision — it's a company decision, and the
  package treats it as the former.

### B3. "Measured and stable" is not a decision rule — the monetization choice is a punt
- Refs: `docs/milestones.md` v1.2 growth gates ("Contact → booking
  conversion measured and stable. Designer retention… Unit economics:
  revenue per qualified lead (or % of project value) covers CAC + WhatsApp
  conversation costs."); `docs/business-plan.md` §8.
- Expectation violated: no numeric threshold anywhere. What conversion rate
  selects lead-fee? What project-value distribution selects take-rate?
  "Covers CAC + conversation costs" is a viability test, not a choice rule —
  and note that CAC itself is never modeled anywhere in the package (a gap
  in the "unit economics covers CAC" gate: you can't test coverage of a
  number you don't estimate). Further, the lead-fee model requires a
  platform-observed conversion event (plan §3: "does not exist yet — it is
  v1.2 scope"). The decision depends on attribution infrastructure that
  doesn't exist, measured against thresholds that aren't stated. State the
  rule: e.g. "if median project value ≥ ₹X and counsel clears custody →
  take-rate; else lead-fee priced at ≤Y% of measured consultation fee."

---

## Majors

### M1. Take-rate contribution range uses inconsistent cost pairing — hides a negative tail
- Ref: `docs/business-plan.md` §6 (take-rate table): stated ≈ ₹6,000–60,000
  (IN), ≈ $300–3,000 (US).
- Re-run, India: gross 10–15% × ₹1,00,000–5,00,000 = ₹10,000–75,000. Costs:
  escrow 1–3% of project value = ₹1,000–15,000; dispute reserve 1–2% =
  ₹1,000–10,000. The low end (₹6,000) pairs 10% × ₹1,00,000 with worst-case
  costs (10,000 − 3,000 − 1,000); the high end (≈₹60,000) pairs 15% ×
  ₹5,00,000 with best-case costs (75,000 − 5,000 − 5,000). But the true
  envelope from the stated assumptions runs 10,000 − 15,000 − 10,000 =
  **−₹15,000** (low project value, low rate, high costs) to
  75,000 − 1,000 − 1,000 = **₹73,000**. The printed range quietly drops
  the negative tail — and §6's own warning ("one mishandled ₹5,00,000
  escrow dispute wipes out the margin of many good deals") lives in prose
  while the table pretends the floor is +₹6,000. Print the true envelope or
  state the pairing assumption explicitly.

### M2. No moat — and disintermediation is structural to the channel
- Refs: `docs/business-plan.md` (no moat/defensibility section); §7 risk 2
  (attribution leakage); §3 (lead-fee "where it breaks").
- Expectation violated: the rubric asks what stops a clone; the plan never
  asks. The product is Pillow/NumPy compositing at preset anchors behind a
  WhatsApp state machine — cloneable in weeks. Worse, the distribution
  channel is the disintermediation vector: designer and prospect meet *on
  WhatsApp* and can transact there forever, off-platform, with zero
  switching cost. The lead-fee model monetizes a conversion the platform
  can't observe in MVP (plan: attribution is "manual designer self-
  reporting," and the designer has "a direct financial incentive to
  under-report"). The only named mitigation — a platform-observed conversion
  event — is v1.2 scope that doesn't exist. What could be a moat: the
  designer catalog/CRM data, prospect photo history, and placement
  intelligence locked in the platform; multi-designer discovery (currently
  out of scope); the opt-in marketing base. None is claimed. The honest
  version: this is an execution and distribution play whose lead-fee model
  has a known, structural leak — the plan should quantify the leak's
  tolerance (what under-reporting rate kills the model?) instead of
  deferring it to an unbuilt event.

### M3. MVP success criteria prove a funnel, not a business — and "≥1 paid consultation" is a thin business gate
- Refs: `docs/milestones.md` MVP done criteria; `docs/business-plan.md` §8.
- 20+ visualizations, ≥70% completion, ≥15% prospect→contact: these prove
  the preview converts curiosity into contact — genuine demand validation.
  But "≥ 1 paid consultation attributed" (designer-reported, manual) is the
  only money signal, and the platform captures none of it. No pricing is
  set anywhere ("lead fee TBD from pilot data" — plan §3); there is no
  willingness-to-pay probe for either model. The package is honest that the
  funnel must be measured before pricing — but a single attributed
  consultation across 2–3 designers is a thin base for a take-rate-vs-
  lead-fee decision. Consider: minimum consultations per designer, and a
  directional WTP question to designers during the pilot (what would you
  pay per converted consult?), so v1.2 pricing starts from a stated number
  rather than a blank.

### M4. CAC is referenced by the growth gate but never estimated
- Ref: `docs/milestones.md` v1.2 growth gates ("revenue per qualified lead…
  covers CAC + WhatsApp conversation costs"); `docs/business-plan.md` (no
  CAC line anywhere).
- The go-to-market (§4) assumes each designer "brings their own customer
  list" and acquisition is cook/designer-to-designer word of mouth — i.e.
  CAC is assumed near-zero without being stated. If that's the assumption,
  state it and defend it (designer onboarding labor in §5 is the real CAC
  proxy: studio profile, catalog cutouts, portfolio — hours per designer).
  A gate that tests "covers CAC" against an unestimated CAC is untestable.

---

## Minors

### m1. "India and US modeled separately" is honored in the tables but the decision framework doesn't say which market decides
- Refs: `docs/business-plan.md` §6; `docs/milestones.md` v1.2.
- If the India funnel supports lead-fee and the US funnel supports take-rate
  (or vice versa), can the models differ by market? The package never says.
  One line — "the monetization decision is made per market" or "one global
  model" — removes the ambiguity.

### m2. Media retention is named as a pre-v1.2 cost/policy item but has no owner or deadline
- Refs: `docs/business-plan.md` §5 ("set a retention policy before v1.2"),
  §7 risk 6.
- Storage cost at scale is a real variable cost of the visualization
  product (renders + Ken Burns clips per prospect). Fine as flagged; worth
  a dated milestone (e.g. "retention/deletion policy written before first
  paid pilot") rather than "by v1.2."

### m3. The ₹2,000–5,000 / $150–400 consultation-fee and project-value inputs are pure assumptions driving both models — and they're the inputs the pilot is least equipped to measure precisely
- Ref: `docs/business-plan.md` §6 (labeled assumption, "the pilot must
  replace them with designer-reported numbers").
- Correctly labeled. The risk is that designer-reported fees are the least
  reliable pilot input (designers understate income to a platform that
  might charge a % of it — the same incentive as the attribution leak).
  Cross-check against the attributed-consultation receipts in the pilot,
  not just designer statements.

---

## Money-movement honesty (b)

Consistent for MVP across all three documents. Milestones: "Payment stays
off-platform in MVP (explicit)"; gap #2 "No monetization capture… designers
are paid off-platform." Business plan §1–§2: "the product does not touch
the money and does not verify payment," with the licensing rationale and
the money-flow diagram showing designer → platform: nothing. Video plan §4
and the claim-to-evidence map: "the tap writes an order row and notifies
the designer; the designer is paid directly, off-platform… Money is
deliberately out of the MVP." The v1→v2 round's commission-claim kill
(A1/A2) holds. No section implies platform-held money in MVP. The issue is
not honesty but asymmetry (B2): the take-rate candidate implies platform
custody of funds in v1.2+, which is disclosed but presented as a symmetric
pricing alternative rather than a boundary reversal with its own
regulatory gate.

## Deferred billing decision (c)

"Decide from pilot data" is a real gate on timing but a punt on the
decision: no numeric thresholds, no mapping from measured inputs to the
choice (B3), the lead-fee model depends on a conversion event that doesn't
exist yet, and the take-rate model depends on a custody posture the
package hasn't gated on counsel (B2). The pilot will produce a funnel
measurement; it will not by itself produce a monetization decision.

## Moat (d)

None stated. See M2. The structural problem is disintermediation, not just
cloning: the channel (WhatsApp) that makes distribution free also makes
bypass free, and the lead-fee model taxes a conversion the platform can't
see. The take-rate/escrow model is the anti-disintermediation answer — at
the cost of the money boundary (B2). The plan should connect these two
points explicitly: they are the same decision.

## MVP success criteria as business proof (e)

They prove the core value hypothesis — a preview of your own room creates
purchase intent (≥15% prospect→contact is the number that matters) — but
they prove no business: zero platform revenue, zero pricing, zero
willingness-to-pay, and the single money data point is designer-reported.
The v1.2 gates (conversion measured, 90-day designer retention, revenue
covers CAC + conversation costs) are the first business tests, but B3/M4
show they aren't yet specified tightly enough to be pass/fail.
