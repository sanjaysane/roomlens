# RoomLens v3 review triage — accept / reject / defer per finding

Date: 2026-09-07. Triage owner (Phase 3b). Scope: all seven v3 persona
reviews in `docs/review-loop/reviews/v3/`.

## Verdict tally (confirmed while reading)

| Persona | Verdict |
|---|---|
| qa-analyst.md | SHIP |
| senior-engineer.md | NEEDS WORK |
| senior-technical-leader.md | NEEDS WORK |
| product-manager.md | NEEDS WORK |
| external-user.md | NEEDS WORK |
| vc.md | NEEDS WORK |
| board-director.md | SHIP |

**RoomLens: 5× NEEDS WORK + 2× SHIP (QA Analyst, Board Director).**
Confirmed as briefed.

## Triage rule applied

Framework rule: *"Fix in v3 what the video/docs can fix; disclose what the
code can't."* The only acceptable rejections are ones that would require
faking output or inventing numbers. The framework forbids silently
overruling a blocker — every rejected/deferred finding carries a written
reason below. Cross-persona duplicates are merged into single fix IDs
(shown as e.g. `QA m1 + BD m1 → F-01`).

**Fix-ID groups:** (A) code fixes · (B) doc fixes (milestones /
business-plan / SCALE / ARCHITECTURE / DEPLOYMENT / TROUBLESHOOTING /
CI config) · (C) v3-presentation-plan fixes. **🎬 VIDEO-BLOCKING** = the
v3 video build would otherwise narrate or show something false.

---

## Accepted fixes

### F-01 (B) — Correct "85 keys" → "87" (business-plan §1 + plan §3 claim map)
- **Findings:** QA m1 + BD m1.
- **Verified:** JSON parse — `locales/en.json`, `es.json`, `hi.json` each
  hold **87** keys; `mr.json` holds 46. `business-plan.md:46` says "85
  keys each"; `docs/videos/v3-presentation-plan.md:245` repeats "85 keys".
  The parity claim is true (`test_key_parity` passes) — only the hard
  number drifted after keys were added.
- **Change:** "85" → "87" in both files, or drop the count and cite
  `test_key_parity` instead.

### F-02 (B + C) — 🎬 Fix SCALE.md's load-test workload claim; plan row 8 inherits it
- **Finding:** SE M1.
- **Verified:** `docs/SCALE.md` "Load test setup" claims "20% image
  messages (room-photo path)" and "Honest limits" says "The composite/render
  path (Pillow + ffmpeg) was not the bottleneck here." But `locustfile.py`
  sends `media_id = "loadtest-media"`, the run wires `FakeWhatsAppMedia`
  (no `WHATSAPP_TOKEN`), whose registry is never populated —
  `FakeWhatsAppMedia.download("loadtest-media")` raises
  `RuntimeError("Unknown test media id")` (`src/media.py:133–137`), and the
  prospect handler catches any download failure and replies with the retake
  ask (`src/handlers/prospect.py:112–114`). So the ~20% "image" traffic
  exercised the **download-failure → retake** path; `assess_quality` and
  `render_visualization` **never executed**. The ~35 req/s figure is
  measured for text traffic + failed-download image traffic, not for the
  compositing workload the funnel actually performs.
- **Change (B):** either pre-register a real fixture image
  (`media.register("loadtest-media", <bytes>)`) in the load run so the
  quality gate + render path are genuinely exercised (preferred, real
  measurement), or narrow the claim to "image traffic exercised only the
  download-failure/retake path; render throughput under load is
  unmeasured." **(C):** plan §3 row 8 (`v3-presentation-plan.md:239`)
  cites SCALE.md verbatim — it heals automatically once SCALE.md is fixed,
  but the row must be re-checked at build time.
- **Video-blocking:** the plan currently repeats the overclaim.

### F-03 (B) — ARCHITECTURE.md += "Deliberate simplifications / honest limits"
- **Finding:** SE M2.
- **Verified:** `src/marketing.py::send_marketing` (lines 43–52) loops over
  prospects calling `wa.send_template(...)` per recipient — no batching, no
  per-second rate control, no delivery-receipt tracking, no retry/backoff
  on Meta rate-limit errors. ARCHITECTURE's "Outbound templates" calls it
  "the single choke point" — implying safety — while business-plan §7
  risk 5 covers template-approval delays but not send-side rate limiting.
  The repo has no "Deliberate simplifications" section; signature
  verification lives only in DEPLOYMENT.md line 83.
- **Change:** new ARCHITECTURE.md section covering (1) campaign sends are
  an unthrottled loop (no per-second rate control, no delivery receipts, no
  retry) and (2) webhook signature validation not implemented — mirroring
  BiteFlow's ARCHITECTURE §10 discipline.

### F-04 (B) — Name the silent-drop consequence; make the load workflow grep logs
- **Finding:** SE m1.
- **Verified:** `src/main.py:144–146` catches every handler exception,
  prints `[roomlens] handler error …`, returns `{"ok": True}`.
  ARCHITECTURE documents the mechanism ("Meta retries aggressively on
  non-2xx, so failing loudly would replay") but not the user-visible
  consequence: Meta will *not* retry a 200, so the prospect receives **no
  reply at all** — the message is dropped, with no fallback reply and no
  dead-letter count.
- **Change:** add to ARCHITECTURE "Webhook flow": "on handler error the
  user gets no response; monitor `[roomlens] handler error` logs." And
  `.github/workflows/loadtest.yml` must grep server logs for handler
  errors — the load run's "0 failures" is currently HTTP-status only.

### F-05 (B + C) — 🎬 Webhook signature validation → MVP scope; conditional approval; Known gap #4
- **Findings:** STL B1 + BD m2.
- **Verified:** SECURITY.md states `POST /webhook` does not validate
  `X-Hub-Signature-256`; DEPLOYMENT.md's production checklist says
  "Implement it before exposing the webhook publicly." But milestones.md's
  MVP scope does not include it — the MVP asks the board to approve real
  prospects sending real room photos to a publicly exposed, unauthenticated
  webhook. A forged payload can trigger renders (compute cost), fire
  outbound WhatsApp sends (Meta conversation charges — business-plan §5's
  binding cost line), and spam `STOP` against a designer's opted-in base.
  BD m2 adds the cross-doc gap: milestones' Known gaps list only synthetic
  fixtures / no monetization capture / Marathi partial — the video plan's
  Transitions card carries the signature gap, so a milestones-only reader
  never sees it.
- **Change (B):** add webhook signature validation as milestones Known gap
  #4 (one line, mirroring BiteFlow's gap #2) **and** into MVP "In scope"
  before first real prospect; board approval conditional on it. **(C):**
  Transitions already give the gap spoken airtime — add the gating
  sentence; the §6 Ask states the condition out loud ("approve MVP scope
  conditional on signature validation landing before first real prospect").
- **Video-blocking:** without the gating language, approval can be read as
  approving an unauthenticated public webhook.

### F-06 (B + C) — 🎬 Privacy posture before first real photo; spoken Meta-visibility disclosure
- **Findings:** STL B2 + VC m2 (folded).
- **Verified:** the MVP's core action is prospects sending photos of their
  homes — sensitive PII (interiors reveal wealth, occupants, children,
  location cues). Current state: `docs/how-to/media-retention.md` is
  mechanics + suggestions ("ships no automatic deletion"); business-plan
  §7 risk 6 pushes the retention/deletion policy to **v1.2** — but the
  pilot (MVP) is when real photos first arrive. Nowhere disclosed:
  WhatsApp Cloud API business messages are not end-to-end encrypted the
  way consumer chats are — room photos transit Meta's infrastructure and
  are visible to Meta.
- **Change (B):** move the retention/deletion policy from "by v1.2" to a
  milestones "what must be true" item for MVP — written policy + working
  deletion path (the media-retention.md procedure, implemented and tested,
  not just documented), with a **named owner and a dated deadline**
  ("before first paid pilot", not "by v1.2"). **(C):** one spoken
  Transitions line: room photos travel over WhatsApp Business messaging
  and are visible to Meta; the product additionally stores originals and
  renders per the retention policy. A production-savvy viewer asks exactly
  this.
- **Video-blocking:** the spoken disclosure.

### F-07 (B) — Scheduled + rehearsed backup/restore for DB and media store
- **Finding:** STL B3.
- **Verified:** DEPLOYMENT.md's checklist ends with "Back up the DB and the
  media volume/store on a schedule" — unchecked, unscheduled, untested. The
  media store holds irreplaceable customer originals; the DB holds the refs
  — a ref without its file (or file without ref) is silent corruption.
- **Change:** milestones "what must be true" (or v1.2 growth gates at the
  latest): scheduled backups + a rehearsed restore documented in
  TROUBLESHOOTING.md, including a media-ref integrity check.

### F-08 (B + C) — 🎬 Concurrent-render load gate + multi-window cost sensitivity
- **Finding:** STL M1.
- **Verified:** SCALE.md is candid ("The composite/render path … was not
  the bottleneck here; it will be if many visualizations render
  concurrently") but the #1 product action (rendering) has no concurrency
  characterization — concurrent Pillow/ffmpeg renders on a single worker
  will queue behind webhook traffic. Business-plan §6 has no sensitivity
  case for funnels spanning 2+ conversation windows (the plan itself notes
  a chatty preview loop can span multiple 24h windows).
- **Change (B):** v1.2 growth gates += concurrent-render load test (e.g. N
  simultaneous visualizations, p95 render latency + zero webhook handler
  errors); §6 += a sensitivity row for funnels spanning 2+ conversation
  windows. **(C):** Transitions disclose that renders are untested under
  concurrent load.
- **Video-blocking:** the Transitions disclosure.

### F-09 (B + C) — Pilot ops/alerting floor; v1.2 SLO gate; ffmpeg self-check
- **Findings:** STL M2 + STL m2b (folded).
- **Verified:** TROUBLESHOOTING.md documents `/health` p50 ~1.5s under load
  and advises "run more workers or lengthen the timeout" — good
  troubleshooting, not an ops plan. No alerting on handler errors, no
  render-failure alerting, no on-call. At 10x designers, a dead worker
  silently drops a designer's entire lead pipeline — and the lost asset (a
  prospect who sent a room photo and heard nothing) is trust lost for the
  *designer's* business. TROUBLESHOOTING.md also documents that
  ffmpeg-missing silently degrades video to "send a still photo" with no
  alert.
- **Change (B):** milestones states the pilot ops floor (alert on
  `[roomlens] handler error`, named human during business hours); v1.2
  gates += SLO/alerting definition; add a startup self-check that fails
  loudly if ffmpeg is absent when video is enabled. **(C):** one spoken
  Transitions sentence disclosing the current state.

### F-10 (B) — Bound the attribution bias in the v1.2 growth gates
- **Finding:** STL M3.
- **Verified:** business-plan §7 risk 2 names the bias exactly ("the
  designer has a direct financial incentive to under-report"); milestones
  accepts manual self-reporting for MVP — defensible for the pilot, but
  the v1.2 decision (lead fee vs take-rate) is gated on "contact → booking
  conversion measured and stable" measured by the party being measured.
- **Change:** v1.2 growth gates += an attribution-integrity check (e.g.
  spot-audit designer-reported outcomes against in-chat "talk to the
  designer" taps, or require the platform-observed conversion event before
  the lead-fee model can be selected — which business-plan §7 already
  implies; make it a gate, not an implication).

### F-11 (B) — DEPLOYMENT.md: secret rotation + custody note
- **Finding:** STL M4.
- **Verified:** the production checklist covers unique-per-environment
  verify tokens and tokens-in-environment — placement is solid; rotation
  cadence, who holds Meta app admin, and pilot-vs-production Meta app
  separation are missing (TROUBLESHOOTING.md documents the 401 token-failure
  mode; business-plan §5 has ops helpers doing catalog cutouts at 10x).
- **Change:** short rotation + custody note in DEPLOYMENT.md. Low effort.

### F-12 (C) — Transitions: opt-outs are currently unauthenticated
- **Finding:** STL m1.
- **Verified:** DEPLOYMENT.md's checklist names forged-`STOP` spam as an
  impact of the missing signature validation; `STOP` handling itself is
  tested.
- **Change:** one line in Transitions: opt-outs are currently
  unauthenticated. Closes automatically once F-05 lands.

### F-13 (C) — Demo frames show Marathi fallback strings verbatim
- **Finding:** STL m2.
- **Verified:** handled by the plan's non-goal #7 and claim map; the plan's
  verbatim-output rule covers it.
- **Change:** a rendering note in the plan: a Marathi-speaking viewer will
  notice fallback English strings — the render pass must never "clean up"
  a frame. Plan discipline, not a code change.

### F-14 (C) — 🎬 Walk the conversion beat: order confirm → placed → tracking
- **Findings:** PM M1 + EU M3.
- **Verified against the plan:** §2 walks designer onboarding → catalog add
  → prospect photo → placement → localized preview delivery (frames 1–6),
  then jumps to DB records (frame 7) and the photo quality gate (frame 8).
  The §2 purpose ends at "prospect receives the preview → prospect
  responds" and lists the four prospect options ("1. Order it", "2. Change
  the placement", "3. Change the product", "4. Talk to the designer")
  without walking any of them — but the MVP is literally named "First paid
  consultation" and its done criteria are ≥15% prospect→designer contact
  and ≥1 paid consultation attributed. The mechanics exist and are
  documented (`docs/how-to/first-visualization.md` Scene 5; `docs/how-to/
  designer-onboarding.md` Scene 5) but are never scheduled on screen. A
  pitch whose walkthrough stops one tap before the MVP's own money moment
  leaves the board unable to evaluate the conversion loop the milestone is
  named for.
- **Change:** extend §2 with one conversion beat end-to-end: prospect
  replies `1` → quote → confirm → order placed (with the F-22 payment
  line) → order tracking view, plus the designer's order-queue status
  update. This proves the MVP is a *commerce* loop, not a render demo.

### F-15 (C) — 🎬 Cut §2 to 5–6 beats; merge the two prospect flows
- **Finding:** PM M2.
- **Verified:** §2 schedules eight distinct beats in 6:00 (~45 s/beat) —
  tighter per-beat than the v2 script the plan criticizes for rushing at
  0:42/scene — contradicting the plan's own "pacing fix is structural, not
  cosmetic" framing and leaving no room for the F-14 conversion beat.
- **Change:** cut §2 to 5–6 beats max: merge the English and Marathi
  prospect flows into one complete flow + one held Marathi localization
  proof frame (the Marathi strings are required as locale-parity proof,
  not the full duplicated flow). Give the recovered ~2 minutes to F-14.

### F-16 (B) — Split v1.2: un-bundle the conditional escrow build
- **Finding:** PM M3.
- **Verified:** `docs/milestones.md` v1.2 "In scope" bundles (a)
  payment/escrow rail *after an explicit decision* (take-rate vs
  qualified-lead fee), (b) customer reviews, (c) style quiz + saved boards,
  (d) perspective/lighting correction, (e) designer CRM lite. Item (a)
  alone is a licensing/KYC/dispute-handling project — the business plan
  (§3 "Where it breaks") says operating escrow brings licensing, KYC,
  dispute handling, and settlement risk (India PA/PG, US money-transmitter),
  and "10–15% looks generous until one dispute consumes it." And (a) is
  *conditional*: if pilot data picks the qualified-lead fee, the escrow
  rail is never built — so the milestone's largest work item may evaporate
  at the decision gate. You cannot staff, budget, or sign off on a
  milestone whose biggest component might not exist.
- **Change:** v1.2a = platform-observed conversion event + lead-fee
  plumbing + CRM lite + reviews (lead-fee path and shared tooling);
  v1.2b = escrow rail, gated on an explicit board decision *for* the
  take-rate model from measured conversion data; style quiz / saved boards
  become their own optional v1.3.

### F-17 (B) — Rename "Consultation booking" → "consultation request + lead handoff"
- **Finding:** PM m1.
- **Verified:** milestones MVP in scope #4 says "Consultation booking +
  lead handoff with designer contact"; the product behavior is a tap that
  writes an order row and notifies the designer (`src/handlers/
  prospect.py:245` + `_notify_designer`) — no time-slot, calendar, or
  scheduling step. The plan's §4 non-goal ("The booking tap writes an order
  row and notifies the designer") already says this correctly.
- **Change:** milestones MVP in scope #4 → "consultation request + lead
  handoff" so the pilot team and board don't over-read the feature.

### F-18 (B) — Update "Still open (v3 round)"
- **Finding:** PM m2.
- **Verified:** `docs/milestones.md:83` lists `docs/business-plan.md` and
  the v3 pitch video as open, but both exist dated 2026-09-07 (same
  staleness pattern as the BiteFlow repo).
- **Change:** the section reflects what is actually still open — the board
  review itself.

### F-19 (A) — 🎬 Localize the quote "Total" label (`src/pricing.py:95`)
- **Finding:** EU B1 (v1 M3, now enshrined in the plan's own claim map).
- **Verified:** `src/pricing.py:95`:
  `f"Total — {format_money(quote['total_cents'], currency)}"` renders inside
  `p_order_confirm` for **every** locale; the plan's §2 frame 7 and §3 claim
  map show the "rendered for mr viewer" quote as `Aria Chair × 1 —
  ₹189.00 / Total — ₹189.00` (also `docs/evidence/engine-output-2026-09-07.
  log` lines 337–338, 351–352). This is the money screen; "Total" is plain
  English, and the plan's §2(4) claims the Marathi frames were reviewed for
  "natural Marathi, never translated word-for-word" — contradicted by its
  own evidence frame.
- **Change:** a localized total label — "एकूण" for Marathi; check `en`,
  `es`, `hi` too. Real code change, not a render patch.
- **Video-blocking:** the quote frame is plan evidence.

### F-20 (A) — Localize order-tracking statuses; fix the "received" semantics
- **Finding:** EU B2 (v1 M4, unfixed).
- **Verified:** `src/handlers/prospect.py:271–281` (`handle_tracking`)
  renders `f"#{o['id']}: {o['status'].replace('_', ' ')} — …"` inside
  `p_tracking` ("📦 तुमच्या ऑर्डरी:") for every locale — a Marathi prospect
  sees `#5: received — ₹189.00`. `src/handlers/designer.py:415–421` sends
  `p_tracking_update` with the raw status to the prospect too. Two
  problems: English in a Marathi chat, and "received" is backwards from the
  prospect's point of view (she received nothing — the *designer* received
  *her* order).
- **Change:** per-locale status strings ("ऑर्डर मिळाली", "तयार होत आहे",
  …); the prospect-facing wording speaks to the prospect. Currency was
  localized; the status — the word that tells the user what is happening
  to her order — must be too.

### F-21 (A) — `locales/mr.json` `p_no_open_orders`: "उघडी ऑर्डर" → "चालू ऑर्डर"
- **Finding:** EU B3.
- **Verified:** "सध्या तुमची कोणतीही **उघडी ऑर्डर** नाही." — "open orders"
  translated word-for-word, the exact failure class the v1 board caught in
  BiteFlow's "उघड्या ऑर्डरी पहा". (Note: `d_new_order`'s "ऑर्डर्स उघडा"
  uses "उघडा" correctly as the verb — fine.)
- **Change:** "सध्या तुमची कोणतीही **चालू ऑर्डर** नाही."

### F-22 (A) — 🎬 Tell the prospect how she pays: payment line in `p_order_placed`
- **Finding:** EU M1 (v1 M6, unfixed).
- **Verified:** `p_order_confirm` → `p_order_placed`
  ("🎉 ऑर्डर #{order_id} झाली! डिझायनर लवकरच डिलिव्हरीची माहिती देईल.")
  — no locale contains a payment line anywhere in the confirm/placed
  sequence. Pressing "ऑर्डर पक्की करा" on a ₹189 order yields
  congratulations with nobody saying when money leaves her hands or how.
  The plan's §4 explains "the designer is paid directly, off-platform" to
  the **board**; the prospect in the chat is never told.
- **Change:** one line on `p_order_placed` — e.g. "पैसे डिझायनरला थेट द्या
  — अ‍ॅप मध्ये पैसे घेत नाही" (pay the designer directly; the app takes
  no money). Marathi at minimum; mirror in other locales.
- **Video-blocking:** the F-14 conversion beat lands on this screen.

### F-23 (C) — 🎬 Frame the opening renders as expectation, not as the value proof
- **Finding:** EU M2 (stays major, not a blocker — milestone gap #1 owns it).
- **Verified:** `docs/evidence/viz-asha-aria-chair.jpg` and
  `viz-marathi-user-aria-chair.jpg` both show a flat brown rounded
  rectangle with "Aria Chair" in English under an English header ("Your
  room, with our furniture: Aria Chair — $189.00"); the Marathi caption is
  Marathi but the picture is the thing the viewer looks at hardest. The
  plan's §2(2) opens with these two renders as the first visual proof with
  only a "sample photos" disclosure caption.
- **Change:** plan §2(2) carries the expectation framing on the opening
  frames themselves — "illustrative preview, not to scale, not AR" (the
  milestones' honest framing) — not just "sample photos"; and the §1 intro
  stakes the value claim on the *funnel* (photo → preview → contact), not
  on render realism. The pilot's 20-photo quality bar (gap #1) remains the
  mechanism for the underlying risk.
- **NOT changed (see R-01):** the renders are not regenerated or retouched.

### F-24 (A) — Marathi button/register polish (`d_studio_adjust`, catalog strings)
- **Finding:** EU minors (v1 minors, unfixed).
- **Verified:** `d_studio_adjust`: "3️⃣ परफेक्ट — ग्राहकाला पाठवा" —
  English wearing Devanagari clothes on a button → "छान! ग्राहकाला पाठवा"
  or "मस्त — ग्राहकाला पाठवा". Catalog strings (`d_studio_pick_product`
  "ठेवण्यासाठी उत्पादन निवडा", `d_cat_name_ask` "उत्पादनाचं नाव काय?",
  `d_catalog` "तुमचा कॅटलॉग") use textbook "उत्पादन" where chat Marathi
  says "वस्तू".

### F-25 (B + C) — 🎬 §6 lead-fee table: print the true computed ranges
- **Finding:** VC B1.
- **Re-run confirmed from the plan's own assumptions:** India — gross
  ₹300–600/converted lead; costs ₹5–15 × ~7 prospects = ₹35–105 plus
  attribution/chasing labor ₹50–150 → contribution **₹45–515**. Plan states
  "≈ ₹150–400" — narrower than the assumption envelope on both ends. US —
  gross $25–60; costs $3.50–14 + $5–15 = $8.50–29 → contribution
  **−$4 to +$51.50**. Plan states "≈ $10–40" — hiding the material fact
  that the US low-end case is **negative per converted lead**.
- **Change:** reconcile — either tighten the input assumptions or print the
  true computed ranges (IN ≈ ₹45–515, US ≈ −$4 to +$52). **(C):** the
  plan's §4 on-screen ranges must match the corrected table; the negative
  US tail stays on the page. Until fixed the "volume game" has no verified
  floor.
- **Video-blocking:** the business-model section's on-screen numbers.

### F-26 (B + C) — 🎬 Take-rate: state the boundary reversal; counsel sign-off as precondition
- **Finding:** VC B2.
- **Verified:** the package's foundational, thrice-repeated position is
  that the platform never touches customer funds ("keeps the platform out
  of payment-licensing territory… deliberately out of the MVP"). Lead-fee
  preserves that boundary; take-rate requires operating escrow — holding
  project funds of ₹1,00,000–5,00,000 (India) with licensing (PA/PG; US
  money-transmitter), KYC, dispute handling, settlement risk. The plan
  flags this as risk 3 (correctly labeled inference) but milestones, plan,
  and video present it as a symmetric "take-rate vs qualified-lead fee"
  choice with no gate on the asymmetry.
- **Change (B):** (1) state plainly that take-rate reverses the money
  boundary while lead-fee preserves it; (2) add counsel sign-off per market
  as a **precondition** of choosing take-rate, not a post-decision
  implementation detail. **(C):** plan §4 presents the asymmetry, not the
  symmetric "two models" framing — a monetization decision that changes the
  company's regulatory posture is a company decision, not a pricing
  decision.
- **Video-blocking:** the §4 framing.

### F-27 (B) — State the monetization decision rule with numeric thresholds; estimate CAC
- **Findings:** VC B3 + VC M4 (folded).
- **Verified:** milestones v1.2 gates: "Contact → booking conversion measured
  and stable" — no numeric threshold anywhere ("covers CAC +
  conversation costs" is a viability test, not a choice rule, and CAC is
  never modeled). The lead-fee model requires a platform-observed conversion
  event that "does not exist yet — it is v1.2 scope."
- **Change:** state the rule — e.g. "if median project value ≥ ₹X and
  counsel clears custody → take-rate; else lead-fee priced at ≤Y% of
  measured consultation fee." And estimate CAC: the GTM (§4) assumes each
  designer brings their own list (near-zero CAC, unstated); the real proxy
  is designer onboarding labor (studio profile, catalog cutouts, portfolio
  — hours per designer in §5). State the assumption and defend it — a gate
  testing "covers CAC" against an unestimated CAC is untestable.

### F-28 (B) — §6 take-rate table: print the true envelope or state the pairing assumption
- **Finding:** VC M1.
- **Re-run confirmed:** India gross 10–15% × ₹1,00,000–5,00,000 =
  ₹10,000–75,000; escrow 1–3% = ₹1,000–15,000; dispute reserve 1–2% =
  ₹1,000–10,000 → true envelope **−₹15,000 to ₹73,000**. The plan states
  "≈ ₹6,000–60,000" — the printed range quietly drops the negative tail
  while §6's own prose warns "one mishandled ₹5,00,000 escrow dispute wipes
  out the margin of many good deals."
- **Change:** print the true envelope or state the pairing assumption
  explicitly.

### F-29 (B) — Add the honest moat/defensibility section
- **Finding:** VC M2.
- **Verified:** no moat section exists. The product is Pillow/NumPy
  compositing at preset anchors behind a WhatsApp state machine —
  cloneable in weeks; and disintermediation is structural to the channel:
  designer and prospect meet *on WhatsApp* and can transact there forever,
  off-platform, with zero switching cost. The lead-fee model taxes a
  conversion the platform can't observe in MVP (attribution is "manual
  designer self-reporting," and the designer has "a direct financial
  incentive to under-report"). The only named mitigation — a
  platform-observed conversion event — is unbuilt v1.2 scope.
- **Change:** the honest version: execution and distribution play; name the
  structural leak; quantify the leak's tolerance (what under-reporting
  rate kills the lead-fee model?) instead of deferring it to the unbuilt
  event. Connect the two points the plan leaves separate: the
  take-rate/escrow model is the anti-disintermediation answer — at the
  cost of the money boundary (F-26). They are the same decision.

### F-30 (B) — Strengthen the money signal: MVP criteria = demand validation; add a WTP probe
- **Findings:** VC M3 + VC m3 (folded).
- **Verified:** 20+ visualizations, ≥70% completion, ≥15%
  prospect→contact prove the preview converts curiosity into contact — but
  "≥1 paid consultation attributed" (designer-reported, manual) is the
  only money signal, the platform captures none of it, no pricing is set
  anywhere, and zero willingness-to-pay is probed.
- **Change:** (1) minimum consultations per designer (not a single
  attributed consultation across 2–3 designers) as the money gate; (2) a
  directional WTP question to designers during the pilot (what would you
  pay per converted consult?) so v1.2 pricing starts from a stated number,
  not a blank; (3) the ₹2,000–5,000 / $150–400 consultation-fee inputs are
  the least reliable pilot input (designers understate income to a platform
  that might charge a % of it — the same incentive as the attribution
  leak) — cross-check against the attributed-consultation receipts, not
  just designer statements; (4) label the MVP criteria as demand
  validation in §8.

### F-31 (B) — One line: is the monetization decision per market or global?
- **Finding:** VC m1.
- **Verified:** §6 models India and US separately ("never blended"), but
  the decision framework never says whether the models can differ by
  market.
- **Change:** "the monetization decision is made per market" or "one
  global model" — one line removes the ambiguity.

### F-32 (B) — Milestones "Where we are": add the test count
- **Finding:** BD m3 (cosmetic).
- **Verified:** no discrepancy — evidence and video plan agree on 92
  passed / 1 skipped — but BiteFlow's milestones carry a count and
  RoomLens's don't.
- **Change:** "Tests passing (92 passed, 1 skipped — 2026-09-07); Ruff
  clean; CI green."

---

## Deferred (with written reason — not silently overruled)

### D-01 — EU M2 sub-ask: make the preview composites look believable — REJECTED as code work, accepted as plan/disclosure work
- This is a **rejection with reason**, not a deferral: regenerating or
  retouching the viz JPGs to look more believable would be faking the
  product's actual output — exactly what the framework forbids. The
  underlying risk is genuinely owned: milestones gap #1 ("compositing
  quality on real customer room photos is unproven — the #1 expectation
  risk") and the pilot's first job is the 20-photo quality bar. F-23 makes
  the video frame that expectation instead of selling render realism.
- **Reason (one line):** fixing this "finding" would require inventing
  better output than the engine produces; the framework permits only
  disclosure, which gap #1 + F-23 provide.

### D-02 — EU narration-register minor — DEFERRED
- **Reason:** the "Must say" lines are board-register, but the stated
  audience is the board — no register guidance is needed for this cut.
  Guidance is deferred to any future user-facing cut that reuses the
  Marathi frames.

## Verified-clean findings (no action)

- SE m2 — the money story ("the tap writes an order row and notifies the
  designer") is the highest-stakes fidelity check on this repo and it
  passes; the v1→v2 killed commission claim stays dead.
- QA "What verified cleanly" sections, Board claims 1–9, 11–15 — no action.

## Video-blocking summary (must change before the v3 build)

F-02 (plan §3 row 8: SCALE overclaim) · F-05 (Ask gating: conditional
approval) · F-06 (spoken privacy disclosure) · F-08 (Transitions:
renders untested under concurrency) · F-13 (render pass must not clean up
fallback strings) · F-14 + F-15 (walkthrough: add the conversion beat,
cut to 5–6 beats) · F-19 (localized "Total" on the quote frame) · F-22
(payment line on the order-placed screen) · F-23 (opening frames carry
the "illustrative preview, not to scale" framing) · F-25 (on-screen
lead-fee ranges) · F-26 (plan §4: take-rate asymmetry).

## Counts

- Raw findings across 7 reviews: **41** (QA 1, SE 4, STL 10, PM 5, EU 8,
  VC 10, BD 3) — of which 1 (SE m2, the money-story fidelity check) is
  verified-clean, no action.
- Accepted fix IDs: **32** (A: 5 · B: 15 pure-B + 7 spanning B+C ·
  C: 5 pure-C).
- Deferred: **1** (D-02, with reason). Rejected: **1** (D-01, with reason —
  would require faking output).
