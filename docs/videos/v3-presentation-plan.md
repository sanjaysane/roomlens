# RoomLens — v3 pitch video presentation plan (for 7-persona board review)

Date: 2026-09-07. Status: **plan** — input to the v3 review package.
Video bar (non-negotiable): intro → complete unhurried walkthrough of ACTUAL
behavior → transitions → business model → summary → ask, never starting
mid-thought. Every on-screen product pixel is real engine output from the
Phase-1 evidence files below. Total target: **13–15 minutes, unhurried.**

---

## 1. v2 script analysis (what the v2 scripts get wrong for a pitch)

The v2 scripts are *how-to walkthroughs* for three distinct audiences
(customer, designer, deployer). None is a pitch. Against the video bar:

### script-first-visualization.md (~5 min, customer audience)

| Issue | Detail |
|---|---|
| **Thin intro** | Scene 1 gives a 40-second "what this is" — acceptable for a walkthrough, but a board pitch needs the problem (designers lose sales when prospects can't picture furniture in their own room) and the money question up front, not just "let me show you." It never says who pays. |
| **Rushed** | Seven scenes in 5 minutes (0:42/scene). Scene 5 (the reveal — the product's entire value proposition) gets 60 seconds: photo→preview→price→four options→"rough preview not exact measurement" disclaimer, all in one breath. Scene 6 compresses ordering, quote line items, confirmation, and cancellation into **40 seconds**. The money-adjacent beat is the most rushed in the script. |
| **Misleading claim** | Scene 4: "a real designer is placing the furniture by hand." The designer picks a product, a preset anchor (`floor-center`), and a size step (bigger/smaller) via numbered replies — the *engine* does the compositing (Pillow/NumPy at preset anchors, per `docs/milestones.md`). "By hand" overstates the designer's role and understates the automation. Must be corrected to preset-based placement in v3. |
| **Unproven convenience claim** | Scene 3: "you can also send a short video clip — it uses the first frame." Engine support exists (`test_video_frame_extracted_and_accepted` in the test log), but no evidence artifact shows the actual first-frame extraction; fine to keep only with the test-log citation, or cut. |
| **No summary / no ask** | Scene 7 is a 10-second recap card (photo → preview → one digit). No business moment, no ask. |

### script-designer-onboarding.md (~5 min, designer audience)

| Issue | Detail |
|---|---|
| **Starts mid-thought** | Scene 1 assumes the viewer already wants RoomLens ("Today I'll take you from zero to your first sent visualization") — no intro to the problem, no framing of what the designer is buying into. A board member sees catalog clicks before understanding the business. |
| **Rushed** | Scene 3 packs product naming, pricing, size-class, and the cutout-photo step (including the important "we don't do background removal" disclosure) into 75 seconds. Scene 4 packs the entire Studio placement flow plus the "not AR, tell your customers" honesty note into 75 seconds. The disclosures — the parts the Board Director seat cares about most — are the most compressed. |
| **Honest-note handling is good in substance, rushed in pacing** | "we don't do background removal" and "this is a 2D preview, not augmented reality" are the right disclosures (FRAMEWORK.md: "fix in v2 what the video can fix; disclose what the code can't"), but each gets one sentence. v3 must give them spoken time, on a dedicated frame. |
| **No summary / no ask** | Scene 6 recap + "links below" — training-video ending. |

### script-deployment.md (~5 min, deployer audience)

| Issue | Detail |
|---|---|
| **Wrong register for a pitch** | Terminal-first screencast: `docker compose up`, `.env` filling, cloudflared tunnels, template creation. A board pitch shows product behavior, not deployment mechanics. Almost nothing in this script is reusable verbatim for v3; its value is its two measured claims (see below). |
| **Unproven scale claim** | Scene 2: "scaling is just adding workers." Evidence (`docs/SCALE.md`): load tested on a **single worker only**; "Not tested: multi-worker uvicorn." The honest measured statement is "~35 webhook req/s with zero errors on one worker; the app is stateless so workers can be added" — the script's "just" over-claims. The word "just" must die in v3. |
| **Rushed security disclosure** | Scene 6 names the webhook-signature gap in one breath inside a 40-second checklist. v3's Transition section gives it a full spoken beat. |
| **Measurable value** | Scene 6's "thirty-five requests a second on one worker with zero failures" IS backed (`docs/SCALE.md` measured table: 4,183 POSTs, 0 failures, ~35 req/s, 50 users / 2 min). This is v3's strongest performance evidence — reuse with the exact measured qualifiers. |

### Cross-cutting v2 findings (carried as plan constraints)

- The v1→v2 round killed the **commission-as-business-model** narration
  (CHANGELOG A1/A2 — the biggest blocker: the video claimed money flows
  that the code never touches). v3's business section must restate the
  honest position: **no platform take in MVP; lead-fee vs take-rate
  decided from pilot data** (business-plan.md §2).
- Synthetic-media disclosure rule (A4: "Demo uses sample room & product
  photos", on-mic at the viz step + closing card) applies to every frame
  showing `room-asha-original.jpg` / `viz-asha-aria-chair.jpg` /
  `viz-marathi-user-aria-chair.jpg`.
- The surgical A22 narration patch (2026-09-06) corrected RoomLens
  designer-en Step 2: the backend saves the raw photo as-is, **no
  background removal**. v3 uses the corrected line verbatim.
- USD-only currency stays disclosed (triage R5): the evidence shows
  `$189.00` and `₹189.00` renderings from the same quote — the video
  must say prices display in the viewer's locale, USD for English (real
  engine behavior).

---

## 2. v3 narrative structure (13–15 min, unhurried)

Sections follow the mandatory bar: Intro / Walkthrough / Transitions /
Business model / Summary / Ask. v2 averaged ~0.8 min/scene; v3 targets
~2.2 min/section — the pacing fix is structural, not cosmetic.

### Section 1 — Intro (target 2:00)

- **Purpose:** a cold viewer understands the problem, the product, and
  who pays — before any chat or terminal appears.
- **What it PROVES:** the category (WhatsApp-first furniture
  visualization + ordering for interior designers), the zero-client
  thesis (prospect needs no app/account/forms), and the honest product
  boundary stated once, up front: "2D preset-based compositing at fixed
  anchors — this is explicitly not AR, and we never present it as AR."
- **On screen:** title card + the two real composite renders side by
  side — `docs/evidence/viz-asha-aria-chair.jpg` (Asha's room, Aria
  Chair, English) and `docs/evidence/viz-marathi-user-aria-chair.jpg`
  (Marathi user's room) — with the synthetic-media disclosure caption:
  "Demo uses sample room & product photos." Plus the original room photo
  `docs/evidence/room-asha-original.jpg` shown once so the viewer sees
  input → output.
- **Framing on the opening frames themselves (v3 F-23):** each render
  carries the caption "Illustrative preview, not to scale — not AR"
  (the milestones' honest framing), not just "sample photos." And the
  intro stakes the value claim on the **funnel** (photo → preview →
  contact), never on render realism — the pilot's 20-photo quality bar
  (milestones gap #1) is the mechanism for the underlying expectation
  risk.
- **Must say (slowly, once):** every product pixel in this video is real
  engine output (state machine + Pillow/NumPy compositing + the same
  code path as production, sans network). Sample photos are disclosed,
  never passed off as customer photos.

### Section 2 — Walkthrough (target 6:00)

- **Purpose:** the complete loop a real user lives through — ending at the
  MVP's money moment, not one tap before it: designer onboards → lists a
  product → prospect sends a room photo → designer places the product →
  prospect receives the preview → prospect orders → prospect tracks the
  order.
- **What it PROVES:** (a) designer onboarding end-to-end; (b) prospect photo
  flow with the quality gate; (c) preset placement + bigger/smaller adjust;
  (d) localized preview delivery with locale-aware pricing; (e)
  nickname-not-phone-number privacy; (f) the **conversion beat** — quote →
  confirm → order placed (with the payment line) → tracking → designer's
  status update. This proves the MVP is a *commerce* loop, not a render
  demo.
- **On screen, in order — 5 beats (v3 F-15; the EN+MR flows are merged into
  one complete flow + one held Marathi proof frame):**
  1. **Designer onboarding + catalog (~1:00):** `hi` → welcome → `1` →
     "What's your studio name?" → "Casa Studio" → Studio home → catalog add:
     name → `189.00` → size class → cutout photo step (with the corrected
     line: "the backend saves the raw photo as-is — no background removal")
     → "✅ Added: Aria Chair — $189.00". (Evidence: engine-output §1–§2.)
  2. **Prospect photo + quality gate (~1:00):** 'Asha' flow: `hi` → `2` →
     pick designer → nickname prompt → "Asha" → photo prompt →
     `[IMG room_asha]` → designer notified ("📸 New room photo from Asha!")
     → opt-in question → `1` → opted in. Then the quality gate, held
     briefly: dark/blurry/small photos trigger a polite retake — "never a
     misleading overlay." (Evidence: engine-output §3; test log retake
     tests.)
  3. **Studio placement + preview delivery (~1:15):** room list shows
     "📸 Asha" (nickname, not phone); product pick → preset pick
     (`floor-center`) → preview → "1️⃣ Bigger / 2️⃣ Smaller / 3️⃣ Perfect —
     send to prospect" → `3` → the actual composite renders delivered with
     price strips: English "✨ Here's the Aria Chair in YOUR room!
     💰 Price: $189.00" and the Marathi "✨ पाहा, तुमच्याच खोलीत Aria
     Chair! 💰 किंमत: ₹189.00" — each held ≥30 s with the four options
     (including "talk to the designer"). (Evidence: engine-output §5–§6;
     viz JPGs.)
  4. **The conversion beat (~1:30, v3 F-14):** prospect replies `1` →
     quote screen ("🧾 Your order: Aria Chair × 1 — $189.00 / Total —
     $189.00") → `1` confirm → **order placed with the payment line**
     ("🎉 Order #9 placed! … 💳 Pay the designer directly — the app never
     takes your money.") → tracking view ("📦 Your orders: #9: Received
     by the designer — $189.00") → designer opens Orders, sets
     "Preparing" → prospect gets "📦 Order #9 is now: Preparing."
     (Evidence: `docs/evidence/engine-conversion-beat-2026-09-07.log` —
     real engine output on the v3-fixed code.)
  5. **Marathi localization proof frame (~0:45, v3 F-15):** one held frame
     from `docs/evidence/engine-conversion-beat-mr-2026-09-07.log`, shown
     verbatim: "एकूण — ₹189.00" on the quote, and the Marathi payment line
     ("पैसे डिझायनरला थेट द्या — अ‍ॅप मध्ये पैसे घेत नाही."). The Marathi
     strings are required as locale-parity proof, not as a second full
     flow. The render pass must never "clean up" a fallback English
     string in these frames (v3 F-13).
- **Pacing rule:** every frame containing chat text or a render stays on
  screen until the narration has finished describing it. The v2 flaw was
  cutting the reveal and the order beats before the viewer finished
  reading; v3 holds the two preview deliveries a full 30+ seconds each.

### Section 3 — Transitions (target 1:30)

- **Purpose:** the honest bridge — what was shown vs. what a pilot
  still needs — spoken, not flashed.
- **What it PROVES:** the team knows exactly where the demo ends and
  the product work begins.
- **On screen:** a disclosure card listing milestones "Known gaps"
  verbatim (`docs/milestones.md`): (1) **demo fixtures are synthetic** —
  compositing quality on real customer room photos is unproven (the #1
  expectation risk; the pilot's first job is 20+ real photos);
  (2) **no monetization capture** — no platform commission accounting,
  no in-app payment rail; designers are paid off-platform;
  (3) **Marathi parity partial** — English fallback labels; (4) **webhook
  signature validation not implemented** — plus the review-carried items:
  media is sample photos (disclosed), no background removal, USD for
  English viewers (real engine behavior).
- **Spoken, one sentence each (v3 review):**
  - (F-05, gating) "One condition on this approval: webhook signature
    validation lands before the first real prospect — until then the
    public webhook is unauthenticated, and we're asking you to approve
    the scope, not the exposure."
  - (F-06, privacy) "Room photos travel over WhatsApp Business messaging —
    they're visible to Meta, not end-to-end encrypted like consumer chats —
    and the product additionally stores originals and renders under a
    written retention policy with a named owner, before the first paid
    pilot."
  - (F-08, concurrency) "One honest limit: renders are untested under
    concurrent load — the load test never ran the composite path, and the
    concurrent-render characterization is a v1.2 growth gate."
  - (F-09, ops) "Current state, plainly: no alerting on handler errors and
    no on-call — a dead worker silently drops a designer's lead pipeline.
    The pilot ops floor in milestones defines what must exist before the
    first paid pilot."
  - (F-12, opt-outs) "Opt-outs are currently unauthenticated — STOP
    handling is tested, but a forged STOP is indistinguishable from a real
    one until signature validation lands."
- **Duration rule:** each gap gets a spoken sentence. v2 compressed all
  disclosures into 40-second checklists; v3 gives them 90 seconds of
  deliberate airtime.

### Section 4 — Business model (target 2:30)

- **Purpose:** who pays, how money moves today, what the v1.2 candidates
  are, and what the pilot must measure before any pricing is set.
- **What it PROVES:** the money path is understood honestly — every
  number labeled measured / sourced / assumption per
  `docs/business-plan.md`.
- **On screen:**
  - The MVP money-flow diagram (business-plan.md §2): prospect → designer
    (consult fee, direct, off-platform); designer → platform: **nothing
    in MVP** (free, "no monetization capture" accepted).
  - The two v1.2 alternatives (business-plan.md §2–§3): **qualified-lead
    fee** per converted consultation (price TBD from pilot data) OR
    **project take-rate 10–15% via escrow** (**assumption**); the choice
    is made from measured conversion data, not before (milestones
    growth gates).
  - Unit-economics framing (§6, **on-screen ranges match the recomputed
    table — v3 F-25**): lead-fee contribution **₹45–515 per converted lead
    (India) / −$4 to +$52 (US)** — the US low-end case is **negative per
    converted lead**, and it stays on the page; take-rate contribution
    **−₹15,000 to ₹73,000 (India) / −$750 to $3,650 (US)** — the negative
    tail is printed, not hidden. **India and US modeled separately** —
    never blended (milestones requirement).
  - **The asymmetry, stated on screen (v3 F-26):** the lead-fee model
    **preserves** the money boundary — the platform never touches customer
    funds, no payment licensing, no custody. The take-rate model
    **reverses** it — the platform would hold project funds of
    ₹1,00,000–5,00,000 per deal (India), which means licensing (India
    PA/PG; US money-transmitter), KYC, dispute handling, settlement risk.
    A monetization decision that changes the company's regulatory posture
    is a **company decision**, not a pricing decision — and counsel
    sign-off per market is a **precondition** of choosing take-rate, not a
    post-decision implementation detail. The plan does not present these
    as a symmetric "two models" choice.
  - The binding unknowns called out on screen: contact→consultation
    conversion rate (the MVP's explicit measurement goal), Meta
    per-conversation cost (read from the rate card at pilot time), and
    the platform-observed conversion event that the lead-fee model
    requires but doesn't exist yet (v1.2 scope).
- **Must say:** "In this build the platform takes no commission: the tap
  writes an order row and notifies the designer; the designer is paid
  directly, off-platform. Money is deliberately out of the MVP so the
  pilot measures demand, not plumbing."

### Section 5 — Summary (target 1:00)

- **Purpose:** one-minute recap a board member can quote.
- **What it PROVES:** the walkthrough's claims are restatable without
  the demo.
- **On screen:** five bullets: (1) real state machine + compositing
  engine, 97 tests green; (2) prospect photo → preview → quote in the
  prospect's language; (3) honest framing: not AR, sample photos,
  retake-before-mislead; (4) no platform take in MVP — payment stays
  designer↔prospect; (5) monetization decision gated on measured pilot
  funnel.

### Section 6 — Ask (target 1:00)

- **Purpose:** say what the team needs from the board, plainly.
- **What it PROVES:** the pitch ends with a decision request, not a
  fade-out.
- **On screen / spoken:** (1) approve the MVP milestone scope and done
  criteria (`docs/milestones.md`: 20+ real-room visualizations, ≥70%
  photo→preview completion, ≥15% prospect→designer contact, ≥3 paid
  consultations attributed per pilot designer) — **conditional on webhook
  signature validation landing before the first real prospect** (v3 F-05);
  (2) commit 2–3 designers with real catalogs and agreement to report
  consultation outcomes; (3) approve the real-photo quality-bar work (20+
  real photos pre-pilot) as the #1 de-risking step; (4) keep the
  monetization decision (lead fee vs take-rate) gated on the measured
  funnel — and on counsel sign-off per market if take-rate is chosen
  (v3 F-26).

---

## 3. Claim-to-evidence map

Every factual claim the video will make, mapped to its backing.

| Claim (as narrated) | Evidence file / commit |
|---|---|
| 97 tests pass, 1 skipped | `docs/evidence/test-run-2026-09-07.log` (v3-fixed run: `97 passed, 1 skipped`; includes the F-02 fixture-seed, F-09 video self-check, and F-19/F-20/F-22 regression tests) |
| Designer onboarding, catalog add, both prospect flows, studio placement, localized delivery are real engine output on the production code path | `docs/evidence/engine-output-2026-09-07.log` — header: "All text below came from src/state_machine.process_incoming over the fake adapters (same code path as production, sans network)." |
| Composite renders are real engine output | `docs/evidence/viz-asha-aria-chair.jpg`, `viz-marathi-user-aria-chair.jpg` (rendered_ref `local:renders/viz-3-*.jpg` in the log §7); input room `room-asha-original.jpg` |
| Quote totals $189.00 (en) / ₹189.00 (mr) from the same quote row; Marathi receipt reads "एकूण" | `docs/evidence/engine-conversion-beat-2026-09-07.log` (P_ORDER_CONFIRM: "Total — $189.00"); `docs/evidence/engine-conversion-beat-mr-2026-09-07.log` (P_ORDER_CONFIRM: "एकूण — ₹189.00"); `test_quote_lines_text_locale_currency`, `test_quote_total_label_localized` |
| **Conversion beat (F-14):** prospect replies `1` → quote → confirm → order placed **with the payment line** ("Pay the designer directly — the app never takes your money") → tracking view ("Received by the designer") → designer sets "Preparing" → prospect notified ("is now: Preparing.") | `docs/evidence/engine-conversion-beat-2026-09-07.log` — full transcript driven through the real state machine on the v3-fixed code |
| Nickname shown instead of phone; phone fallback | engine-output §5 room list ("📸 Asha" vs "📸 15550003333"), §8 `display_name`; tests `test_studio_room_list_shows_nickname`, `test_designer_notification_falls_back_to_phone` |
| Placement is preset-based (floor-center etc.), sized by fractions of photo width — NOT AR | `docs/milestones.md` "Where we are" + business-plan.md "Honest product boundary"; engine-output §7 placements `preset: 'floor-center', scale: 1.0`; tests `test_each_preset_renders_valid_jpeg[floor-center/left-wall/right-wall/wall-hang]` |
| Dark/blurry/small photos trigger a polite retake, never a misleading overlay | tests `test_dark_photo_triggers_retake`, `test_blurry_photo_triggers_retake`, `test_small_photo_triggers_retake`, `test_quality.py` (all in test log); quality-gate philosophy in milestones |
| ~35 webhook req/s, 0 failures, single worker (50 users, 2 min) — measures the webhook/state-machine path; image traffic in that run hit the download-failure path, and the composite/render path was never exercised (v3 F-02) | `docs/SCALE.md` measured table (4,183 POSTs, 0 failures) + "Honest limits"; fixture seeding (`ROOMLENS_SEED_LOADTEST_MEDIA`) wired into the CI workflow so the next run measures the real download → quality-gate path |
| Opt-in gating for campaigns; STOP opts out instantly | engine-output §3–§4 opt-in transcript; tests `test_stop_opts_out_everywhere`, `test_campaign_suppresses_opted_out` |
| No platform commission or payment rail in this build — tap writes an order row, notifies the designer; designer paid directly, off-platform | business-plan.md §1–§2; review-loop CHANGELOG A1/A2; milestone gap #2 "No monetization capture" |
| v1.2 candidates: qualified-lead fee (TBD) OR 10–15% take-rate via escrow; decision from measured data | business-plan.md §2–§3 (assumption labels); milestones v1.2 |
| Demo photos are sample/synthetic; real-photo quality is unproven (gap #1) | milestones Known gaps #1; review-loop CHANGELOG A4 (synthetic-media disclosure) |
| Backend saves the raw photo as-is; no background removal | surgical narration patch 2026-09-06 (CHANGELOG A22); product code `src/media.py` |
| Locales: en/es/hi full parity (87 keys), Marathi partial with English fallback | business-plan.md §1 (measured); tests `test_key_parity`, `test_mr_is_subset_of_en`, `test_mr_falls_back_to_english_for_missing_keys` |

---

## 4. Explicit non-goals (claim-audit hygiene)

v3 will NOT claim any of the following:

1. **No AR / 3D / perspective language.** The video says "2D preset-based
   compositing at fixed anchors" and corrects the v2 script's "placing the
   furniture by hand" line. No plane detection, no depth, no scale
   guarantee — ever.
2. **No commission or revenue numbers as fact.** 10–15% is an
   **assumption**; lead-fee pricing is **TBD**. No unit-economics table
   without the assumption label on every row. (The v1 commission claim
   that the board killed in the v1→v2 round stays dead.)
3. **No real-customer-photo implication.** Every render frame carries the
   "sample room & product photos" disclosure, on mic at the viz step and
   on the closing card.
4. **No multi-worker scale claim.** "Scaling is just adding workers" is
   replaced with the measured sentence: ~35 req/s, zero failures, single
   worker; statelessness makes adding workers possible, but multi-worker
   is untested.
5. **No Meta rate-card numbers.** Per-conversation cost is "read the rate
   card at pilot time" — quoted nowhere.
6. **No payment or escrow functionality.** The booking tap writes an
   order row and notifies the designer; the video never says "pay" where
   the code says "notify."
7. **No Marathi full parity.** "Partial — English fallback" is stated on
   screen.
8. **No attribution automation.** Consultation attribution is manual
   designer self-reporting in MVP; the video doesn't imply the platform
   verifies conversions (that conversion event is v1.2 scope).

---

## 5. Build notes (for the narration/render pass)

- v3 is a **new script**, not a patch of the three v2 scripts: single
  narrator, single audience (the board), single product story.
- Reuse the corrected v2 phrasing: no background removal (A22 patch,
  2026-09-06); "designer paid directly, off-platform" (A2); synthetic-
  media disclosure on mic at the viz step + closing card (A4).
- Evidence frames are captures of the engine-output transcript, the test
  log, and the rendered JPGs — never hand-written chat text, per the
  FRAMEWORK.md iron rule.
- **Render-pass discipline (v3 F-13):** a Marathi-speaking viewer will notice
  fallback English strings in the Marathi frames (mr is a declared partial
  locale with English fallback — non-goal #7). The render pass must show
  every frame **verbatim as the engine produced it** and must never "clean
  up," retype, or translate a string to make a frame look tidier.
- Caption safe margins and emoji-glyph re-render lessons from v1→v2 (A6)
  apply to every new frame.
- Spot-check against the claim-to-evidence map (§3) before any render:
  every narrated sentence must trace to a row. The v2 round's A22
  misattribution (changelog item pointing at a video that never contained
  the phrase) is the failure mode to avoid: cite the exact file and
  section for every claim.
