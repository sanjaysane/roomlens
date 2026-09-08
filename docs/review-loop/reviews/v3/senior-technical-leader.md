# Senior Technical Leader review — RoomLens v3 milestone package

**Verdict: NEEDS WORK**

Reviewer persona: Senior Technical Leader. Rubric: production readiness;
scale/security/compliance/ops gaps that must be disclosed. The question
answered: *what breaks at 10x, and what must be disclosed before the board
approves real customer room photos flowing through the system?*

Docs read: `docs/milestones.md`, `docs/business-plan.md`,
`docs/videos/v3-presentation-plan.md`, `docs/SCALE.md`, `SECURITY.md`,
`docs/TROUBLESHOOTING.md`, plus `docs/DEPLOYMENT.md` (production checklist)
and `docs/how-to/media-retention.md`.

Overall: strong disclosure hygiene — the honest product boundary (not AR),
the synthetic-media rule, the killed commission claim, the single-worker
scale qualifiers. The gaps that remain are the ones a technical leader
cares about most: **PII handling for room photos, a webhook gap that is
still a checklist item rather than MVP scope, and the 10x ops story.**

---

## Blockers

### B1 — Webhook signature validation is a production-checklist item, not MVP scope — but the pilot exposes the webhook publicly (SECURITY.md; DEPLOYMENT.md "Production checklist"; milestones.md § MVP)

SECURITY.md states `POST /webhook` does not validate `X-Hub-Signature-256`
and DEPLOYMENT.md's production checklist says "Implement it before
exposing the webhook publicly… without it, anyone who discovers your
callback URL can POST forged payloads — impersonating prospects,
triggering renders, firing outbound WhatsApp sends." That is a complete
and correct disclosure of impact. The problem: **milestones.md's MVP scope
does not include it.** The MVP asks the board to approve real prospects
sending real room photos to a publicly exposed webhook whose signature
check is a checkbox in another document. A forged payload can trigger
renders (GPU/CPU cost), fire outbound WhatsApp sends (Meta conversation
charges — business-plan.md §5's binding cost line), and spam `STOP`
(opt-out sabotage against a designer's opted-in base).

Expectation violated: a control described as "implement before exposing
publicly" (DEPLOYMENT.md) must be in the scope of the milestone that
exposes it publicly (milestones.md MVP). Checklist placement is not a
commitment.

Required: move webhook signature validation into milestones.md MVP
"In scope" (before first real prospect), and make the board's MVP approval
conditional on it — the same condition the v3 Transitions section should
state out loud (it already gives the gap spoken airtime; add the gating
language).

### B2 — No privacy consent/retention posture for real customer room photos before the pilot — and an undisclosed Meta-visibility fact (milestones.md § MVP; media-retention.md; business-plan.md §7 risk 6)

The MVP's core action is prospects sending **photos of their homes** —
among the most sensitive PII a consumer product can hold (interiors reveal
wealth, occupants, children, location cues). Current state:

- `docs/how-to/media-retention.md` is mechanics + suggestions: "RoomLens
  ships no automatic deletion," retention is a "suggested policy," and
  deletion-on-request is a "periodic job" that does not exist yet.
- business-plan.md §7 risk 6 says a retention/deletion policy must exist
  **by v1.2** — but the pilot (MVP) is when real photos first arrive.
- Nowhere in the package is it disclosed that **WhatsApp Cloud API
  business messages are not end-to-end encrypted the way consumer chats
  are — room photos transit Meta's infrastructure** and are visible to
  Meta per its business-messaging terms. SECURITY.md's scope notes say no
  image goes to a third-party vision service (good), but Meta itself is
  not a third party here — it is the transport, and its visibility is
  undisclosed.

Expectation violated: a production review expects (a) consent language at
collection, (b) a retention/deletion policy *before first real photo*,
not v1.2, and (c) disclosure of every party that can see the PII —
including the platform carrier.

Required: (1) move the retention/deletion policy from "by v1.2" to a
milestones.md "what must be true" item for MVP — written policy +
working deletion path (the media-retention.md procedure, implemented and
tested, not just documented); (2) add one spoken disclosure line to the
v3 Transitions: room photos travel over WhatsApp Business messaging and
are visible to Meta; the product additionally stores originals and
renders per the retention policy. A production-savvy viewer will ask
exactly this.

### B3 — No tested backup/restore for DB + media store (DEPLOYMENT.md "Production checklist"; media-retention.md)

DEPLOYMENT.md's checklist ends with "Back up the DB and the media
volume/store on a schedule" — unchecked, unscheduled, untested. The media
store holds irreplaceable customer originals; the DB holds the refs, and
a ref without its file (or a file without its ref) is silent corruption.
At 10x designers, media volume is business-plan.md §5's own "real line
item."

Expectation violated: same as BiteFlow B3 — a backup checkbox is a vendor
feature, not an ops capability. Production readiness means a rehearsed
restore of *both* stores with ref integrity verified.

Required: milestones.md MVP "what must be true" (or v1.2 growth gates at
the latest): scheduled backups + a rehearsed restore documented in
TROUBLESHOOTING.md, including media-ref integrity check.

---

## Majors

### M1 — Render path untested under concurrency; media cost unmodeled (SCALE.md "Honest limits"; business-plan.md §5)

SCALE.md is candid: "The composite/render path (Pillow + ffmpeg) was not
the bottleneck here; it will be if many visualizations render
concurrently — pre-warm or queue renders if a studio batch-imports."
Business-plan.md §5 says media cost "at scale… is a real line item — set a
retention policy before v1.2." Both are honest; neither is gated. At 10x
prospects, concurrent Pillow/ffmpeg renders on a single worker will queue
behind the same worker serving webhooks (SCALE.md shows `/health` p50 at
1.5s from queueing alone), and the per-prospect conversation cost the
business plan models per 24-hour window can multiply when a chatty
preview loop (photo → retake → preview → adjust → re-render) spans
multiple windows — a cost shape the unit-economics table (§6) does not
stress.

Expectation violated: the #1 product action (rendering) has no concurrency
characterization, and the variable-cost model has no sensitivity case for
multi-window funnels.

Required: add to the v1.2 growth gates a concurrent-render load test
(e.g., N simultaneous visualizations, p95 render latency + zero webhook
handler errors) and a unit-economics sensitivity row for funnels spanning
2+ conversation windows. Disclose in v3 Transitions that renders are
untested under concurrency.

### M2 — No monitoring/alerting/on-call story; health-check queueing is documented but not operationalized (TROUBLESHOOTING.md; SCALE.md)

TROUBLESHOOTING.md documents that under load a single worker takes ~1.5s
to answer `/health` and advises "run more workers or lengthen the
timeout" — good troubleshooting, not an ops plan. There is no alerting on
handler errors, no render-failure alerting, no on-call expectation. At
pilot scale (2–3 designers) a human notices; at 10x designers, a dead
worker silently drops a designer's entire lead pipeline — and unlike
BiteFlow, the lost asset (a prospect who sent a room photo and heard
nothing) is a trust loss for the *designer's* business, not just the
platform's.

Expectation violated: a lead-generation product needs a liveness/reliability
story commensurate with the revenue it claims to influence. "Check the
logs" is not it.

Required: milestones.md should state the pilot ops floor (alert on
`[roomlens] handler error`, named human during business hours) and the
v1.2 gates should include an SLO/alerting definition. One spoken sentence
in the v3 Transitions disclosing the current state.

### M3 — Attribution remains manual self-reporting with a direct incentive to under-report (milestones.md § MVP; business-plan.md §7 risk 2)

Business-plan.md §7 risk 2 names this exactly: "the designer has a direct
financial incentive to under-report," and requires a platform-observed
conversion event before any lead fee. Milestones.md accepts manual
reporting for MVP. That is a defensible pilot tradeoff — but the v1.2
decision (lead fee vs take-rate) is gated on "contact → booking conversion
measured and stable," and the measurement instrument is the party being
measured. At 10x designers this is not a rounding error; it is the revenue
model's integrity.

Expectation violated: a growth gate must not depend on an instrument with
a known bias unless the bias is bounded. The package discloses the bias
(good) but does not bound it.

Required: milestones.md v1.2 growth gates should add an attribution-integrity
check (e.g., spot-audit designer-reported outcomes against in-chat
"talk to the designer" taps, or require the platform-observed conversion
event before the lead-fee model can be selected — which business-plan.md
§7 already implies; make it a gate, not an implication).

### M4 — Secret lifecycle unaddressed beyond placement (DEPLOYMENT.md "Production checklist")

The checklist covers unique-per-environment verify tokens and "tokens in
the environment (or a secret manager), never in the image or repo" — solid.
Missing: rotation cadence/policy (WhatsApp tokens expire and get revoked —
TROUBLESHOOTING.md documents the 401 failure mode), who holds Meta app
admin, and separation between the pilot and production Meta apps. At 10x
designers with ops helpers doing catalog cutouts (business-plan.md §5),
more humans touch more secrets.

Expectation violated: production readiness includes rotation and custody,
not just placement.

Required: a short rotation + custody note in DEPLOYMENT.md. Low effort.

---

## Minors

### m1 — `STOP` handling is tested but the abuse vector is undisclosed (SECURITY.md; v3 plan §2)

B1's DEPLOYMENT.md checklist already names forged-`STOP` spam as an
impact ("spamming `STOP`"). Once B1's signature validation lands, this
closes. Until then it is worth one line in the v3 Transitions: opt-outs
are currently unauthenticated.

### m2 — Marathi partial parity is disclosed; ensure the demo's Marathi frames show fallback strings verbatim (v3 plan §4.7; milestones.md "Known gaps" #3)

The v3 plan's non-goal #7 and claim map handle this. A production-savvy
Marathi-speaking viewer will notice fallback English strings — the plan's
verbatim-output rule covers it; just don't let the render pass
"clean up" a frame.

### m2b — ffmpeg-missing degrades silently to "send a still photo" (TROUBLESHOOTING.md)

Documented and by design. At 10x prospects, a deploy without ffmpeg
silently loses the video path with no alert — fold into M2's alerting
(starthup self-check that fails loudly if ffmpeg is absent when video is
enabled).

---

## On the v3 presentation plan (would it survive a production-savvy viewer?)

Mostly yes — it is careful, and the corrections from the v1→v2 round
("by hand" → preset-based placement, the killed commission claim, the
"just add workers" fix) show the review loop working. Specific notes from
this seat:

- **Survives:** the claim-to-evidence map (§3), the eight non-goals (§4),
  the synthetic-media disclosure on mic + closing card, the corrected
  scale sentence (~35 req/s single worker, multi-worker untested), and
  the explicit "money is deliberately out of the MVP" line.
- **Would get challenged:** (1) the Transitions card lists "webhook
  signature validation not implemented" among review-carried items but
  does not say it **gates the pilot** — add the B1 gating sentence, spoken;
  (2) there is no privacy disclosure beat — add the B2 line (Meta
  visibility of room photos + retention policy status), spoken, not a
  footnote; (3) the Summary's "92 tests green" is fine, but a savvy
  viewer will ask about concurrency — the M1 "renders untested under
  concurrent load" line belongs in Transitions.
- The Ask (§6) is well-formed; add the B1 condition ("approve MVP scope
  conditional on signature validation landing before first real
  prospect") so approval cannot be read as approving an unauthenticated
  public webhook.

---

## Summary of asks

1. **Blockers:** (B1) move webhook signature validation into MVP scope,
   gate pilot approval on it; (B2) privacy posture before first real
   photo — written retention/deletion policy + working deletion path as
   MVP "must be true," plus spoken disclosure that room photos transit
   Meta's infrastructure; (B3) scheduled + rehearsed backup/restore for
   DB and media store with ref-integrity check.
2. **Majors:** (M1) concurrent-render load gate + multi-window cost
   sensitivity for v1.2; (M2) pilot ops/alerting floor and v1.2 SLO gate;
   (M3) bound the attribution bias in the v1.2 growth gates; (M4) secret
   rotation + custody note.
3. The v3 video plan survives scrutiny with three additions to
   Transitions/Ask: B1 gating language, the B2 privacy disclosure, and
   the M1 concurrency caveat.
