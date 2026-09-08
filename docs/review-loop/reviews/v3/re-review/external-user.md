# Re-review sign-off — External User, harshest critic (v3 board-review round)

**Date:** 2026-09-07. **Re-reviewer:** external-user hat (the one who caught the
BiteFlow Marathi regressions). I do not fix — I verify. Marathi strings were
read as a Marathi reader would read them, not translated word-for-word.
**Test suite run independently:** 97 passed, 1 skipped; `ruff` clean.

## Overall sign-off: **CHANGES STILL NEEDED**

The five code fixes (F-19–F-24) are real and the Marathi reads natural —
nothing here regresses the way the BiteFlow ship did. 31 of 32 accepted fixes
confirmed. But F-06 does not clear: the repo still has **no named owner and no
implemented, tested deletion path** — the two concrete protections the triage
demanded before real home photos are collected. A gate that says "must exist
before the first paid pilot" is the right shape; an empty gate is not a fix.

## Per-fix-ID table

| Fix ID | Verdict | One-line evidence |
|---|---|---|
| F-01 | confirmed | No "85" anywhere: business-plan §1, ARCHITECTURE i18n table, TROUBLESHOOTING, plan claim map all say 87; JSON count en/es/hi = 87, mr = 46 declared partial — the numbers are now honest |
| F-02 | confirmed | SCALE.md admits the 09-05 run never exercised render; plan row 8 now quotes the qualified claim with the honest-limits pointer — no more phantom composite throughput |
| F-03 | confirmed | ARCHITECTURE "Deliberate simplifications" names the unthrottled marketing loop and the missing signature check — reads like an honest engineering doc now |
| F-04 | confirmed | The consequence is finally stated: handler error → 200 → Meta won't retry → the user hears nothing; load workflow greps the log and fails loud |
| F-05 | confirmed | Gap #4 in milestones, MVP in-scope item, gating sentence in Transitions, §6 Ask states conditional approval out loud — the board cannot read this as approving an open webhook |
| F-06 | **REJECTED (partial)** | Moved to MVP gate with deadline ✓, spoken Meta-visibility disclosure ✓ — but *who* owns the retention policy? No name anywhere. *Where* is the deletion code? Only the procedure doc; zero tests. Two explicit criteria from the triage are unverifiable |
| F-07 | confirmed | Backups before first paid pilot in milestones; TROUBLESHOOTING documents the restore drill + integrity check |
| F-08 | confirmed | v1.2 gate for concurrent renders; §6 sensitivity row; spoken disclosure — the "untested under concurrency" fact is on screen, not buried |
| F-09 | confirmed | Ops floor in milestones; startup fails loudly if ffmpeg missing with video on; current no-alerting state spoken plainly |
| F-10 | confirmed | Attribution-integrity check is a real gate — lead-fee can't be chosen until platform-observed data is the source of truth |
| F-11 | confirmed | Rotation cadence, app-admin custody, pilot/prod app separation in DEPLOYMENT |
| F-12 | confirmed | "Opt-outs are currently unauthenticated" spoken in Transitions |
| F-13 | confirmed | Render pass is explicitly forbidden from tidying up fallback English strings — the discipline that prevents a pretty lie |
| F-14 | confirmed | Conversion beat is on screen end-to-end with real engine output in the evidence logs — the pitch now walks the money moment |
| F-15 | confirmed | §2 is 5 beats, EN+MR merged, one held Marathi proof frame — the walkthrough has room to breathe |
| F-16 | confirmed | v1.2a/v1.2b split: the conditional escrow rail is no longer smuggled into a milestone that must be staffed and budgeted |
| F-17 | confirmed | "Consultation request + lead handoff" — nobody will over-read this as scheduling |
| F-18 | confirmed | "Still open" now names the board review itself — no more stale open items |
| F-19 | confirmed | Executed mr quote: "एकूण — ₹189.00" — natural Marathi, the English "Total" is gone from the Marathi receipt |
| F-20 | confirmed | mr tracking: "ऑर्डर डिझायनरला पोहोचली" — prospect-facing (her order reached the designer), not the backwards "received"; all five statuses localized per locale |
| F-21 | confirmed | "उघडी ऑर्डर" is dead; "सध्या तुमची कोणतीही चालू ऑर्डर नाही" reads like spoken Marathi |
| F-22 | confirmed | Payment line on the order-placed screen in all four locales; mr: "💳 पैसे डिझायनरला थेट द्या — अ‍ॅप मध्ये पैसे घेत नाही." — natural, and it's on the conversion beat's landing screen |
| F-23 | confirmed | Opening frames carry "Illustrative preview, not to scale — not AR"; intro stakes the value on the funnel, not the render; renders untouched per D-01 |
| F-24 | confirmed | "परफेक्ट — ग्राहकाला पाठवा" → "छान! ग्राहकाला पाठवा"; catalog strings use chat-register "वस्तू" not textbook "उत्पादन"; `p_photo_ok` also fixed to "छान" |
| F-25 | confirmed | True ranges printed: ₹45–515 / −$4 to +$52; the negative US tail stays on the page and in the plan's §4 on-screen numbers |
| F-26 | confirmed | The asymmetry is stated on screen: take-rate reverses the money boundary; counsel sign-off per market is a precondition, not an implementation detail |
| F-27 | confirmed | Decision rule with real numeric thresholds (₹2,00,000 / $8,000 median project value + counsel → take-rate; else lead-fee ≤ 20% of measured consult fee); CAC estimated via onboarding-labor proxy with a log-and-reprice requirement |
| F-28 | confirmed | True take-rate envelope printed: −₹15,000 to ₹73,000; the negative tail is no longer dropped |
| F-29 | confirmed | Moat section is honest: no tech moat, disintermediation named, under-reporting tolerance quantified (15% under-reporting kills the mid-corner contribution) |
| F-30 | confirmed | ≥3 paid consultations per pilot designer (not one anecdote), WTP probe, fee-input reliability warning, criteria labeled demand validation |
| F-31 | confirmed | "The decision is made per market" — one line, ambiguity gone |
| F-32 | confirmed | Test count line matches my own run today (97 passed, 1 skipped); Ruff clean |

## Residuals for the coordinator

1. **F-06:** the remaining work is small — name the retention-policy owner
   (one line) and land + test the deletion procedure as code. Until then the
   privacy gate is a promise without an assignee or a path.
2. Marathi register overall: clean. The EU flag from v1 (bookkeeping English
   in money screens) is genuinely fixed — verified against real engine output
   logs, not the plan's claims about them.
3. D-01 / D-02 stand as triaged (rejected/deferred with written reasons);
   nothing in this round changes either.
