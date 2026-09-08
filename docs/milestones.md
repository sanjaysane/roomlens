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
- Tests passing (97 passed, 1 skipped — 2026-09-07); Ruff clean; CI green.

## Known gaps (must be closed before or during MVP)

1. **Demo fixtures are synthetic** — compositing quality on real customer room
   photos is unproven. The #1 expectation risk.
2. **No monetization capture**: no platform commission accounting, no in-app
   payment rail — designers are paid off-platform.
3. **Marathi parity partial** (English fallback labels).
4. **Webhook signature validation not implemented (v3 F-05).** `POST /webhook`
   does not validate `X-Hub-Signature-256` (see SECURITY.md and DEPLOYMENT.md's
   production checklist). A forged payload can trigger renders (compute cost),
   fire outbound WhatsApp sends (Meta conversation charges), and spam `STOP`
   against a designer's opted-in base. It must land before the first real
   prospect — board approval of the MVP is conditional on it.

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
4. Consultation request + lead handoff with designer contact (v3 F-17 — the
   tap writes an order row and notifies the designer; there is no time-slot
   or scheduling step). Payment stays **off-platform in MVP** (explicit).
5. Prospect flow unchanged: photo → preview → consult request via
   single-digit replies.
6. Webhook signature validation (`X-Hub-Signature-256`) implemented **before
   the first real prospect** (v3 F-05) — board approval of this MVP is
   conditional on it.

**Out of scope:** in-app payment/escrow, AR, 3D rendering, reviews/ratings.

**Done criteria (metrics)**
- 20+ real-room visualizations completed in pilot.
- Visualization completion rate ≥ 70% (photo sent → preview delivered).
- Prospect → designer contact rate ≥ 15% (**assumption**).
- ≥ 3 paid consultations attributed **per pilot designer**
  (designer-reported, cross-checked against attributed-consultation receipts —
  v3 F-30; the fee inputs are the least reliable pilot input).
- Directional WTP probe: what would each pilot designer pay per converted
  consult? (v3 F-30 — v1.2 pricing starts from a stated number, not a blank).

**Risks**
- Compositing quality on real photos disappoints → expectation gap kills trust.
  (Mitigation: honest framing + quality bar on 20+ real photos pre-pilot.)
- Designer supply: need 2–3 committed designers with real catalogs.
- Zero monetization capture while payment is off-platform (accepted for MVP).

**What must be true**
- 2–3 committed designers with real catalogs and portfolios.
- Photo pipeline tested against 20+ real room photos before pilot.
- Designers agree to report consultation outcomes (attribution is manual in MVP).
- **Privacy posture before the first real photo (v3 F-06):** written
  media retention/deletion policy with a **named owner and a dated deadline**
  ("before first paid pilot"), and the deletion path implemented and tested —
  not just documented in `docs/how-to/media-retention.md`. Room photos are
  sensitive PII (interiors reveal wealth, occupants, children, location cues).
  **Owner:** platform operator (pilot on-call) — owns the written policy, the
  scheduled purge job (`src/retention.py`), and honoring deletion requests.
- **Backup/restore before the first paid pilot (v3 F-07):** DB + media store
  backed up on a schedule; restore rehearsed and documented in
  TROUBLESHOOTING.md, including a media-ref integrity check.
- **Pilot ops floor (v3 F-09):** alert on `[roomlens] handler error` (a
  handler exception means the user got *no reply at all* — Meta won't retry
  a 200); a named human watches alerts during business hours. At 10x
  designers, a dead worker silently drops a designer's entire lead pipeline.

## v1.2a — "Observed conversion" (v3 F-16)

**In scope:** the platform-observed conversion event (in-chat consultation
request + designer confirmation); qualified-lead-fee plumbing; designer CRM
lite (follow-ups, quotes); customer reviews. Everything the lead-fee path
and shared tooling need — and nothing conditional.

**Growth gates**
- Contact → booking conversion measured and stable, with numeric thresholds
  per the business-plan §2 decision rule.
- **Attribution-integrity check (v3 F-10):** spot-audit designer-reported
  outcomes against platform-observed signals (e.g. in-chat "talk to the
  designer" taps); the lead-fee model cannot be selected until the
  platform-observed conversion event is the source of truth.
- Designer retention (designers still active after 90 days).
- Unit economics: revenue per qualified lead covers CAC (onboarding-labor
  proxy, per business-plan §2) + WhatsApp conversation costs.
- **Concurrent-render load test (v3 F-08):** N simultaneous visualizations,
  p95 render latency + zero webhook handler errors — the composite/render
  path is unmeasured under load today.
- **SLO/alerting definition (v3 F-09):** handler-error alerting, render-failure
  alerting, and on-call ownership defined — the pilot ops floor, formalized.

## v1.2b — "Escrow rail" (v3 F-16)

**Gated on an explicit board decision *for* the take-rate model**, made from
measured conversion data per the business-plan §2 decision rule — with
**counsel sign-off per market as a precondition** (v3 F-26), not a
post-decision detail. If pilot data picks the qualified-lead fee, v1.2b is
never built. **In scope (only then):** payment/escrow rail; licensing/KYC/
dispute-handling operations; settlement reconciliation.

## v1.3 — "Discovery" (optional, v3 F-16)

Style quiz + saved boards; perspective/lighting correction improvements.
Unbundled from v1.2 — a product bet, not a monetization dependency.

**Business model (estimates — assumptions to validate)**
- Either a qualified-lead fee per consultation, or 10–15% of project value
  via escrow.
- Average interior project values vary wildly by market — India vs US must be
  segmented explicitly, not averaged.
- The monetization decision is made **per market** (v3 F-31).

## Still open (v3 round)

- The board review itself: this document, `docs/business-plan.md`, and the v3
  pitch video are proposals pending board review (v3 F-18).
- v3 pitch video (intro → walkthrough → summary/ask) — gated on the v3 review
  fixes landing.
