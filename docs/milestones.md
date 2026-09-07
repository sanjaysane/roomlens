# RoomLens — MVP and v1.2 Milestones

Date: 2026-09-07. Status: **proposal** (not yet board-reviewed).
Labels used below: **implemented** = verified on `main`; **assumption** = estimate to validate; **gap** = known deficiency.

## Where we are (implemented)

- WhatsApp-first furniture visualization + ordering for interior designers —
  no app install, no account, no forms.
- Two roles, one chat: designers (catalog, studio, orders, marketing) and
  prospects (photo → preview → order), routed by a role state machine.
- **Preset-based visualization** (Pillow/NumPy compositing at preset anchors
  such as floor-center) — this is NOT AR, and must never be presented as AR.
- Senior-accessible dialogue: single-digit replies, 👍/👎 confirm, no required
  typing in core flows.
- Nickname display; locale-aware currency (commit `1525ccb`).
- How-to and FAQ docs (commit `a764799`).
- Tests passing; Ruff clean; CI green.

## Known gaps (must be closed before or during MVP)

1. **Demo fixtures are synthetic** — compositing quality on real customer room
   photos is unproven. The #1 expectation risk.
2. **No monetization capture**: no platform commission accounting, no in-app
   payment rail — designers are paid off-platform.
3. **Marathi parity partial** (English fallback labels).

## MVP — "First paid consultation"

**Goal:** real prospects send real room photos, receive visualizations, and at
least one converts into a paid designer consultation.

**In scope**
1. Real-photo pipeline: prospect uploads an actual room photo; compositing
   quality bar established on real photos (minimum lighting/perspective
   handling) before pilot.
2. Honest UX framing in-chat: "illustrative preview, not to scale, not AR" —
   set expectations explicitly, every time.
3. Designer onboarding: studio profile, catalog, portfolio.
4. Consultation booking + lead handoff with designer contact. Payment stays
   **off-platform in MVP** (explicit).
5. Prospect flow unchanged: photo → preview → consult request via
   single-digit replies.

**Out of scope:** in-app payment/escrow, AR, 3D rendering, reviews/ratings.

**Done criteria (metrics)**
- 20+ real-room visualizations completed in pilot.
- Visualization completion rate ≥ 70% (photo sent → preview delivered).
- Prospect → designer contact rate ≥ 15% (**assumption**).
- ≥ 1 paid consultation attributed to a RoomLens lead (designer-reported).

**Risks**
- Compositing quality on real photos disappoints → expectation gap kills trust.
  (Mitigation: honest framing + quality bar on 20+ real photos pre-pilot.)
- Designer supply: need 2–3 committed designers with real catalogs.
- Zero monetization capture while payment is off-platform (accepted for MVP).

**What must be true**
- 2–3 committed designers with real catalogs and portfolios.
- Photo pipeline tested against 20+ real room photos before pilot.
- Designers agree to report consultation outcomes (attribution is manual in MVP).

## v1.2 — "Monetizable marketplace"

**In scope:** payment/escrow rail implemented after an explicit decision —
take-rate vs qualified-lead fee; customer reviews; style quiz + saved boards;
perspective/lighting correction improvements; designer CRM lite (follow-ups,
quotes).

**Growth gates**
- Contact → booking conversion measured and stable.
- Designer retention (designers still active after 90 days).
- Unit economics: revenue per qualified lead (or % of project value) covers
  CAC + WhatsApp conversation costs.

**Business model (estimates — assumptions to validate)**
- Either a qualified-lead fee per consultation, or 10–15% of project value
  via escrow.
- Average interior project values vary wildly by market — India vs US must be
  segmented explicitly, not averaged.

## Still open (v3 round)

- `docs/business-plan.md` (business model, revenue, GTM, risks).
- v3 pitch video (intro → walkthrough → summary/ask).
- 7-persona board review of these milestones.
