# Senior Engineer Review — v3 Milestone Package (RoomLens)

**Verdict: NEEDS WORK**

Persona: Senior Engineer. Rubric: narration vs. code fidelity; dishonest
simplifications; skipped failure modes. Method: read `docs/milestones.md`,
`docs/business-plan.md`, `docs/videos/v3-presentation-plan.md`, plus
`docs/ARCHITECTURE.md`; spot-checked `src/main.py`, `src/marketing.py`,
`src/handlers/prospect.py`, `src/composite.py` (`assess_quality`), `src/media.py`
(`FakeWhatsAppMedia`), `locustfile.py`, `docs/SCALE.md`,
`docs/how-to/media-retention.md`, `.github/workflows/loadtest.yml`,
`docker-compose.yml`, and `docs/evidence/*`. Verified ground truths: 92 passed
+ 1 skipped per `docs/evidence/test-run-2026-09-07.log`; no
`X-Hub-Signature-256` verification in `src/main.py`; SCALE.md's ~35 req/s is
single-worker with multi-worker explicitly untested ("Honest limits").

Blockers: **none.** Findings are doc/code-fidelity issues; the underlying
engineering (state machine, compositing, quality gate, stateless webhook) is
honestly represented.

---

## Blockers

None. Nothing found that misrepresents a shipped engineering capability as
working when it is not.

## Major

### M1 — SCALE.md's load-test workload claim overstates what the image path exercised; the "not the bottleneck" line is unearned

- **Doc + section:** `docs/SCALE.md`, "Load test setup": "Workload: … 20% image messages (room-photo path)"; and "Honest limits": "The composite/render path (Pillow + ffmpeg) was not the bottleneck here."
- **What actually happened in the load run:** `locustfile.py` sends image messages with `media_id = "loadtest-media"`. The app runs without `WHATSAPP_TOKEN` (per the SCALE.md reproduce steps, only `DATABASE_URL` is set), so `build_runtime()` wires `FakeWhatsAppMedia`, whose registry is never populated in the load test. `FakeWhatsAppMedia.download("loadtest-media")` raises `RuntimeError("Unknown test media id")` (`src/media.py:133–137`); the prospect photo handler catches *any* download failure and replies with the retake ask (`src/handlers/prospect.py:112–114`: "any download failure = retake ask"). So all ~20% of "image" traffic exercised the *download-failure → retake* path. `assess_quality` (the real quality gate) and `render_visualization` (Pillow + ffmpeg) **never executed** in the load test — there were no image bytes to assess or composite.
- **Expectation violated:** a load-test doc must describe what the measured traffic actually did. "The composite/render path … was not the bottleneck here" implies the render path ran and performed adequately; it did not run. The ~35 req/s figure is measured for text traffic plus failed-download image traffic, not for the compositing workload the funnel actually performs.
- **Fix:** either pre-register a real fixture image (`media.register("loadtest-media", <bytes>)`) in the load run so the quality gate + render path are genuinely exercised, or narrow the claim: "image traffic exercised only the download-failure/retake path; render throughput under load is unmeasured."
- **Contagion:** `docs/videos/v3-presentation-plan.md` §3 claim-to-evidence row 8 ("~35 webhook req/s, 0 failures, single worker … `docs/SCALE.md` measured table") inherits this overclaim verbatim.

### M2 — Marketing fan-out sends template messages in an unthrottled loop; the failure mode is undisclosed in ARCHITECTURE

- **Code fact:** `src/marketing.py::send_marketing` (lines 43–52) loops over prospects and calls `wa.send_template(...)` per recipient — no batching, no per-second rate control, no delivery-receipt tracking, no retry/backoff on Meta rate-limit errors. This is the exact pattern BiteFlow's ARCHITECTURE §10 explicitly discloses for its own campaigns ("no batching, no per-second rate control, no delivery receipts").
- **Doc + section:** `docs/ARCHITECTURE.md`, "Outbound templates" describes `marketing.send_marketing` as "the single choke point" — language implying safety — but names none of the throttle/observability gaps. `docs/business-plan.md` §7 risk 5 covers template-approval delays but not send-side rate limiting. The repo has no "Deliberate simplifications" section (BiteFlow has ARCHITECTURE §10); the only signature-verification disclosure lives in `docs/DEPLOYMENT.md` line 83.
- **Expectation violated:** a failure mode the code demonstrably has (unbounded template fan-out against Meta Cloud API rate limits — ~80 msg/s tier-dependent for template sends) must be named where the docs describe that code path as production-shaped. A designer with a few hundred opted-in prospects can get throttled mid-campaign with no visibility into partial delivery.
- **Fix:** add a "Deliberate simplifications / honest limits" section to ARCHITECTURE.md covering: (1) campaign sends are an unthrottled loop, no per-second rate control, no delivery receipts, no retry; (2) webhook signature validation not implemented (currently only in DEPLOYMENT.md checklist). Mirror the BiteFlow §10 discipline.

## Minor

### m1 — Handler errors silently drop the user's message; the docs name the mechanism but not the consequence

- **Code fact:** `src/main.py:144–146` catches every handler exception, prints `[roomlens] handler error …`, and returns `{"ok": True}`.
- **Doc + section:** `docs/ARCHITECTURE.md`, "Webhook flow": "the webhook still returns 200 — Meta retries aggressively on non-2xx, so failing loudly would replay the same message." The mechanism is documented; the consequence is not: because a 200 was returned, Meta will *not* retry, and the prospect receives *no reply at all* — the message is dropped. There is no fallback "sorry, try again" reply and no dead-letter count.
- **Expectation violated:** failure-mode documentation should state the user-visible outcome, not just the engineering rationale. Add: "on handler error the user gets no response; monitor `[roomlens] handler error` logs."
- **Note:** the same pattern exists in BiteFlow (`docs/SCALE.md` notes "HTTP 200 is not proof of success" and the load-test workflow greps for handler errors). BiteFlow at least documents the monitoring expectation; RoomLens's `loadtest.yml` does *not* grep server logs for handler errors, so the load run's "0 failures" is HTTP-status only.

### m2 — Order/consult taps write state but the money story is only in prose

- **Doc + section:** `docs/business-plan.md` §1: "In this build the platform takes no commission: the tap writes an order row and notifies the designer" — verified against `src/handlers/prospect.py:245` (`ctx.db.create_order(...)`) plus `_notify_designer`. Accurate.
- **Expectation violated:** none. Listed here only because it is the highest-stakes fidelity check on this repo and it passes — the v1→v2 round's killed commission claim stays dead, and the v3 plan's non-goal #6 ("never says 'pay' where the code says 'notify'") is honored in the plan text.

---

## Rubric checklist

- **(a) Business-plan cost/infra story vs. architecture:** MATCHES. Business-plan §5 ("one Python container + one PostgreSQL 16 container — **measured** (`docker-compose.yml`)") verified against `docker-compose.yml` (`app` + `db`, Postgres 16-alpine). Media-retention how-to exists (`docs/how-to/media-retention.md`); the plan honestly notes it covers mechanics, not policy, and business-plan §7 risk 6 requires a written retention/deletion policy by v1.2. WhatsApp conversation cost is correctly framed as per-*prospect-funnel* (multi-message preview loops can span 24h windows) with the rate card to be read at pilot time — no price quoted.
- **(b) Presentation plan vs. actual code behavior:** FIDELITY HOLDS with one inheritance. The claim-to-evidence map verified: 92 passed / 1 skipped ✓ (`test-run-2026-09-07.log`), engine-output transcript real ✓, preset placement not-AR ✓ (matches `src/composite.py` + placements JSON in evidence), no background removal ✓ (A22 patch honored), quality-gate tests real ✓ (`assess_quality` implements brightness/blur/size thresholds — a real gate, not a stub), ~35 req/s single-worker / multi-worker untested ✓. The v2 overclaims ("placing the furniture by hand", "scaling is just adding workers") are explicitly corrected. **Inheritance:** §3 row 8 cites `docs/SCALE.md` verbatim — see M1; fix SCALE.md and the row heals.
- **(c) Skipped failure modes:** M1 (load-test image path), M2 (unthrottled template fan-out), m1 (silent message drop on handler error). Disclosed: signature verification (DEPLOYMENT.md + v3 plan transition — should move into ARCHITECTURE per M2), synthetic fixtures (milestones gap #1 + v3 plan A4 disclosure), attribution leakage (business-plan §7 risk 2), escrow burden (risk 3), media liability (risk 6).
- **(d) Dishonest simplifications in milestones:** none found. Milestones' label discipline (implemented / assumption / gap) matches the code: gap #1 (synthetic fixtures) and gap #2 (no monetization capture) are accurately stated; "NOT AR" is enforced consistently across milestones, business plan, ARCHITECTURE, and the v3 plan.

---

*Reviewed 2026-09-07. Independent review; no coordination with other personas.*
