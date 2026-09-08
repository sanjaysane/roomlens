# RoomLens — Business Plan (v1)

Date: 2026-09-07. Status: **draft for board review** — consistent with
[docs/milestones.md](milestones.md), which is a proposal pending board review.
Nothing here overrides the milestones document.

Label key (used throughout): **measured** = verified in this repo/CI;
**sourced** = from a third-party rate card or public reference, check at
pilot time; **assumption** = modeling estimate to be validated in the pilot.
Numbers are never presented as facts unless labeled measured.

Currency: the product displays ₹ for Hindi/Marathi and $ for English/Spanish
(**measured** — locale-aware currency, commit `1525ccb`). India and the US
are modeled **separately**, per the milestones requirement — project values
vary wildly by market and must not be averaged.

**Honest product boundary (carried from the README and ARCHITECTURE.md):**
RoomLens does 2D preset-based compositing at fixed anchors
(`floor-center`, `left-wall`, `right-wall`, `wall-hang`), sized by fractions
of the photo width. No plane detection, no depth estimation, no perspective
reconstruction, no guaranteed real-world scale. This is **explicitly not
AR**, and the business plan must never imply otherwise — the expectation gap
is the #1 trust risk in the milestones.

---

## 1. What the product is and who pays

**The product.** RoomLens is WhatsApp-first furniture visualization and
ordering for interior designers — no app install, no account, no forms. A
prospect sends a room photo over WhatsApp; the designer places catalog
products into it with a few numbered replies; the prospect sees their own
room with the furniture in it; they order or request a consultation with a
single digit. Measured capabilities (on `main`):

- Two roles, one chat: designers (catalog, studio, orders, marketing) and
  prospects (photo → preview → order), routed by role state machine.
- Senior-accessible dialogue: single-digit replies, 👍/👎 confirm, no
  required typing in core flows.
- Honest quality gate: dark/blurry/too-small photos get a polite retake
  request — never a misleading overlay.
- Quotes with line items, delivery, totals; order tracking
  (`received → preparing → out_for_delivery → delivered`).
- Opt-in-gated marketing (campaigns, follow-ups, win-backs) via Meta
  pre-approved templates only; `STOP` opts out instantly.
- Locales: English, Spanish, Hindi full parity (87 keys each, tested);
  Marathi partial with English fallback.

**Who pays.** The **designer (or design studio)** pays for the platform —
eventually. In MVP, the designer pays nothing: milestones state payment
stays **off-platform in MVP** explicitly, and there is "no monetization
capture" — a gap accepted for the pilot.

**Whose money moves today (MVP).** Prospect → designer, entirely
off-platform: consultation fees and furniture orders are settled directly
between them (cash, UPI, bank transfer — the product does not touch the
money and does not verify payment). BiteFlow-style lesson applies:
keeping the platform out of the money flow in MVP avoids payment-licensing
and escrow obligations while the product proves demand.

**Who does NOT pay.** The prospect (homeowner) never pays RoomLens
anything. The unit of monetization is the designer, per qualified lead or
per project value.

---

## 2. Business model — how money moves

**Today (MVP — no platform take).**

```
Prospect                    Designer                      RoomLens platform
   │                           │                                  │
   │── room photo (WhatsApp) ──▶│                                  │
   │◀── preview w/ products ────│  (2D composite, not AR)          │
   │── "talk to designer" ─────▶│                                  │
   │◀── consultation ───────────│                                  │
   │── consult fee ────────────▶│  (direct, off-platform)          │
   │                           │── nothing ──────────────────────▶ │ (free in MVP)
```

- The platform's MVP job is lead generation with proof-of-value: the
  prospect arrives with a real room and a real interest; the designer
  converts the conversation into a paid consultation manually.
- Attribution in MVP is **manual**: designers report consultation outcomes
  (milestones § "What must be true" — designers agree to report outcomes).
  There is no platform-verified booking or payment record.

**From v1.2 (decision gated by measured pilot data — per milestones).**
One of two models, decided after "contact → booking conversion measured
and stable" and designer retention data:

- **Qualified-lead fee:** designer pays a fixed fee per consultation that
  originated from a RoomLens lead, or
- **Project take-rate:** 10–15% of project value via an escrow rail the
  platform operates (**assumption** range from milestones v1.2).

Milestones state the choice is "take-rate vs qualified-lead fee" and that
"payment/escrow rail [is] implemented after an explicit decision." The
plan does not pre-commit.

**The asymmetry the "two models" framing hides (v3 F-26).** These are not
symmetric pricing choices. The qualified-lead fee **preserves** the money
boundary the whole package is built on (the platform never touches customer
funds — no payment licensing, no custody). The take-rate **reverses** it:
the platform would hold project funds of ₹1,00,000–5,00,000 per deal
(India), which means licensing (India PA/PG; US money-transmitter),
KYC, dispute handling, and settlement risk. A monetization decision that
changes the company's regulatory posture is a **company decision**, not a
pricing decision. **Counsel sign-off per market is a precondition of
choosing take-rate** — not a post-decision implementation detail.

**The decision rule (v3 F-27 — assumption, to be validated in the pilot).**
From measured pilot data, per market:

- If median measured project value ≥ ₹2,00,000 (India) / ≥ $8,000 (US)
  **and** counsel clears the custody model for that market → take-rate.
- Otherwise → qualified-lead fee, priced at **≤ 20% of the measured median
  consultation fee** for that market.

**The decision is made per market (v3 F-31)** — India and the US are never
blended, and the models may differ between them.

**CAC estimate (v3 F-27 — assumption).** The GTM assumes each designer brings
their own prospect list, so marginal CAC per prospect ≈ ₹0. The real
acquisition cost is **designer onboarding labor**: studio profile, catalog
cutouts, portfolio — estimated 4–8 hours per designer. A v1.2 gate testing
"revenue covers CAC" is untestable against an unestimated CAC, so the pilot
must log actual onboarding hours per designer and re-price this proxy.

---

## 3. Revenue streams and pricing logic

### Stream 1 — Qualified-lead fee (candidate v1.2 model A)

- **Pricing:** a flat fee per consultation attributed to a RoomLens lead.
  No fee number is set anywhere in the repo — pricing is **to be
  determined from pilot data**. For modeling only: a lead fee is sane when
  it is a small fraction of the designer's consultation fee
  (**assumption** — e.g. if a consultation bills ₹3,000, a ₹300–600 lead
  fee is 10–20% of one consult; India/US numbers differ — see §6).
- **Logic:** simplest to collect (designer pays per converted lead, can be
  invoiced or auto-charged), no escrow infrastructure, no custody of
  project funds. Works while payments stay off-platform.
- **Where it breaks:** attribution is the entire model. In MVP attribution
  is manual designer self-reporting — under-reporting is the obvious leak.
  A lead fee requires a platform-observed conversion event (e.g. the
  prospect taps "book consultation" in-chat and the designer confirms),
  which does not exist yet — it is v1.2 scope.

### Stream 2 — Project take-rate via escrow (candidate v1.2 model B)

- **Pricing:** 10–15% of project value (**assumption** from milestones
  v1.2).
- **Logic:** revenue scales with the thing designers actually sell
  (projects, not chats). At 10–15%, even a modest project yields
  meaningful per-deal revenue — this is the only model where a handful of
  designers can carry the business.
- **Where it breaks:** operating escrow means holding customer money —
  licensing, KYC, dispute handling, and settlement risk (India: PA/PG
  guidelines; US: money-transmitter considerations — **inference**, needs
  counsel, not a legal conclusion). It is the heaviest operational lift
  and is explicitly **out of scope for MVP** (milestones: "in-app
  payment/escrow" out of scope). **Counsel sign-off per market is a
  precondition of choosing this model** (v3 F-26) — the decision gate, not
  the build plan, is where the money boundary gets crossed. Also: 10–15% of
  a full interior project is a large bite — designers will only accept it if
  RoomLens-sourced projects are incremental business they wouldn't have won
  otherwise.

### Stream 3 — Designer subscription / SaaS seat (possible v1.2 adjunct)

- Not named in milestones, but a natural third option: flat monthly fee
  per designer studio for the visualization + CRM-lite tooling
  (follow-ups, quotes — both already in v1.2 scope as "designer CRM
  lite"). Included here as an option the board may consider; no pricing
  modeled until pilot data exists.

### Pricing logic summary

| Model | Price | Designer pays | Scales with |
|---|---|---|---|
| Qualified-lead fee | TBD from pilot data | per converted consultation | lead volume × conversion |
| Project take-rate | 10–15% of project value (assumption) | per project, via escrow | project GMV |
| (Adjunct) Studio subscription | TBD | monthly | active designer count |

Models A and B are alternatives for v1.2, per milestones — "take-rate vs
qualified-lead fee."

---

## 4. Target customers / prospects and go-to-market

### The designer (paying side, v1.2+)

- **Profile:** independent interior designers and small studios who sell
  consultations and furniture/product packages. They already market on
  WhatsApp and Instagram (inference from the product's WhatsApp-first
  design and opt-in campaign tooling) and struggle to convert casual
  inquiries into paid consultations.
- **Why they'd adopt:** the preview is a conversion tool — a prospect who
  has seen *their own room* with the designer's products in it is warmer
  than a cold inquiry. The honest framing ("illustrative preview, not to
  scale, not AR") protects the designer's reputation instead of risking
  it. The marketing loop (opt-in campaigns, follow-ups, win-backs) is
  built in for reactivation.
- **Pilot sourcing:** 2–3 committed designers with real catalogs and
  portfolios — a milestones "what must be true" item. Real catalogs
  matter: demo fixtures are synthetic, and compositing quality on real
  customer photos is unproven (milestones gap #1). **Do not pilot with
  stock-photo catalogs.**

### The prospect (non-paying side, the value engine)

- **Profile:** homeowners considering furniture purchases or a design
  consultation — with seniors as the design center (no app, no account,
  no typing). They bring the room photo, which is the raw material the
  whole funnel runs on.
- **Acquisition:** through the designer's existing channels (their
  WhatsApp contacts, Instagram, word of mouth). The product does not do
  direct-to-homeowner marketing; campaigns reactivate a designer's own
  opted-in base.

### Go-to-market sequence

1. **MVP:** 2–3 designers, real-photo pipeline validated on 20+ real room
   photos *before* pilot (milestones requirement), honest "not AR"
   framing in every chat, manual outcome reporting. Success = 20+
   visualizations, ≥70% photo→preview completion, ≥15% prospect→designer
   contact (assumption), ≥1 paid consultation attributed.
2. **v1.2:** only if contact→booking conversion is measured and stable
   and designers are still active after 90 days. Then decide lead-fee vs
   take-rate, build the conversion event (lead fee) or escrow rail
   (take-rate).
3. **Scale:** each designer brings their own prospect flow; template
   campaigns and win-backs compound it. India and US funnels are run and
   measured separately — never blended.

---

## 5. Costs

### Infrastructure (measured/sourced)

- **Stack:** one Python container + one PostgreSQL 16 container
  (**measured** — `docker-compose.yml`). FAQ: "a few dollars a month" on
  a small VPS or modest cloud VM (**sourced** from the FAQ; recheck at
  pilot time).
- **Media storage:** room photos, renders, Ken Burns clips live in the
  media store (local disk by default, Supabase in prod — **measured**
  seams in `src/media.py`). Cost scales with photo volume and retention
  policy; see `docs/how-to/media-retention.md`. At pilot scale (tens of
  photos), negligible; at scale, this is a real line item — set a
  retention policy before v1.2.
- **WhatsApp conversation charges:** Meta bills per 24-hour conversation
  window (**sourced** from Meta's WhatsApp Business pricing; exact price
  not in this repo — read the rate card at pilot time). Note the funnel
  shape: each prospect generates a multi-message conversation (photo →
  preview → review → order/consult), so per-*prospect* conversation cost
  is the unit to model, not per-message.

### Operations labor (assumptions — validate in pilot)

- **Designer onboarding:** studio profile, catalog setup (RGBA cutouts —
  background removal is explicitly out of scope, so the designer or an
  ops helper does it with an external tool), portfolio. Heavier than
  BiteFlow's cook onboarding because catalog assets are visual.
- **Quality-bar work pre-pilot:** establishing the compositing quality
  bar on 20+ real photos (milestones requirement) is staff/contractor
  time, not code.
- **Attribution chasing (MVP):** someone follows up with designers to get
  consultation outcomes reported — manual, and a real labor cost of the
  "free" MVP.

### What is NOT a cost in MVP

- Payment processing/escrow (no rail built), AR/3D licensing (nothing to
  license — it's Pillow/NumPy compositing, **measured**), app-store fees,
  per-seat licensing.

---

## 6. Unit economics per consultation / per lead

All inputs are **assumptions for modeling** unless labeled otherwise.
India and the US are modeled separately, per milestones. Consultation
fees and project values below are **assumptions** (illustrative market
ranges, not measured, not sourced from a rate card) — the pilot must
replace them with designer-reported numbers.

**Worked example — qualified-lead fee model (assumptions):**

| Line | India (assumption) | US (assumption) |
|---|---|---|
| Designer consultation fee | ₹2,000–5,000 | $150–400 |
| Lead fee (10–20% of one consult) | ₹300–600 | $25–60 |
| Gross revenue per converted lead | ₹300–600 | $25–60 |
| Meta conversation cost per prospect funnel | ₹5–15 | $0.50–2.00 |
| Prospects needed per converted lead (at 15% contact→consult) | ~7 | ~7 |
| Conversation cost per converted lead | ₹35–105 | $3.50–14 |
| Attribution/chasing labor per lead | ₹50–150 | $5–15 |
| **Contribution per converted lead** | **≈ ₹45–515** | **≈ −$4 to +$52** |

> **Recomputed 2026-09-07 (v3 F-25)** from the table's own inputs — adversarial
> corners (min = min gross − max costs, max = max gross − min costs); see
> `docs/evidence/unit-economics-recompute-2026-09-07.log`. The US low-end
> case is **negative per converted lead**: at the bottom of the assumption
> envelope the lead-fee model loses money on every converted lead.

**Worked example — project take-rate model (assumptions):**

| Line | India (assumption) | US (assumption) |
|---|---|---|
| Typical small project value | ₹1,00,000–5,00,000 | $5,000–25,000 |
| Take-rate | 10–15% | 10–15% |
| Gross revenue per project | ₹10,000–75,000 | $500–3,750 |
| Escrow/payment processing | 1–3% of project value | 1–3% of project value |
| Dispute/support reserve | 1–2% of project value | 1–2% of project value |
| **Contribution per project** | **≈ −₹15,000 to ₹73,000** | **≈ −$750 to $3,650** |

> **Recomputed 2026-09-07 (v3 F-28)** from the table's own inputs — adversarial
> corners; see `docs/evidence/unit-economics-recompute-2026-09-07.log`. The
> printed range previously hid the negative tail: at the low corner (small
> project × low take-rate × high escrow + reserve) a project **loses**
> ₹15,000 (India) / $750 (US). The prose warning stands — one mishandled
> ₹5,00,000 escrow dispute wipes out the margin of many good deals.

**Reading the table honestly:**

- The lead-fee model is a volume game: per-lead contribution is small
  (hundreds of rupees / tens of dollars), so it needs many designers each
  converting steadily. Its advantage is near-zero operational lift — no
  escrow, no money custody.
- The take-rate model needs very few deals to matter, but each deal
  carries escrow operations, dispute risk, and licensing questions. One
  mishandled ₹5,00,000 escrow dispute wipes out the margin of many good
  deals.
- The binding unknown in both models is the **contact→consultation→
  project conversion rate**, which the MVP is explicitly designed to
  measure (≥15% prospect→designer contact is itself an assumption to
  validate). Do not price either model until that funnel is measured.
- Meta conversation cost per *prospect funnel* (not per message) is the
  variable cost to nail down from the rate card — a chatty preview loop
  (photo → retake → preview → change placement → change product) can span
  multiple 24-hour windows.
- **Sensitivity: funnels spanning 2+ conversation windows (v3 F-08).** Every
  additional 24h window roughly doubles the per-funnel Meta cost. Two windows
  → conversation cost per converted lead ≈ ₹70–210 (India) / $7–28 (US).
  At the India low corner (₹45 contribution) a two-window funnel is already
  underwater; at the US low corner it deepens the −$4 loss. Per-funnel
  window count is therefore a pilot metric, not a footnote.

---

## 7. Risks and what-must-be-true

Consistent with milestones § Risks and § "What must be true" (not
contradicting it; elaborating the business-model implications).

### Risks

1. **Expectation gap on visualization quality.** Compositing on real,
   cluttered, badly-lit customer photos may disappoint — "a bad overlay
   is worse than a polite re-ask" is already the product's philosophy,
   but a disappointed prospect blames the designer, and the designer
   blames the platform. Mitigation (per milestones): quality bar on 20+
   real photos pre-pilot + honest "illustrative, not to scale, not AR"
   framing in every chat. **What must be true:** the pre-pilot photo
   set proves the composite is good enough to help sell, not just
   technically render.
2. **Attribution leakage (lead-fee model).** Manual designer self-reporting
   under-counts conversions; the designer has a direct financial incentive
   to under-report. **What must be true:** a platform-observed conversion
   event exists before any lead fee is charged (v1.2 scope) — e.g.
   in-chat "book consultation" tap + designer confirmation.
3. **Escrow burden (take-rate model).** Holding project funds brings
   licensing, KYC, dispute handling, and settlement risk. 10–15% looks
   generous until one dispute consumes it. **What must be true:** counsel
   signs off on the custody model per market (India vs US separately)
   before the rail is built.
4. **Designer supply and retention.** The pilot needs 2–3 designers with
   real catalogs; v1.2 needs them still active after 90 days. If designers
   churn after the novelty, there is no funnel. **What must be true:**
   the visualization demonstrably helps designers close — measured via
   their reported outcomes, not platform vanity metrics.
5. **Meta cost and policy.** Conversation pricing changes; template
   approvals stall; a policy violation can suspend the business number.
   Business-initiated messages (campaigns, win-backs) require approved
   templates (**measured** requirement in the codebase). **What must be
   true:** per-conversation pricing read from the rate card before unit
   economics are finalized; templates approved before any campaign
   spend is modeled.
6. **Media liability.** Room photos are personal spaces; renders are
   stored files. Retention, deletion-on-request, and consent need a
   written policy before scale (the how-to doc covers mechanics, not
   policy). **What must be true (v3 F-06):** the written retention/deletion
   policy — with a named owner and a dated deadline — exists and the deletion
   path is implemented and tested **before the first paid pilot**, not "by
   v1.2". The pilot is when real photos of real homes first arrive.

### What-must-be-true (business-model edition)

- 2–3 committed designers with real catalogs and portfolios.
- Photo pipeline tested against 20+ real room photos before pilot.
- Designers agree to report consultation outcomes (attribution is manual
  in MVP).
- India and US funnels measured and priced separately — never blended.
- The monetization decision (lead fee vs take-rate) is made from measured
  conversion data, not from this document.

---

## 8. MVP success criteria (tied to milestones.md)

**Label: demand validation, not revenue (v3 F-30).** The MVP proves that
previews convert curiosity into contact and contact into paid work. It does
not prove a business model — the platform captures none of the money, sets
no prices, and probes no willingness-to-pay yet.

The milestones "Done criteria" are the MVP scoreboard; the business-plan
readout maps each to a business question:

| Milestone done criterion | What it proves for the business |
|---|---|
| 20+ real-room visualizations completed | the pipeline works on real photos, not fixtures |
| Visualization completion ≥ 70% (photo → preview) | the quality gate + render loop doesn't leak prospects |
| Prospect → designer contact ≥ 15% (**assumption**) | previews create purchase intent |
| ≥ 3 paid consultations attributed **per pilot designer** (designer-reported, cross-checked against receipts) | the funnel produces repeatable paid work, not one anecdote |
| Directional WTP probe: what would each pilot designer pay per converted consult? | v1.2 pricing starts from a stated number, not a blank |
| Honest "not AR" framing in every chat | trust is protected even when the render is imperfect |

> **On the consultation-fee inputs (v3 F-30):** the ₹2,000–5,000 / $150–400
> consultation-fee assumptions in §6 are the least reliable pilot input —
> designers understate income to a platform that might charge a percentage
> of it (the same incentive as the attribution leak in risk 2). The pilot
> must cross-check designer-stated fees against attributed-consultation
> receipts, not take statements at face value.

**Business-plan gate to v1.2:** in addition to the above, the pilot must
produce the measured inputs for §6 — actual contact→consultation→project
conversion rates, actual Meta conversation cost per prospect funnel,
actual consultation fees and project values per market (designer-reported),
and 90-day designer retention. The monetization decision (qualified-lead
fee vs project take-rate via escrow) is made from those numbers. No
pricing is final until the funnel is measured.

---

## 9. Honest moat / defensibility (v3 F-29)

**There is no technology moat.** The product is Pillow/NumPy compositing at
preset anchors behind a WhatsApp state machine — cloneable in weeks by any
competent team. Any moat claim stronger than that would be fiction, and the
board should not underwrite one.

**The structural leak: disintermediation.** Designer and prospect meet *on
WhatsApp* and can transact there forever, off-platform, with zero switching
cost. The lead-fee model taxes a conversion the platform cannot observe in
MVP: attribution is manual designer self-reporting, and the designer has a
direct financial incentive to under-report.

**Quantifying the leak's tolerance (assumptions, from §6's India inputs):**
at the low-end corner, contribution per converted lead is ₹45 — so
**15% under-reporting wipes out the contribution entirely**
(₹300 × 0.15 = ₹45). At the mid-case (≈ ₹450 gross, ≈ ₹170 costs),
tolerance is ≈ 62%; at the high corner, ≈ 86%. In other words: the lead-fee model survives only with
the platform-observed conversion event (v1.2a scope) *and* spot-audit
discipline (milestones v1.2 gate, F-10). Without both, the leak is not a
risk — it is the P&L.

**What could actually compound:** execution and distribution. Designer
relationships and real catalogs (the compositing quality bar on real photos
is work, not code); opted-in prospect bases behind `STOP`-gated templates;
the honest "not AR" framing as a trust brand; speed of the pilot-to-v1.2a
loop. None of these is a moat in the textbook sense — together they are a
head start that must be converted into the observed conversion event before
a clone catches up.

**The take-rate connection.** The take-rate/escrow model is the
anti-disintermediation answer: when the platform holds the project funds, the
conversion is observed by construction. But it buys that at the cost of the
money boundary (F-26 §2) — licensing, KYC, dispute handling, settlement
risk. They are the same decision: *how much of the transaction do we need to
see, and what are we willing to become in order to see it?*
