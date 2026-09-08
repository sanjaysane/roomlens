# External-User Review — v3 milestone package (RoomLens)

**Reviewer seat:** I am not technical. I am a Marathi-speaking homeowner
who would try a design chat on WhatsApp, and I read the package the way a
real customer would: can I follow it, do I understand the money, and
would I trust it with my room photo, my order, or my phone number. I
reviewed the v1 videos in `docs/review-loop/v1/external-user.md`; this is
the v3 round.

**Verdict: NEEDS WORK**

The v3 package is more honest than v1 — the "explicitly not AR" framing
up front, the synthetic-media disclosure, "no platform take in MVP", and
₹ pricing are all the right moves. But honesty about a problem is not a
fix, and the v3 package ships **three of my own v1 findings unfixed**
(English "Total" on the money screen, English tracking statuses, the
word-for-word "open orders" joke — this time a fresh instance in
RoomLens's own Marathi strings), plus a booking flow that still never
tells me how I pay. And the planned v3 video repeats the exact frames I
rejected: the Marathi money screen saying "Total — ₹189.00" is shown in
the plan's own claim map as *the proof the locale work is done*.

---

## Blockers

### B1. The Marathi money screen still says "Total" — v1 M3, now enshrined in the v3 plan
- **Code:** `src/pricing.py:95`:
  `f"Total — {format_money(quote['total_cents'], currency)}"`
- **Video plan:** `docs/videos/v3-presentation-plan.md` §2 frame 7 and
  the §3 claim map proudly show the quote "rendered for mr viewer" as
  `Aria Chair × 1 — ₹189.00 / Total — ₹189.00` (also
  `docs/evidence/engine-output-2026-09-07.log` lines 337–338, 351–352).
- **Why it blocks me:** this is the screen where I decide to spend money.
  "Total" is plain English, and — as my v1 review noted — BiteFlow's
  Marathi chat already uses "एकूण", so the product demonstrably knows
  the word. This is not a fallback problem; the string itself is wrong
  in every locale.
- **Expectation violated:** the plan's own §2(4) claims the Marathi
  frames were reviewed for "natural Marathi, never translated
  word-for-word (per the v2 review's External User lessons)". A plan
  that claims the lessons were applied, while its own evidence file
  shows the English "Total" on the Marathi money screen, fails its own
  standard.
- **Fix:** a localized total label — "एकूण" for Marathi (and check the
  other locales too).

### B2. Order tracking still speaks raw English to a Marathi user — v1 M4, unfixed
- **Code:** `src/handlers/prospect.py:271–281` (handle_tracking):
  `f"#{o['id']}: {o['status'].replace('_', ' ')} — {format_money(...)}"`
  renders inside `p_tracking` ("📦 तुमच्या ऑर्डरी:") for **every**
  locale, so a Marathi prospect sees `#5: received — ₹189.00`;
  `src/handlers/designer.py:415–421` sends `p_tracking_update` with the
  raw `status.replace("_", " ")` to the prospect as well.
- **Why it blocks me:** two problems, exactly as in v1. First, it's
  English in a Marathi chat. Second, "received" is backwards for me: *I*
  haven't received anything — the *designer* received *my* order. I read
  it and think "received what? by whom?" I expect "ऑर्डर मिळाली" or a
  status that speaks to me ("तयार होत आहे").
- **Expectation violated:** the same v1 M4, unchanged. The currency got
  localized (₹) while the status — the word that tells me what is
  happening to my order — stayed English. Localizing the price but not
  the status is localizing the wrong half.

### B3. "उघडी ऑर्डर" — the word-for-word joke, back in a new disguise
- **Locale:** `locales/mr.json`, key `p_no_open_orders`:
  "सध्या तुमची **कोणतीही उघडी ऑर्डर नाही**. नवीन प्रीव्यूसाठी खोलीचा
  फोटो पाठवा! 📸"
- **What it says vs what it means:** "उघडी" means uncovered / exposed.
  This is "open orders" translated word-for-word — the exact class of
  failure the v1 board caught in BiteFlow's "उघड्या ऑर्डरी पहा" (v1 M1).
  It reads as a joke: your uncovered orders. A real person writes
  "चालू ऑर्डरी" or "सुरू असलेल्या ऑर्डरी".
- **Expectation violated:** the review-loop framework exists precisely
  so a caught failure class stays caught. A reviewer reading this string
  trusts every other Marathi string a little less — if "open" became
  "उघडी", what else got translated by dictionary instead of by person?
- **Fix:** "सध्या तुमची कोणतीही चालू ऑर्डर नाही."

---

## Major

### M1. The booking flow still never tells me how I pay — v1 M6, unfixed
- **Locale/flow:** `locales/mr.json` `p_order_confirm`
  ("🧾 तुमची ऑर्डर: … 1️⃣ ऑर्डर पक्की करा 👍") → `p_order_placed`
  ("🎉 ऑर्डर #{order_id} झाली! डिझायनर लवकरच डिलिव्हरीची माहिती देईल.").
  No locale contains a payment line anywhere in the confirm/placed
  sequence.
- **Why it freezes me:** I press "ऑर्डर पक्की करा" on a ₹189 order and
  get congratulations — but nobody asked me for money, nobody told me
  when money leaves my hands, and nobody told me how. *Am I about to be
  charged?* The video plan's business section (§4 "Must say") explains
  "the designer is paid directly, off-platform" to the **board**; the
  prospect in the chat is never told. My v1 contrast stands: BiteFlow's
  "जेवण आल्यावर … रोख द्या" (pay cash when the food arrives) removes all
  fear; RoomLens still has no equivalent line.
- **Expectation violated:** the (d) trust moment — "money moves directly
  between people" must be explainable *to me in the chat*, not just to
  the board in narration. One line on `p_order_placed` — e.g. "पैसे
  डिझायनरला थेट द्या — अ‍ॅप मध्ये पैसे घेत नाही" (pay the designer
  directly; the app takes no money) — would unblock it.
- **Note:** the plan's §4 non-goals (§4.6, "no payment or escrow
  functionality") are honest about what isn't built; honesty about the
  missing rail does not excuse never telling the user who they pay.

### M2. The preview image still has English burned into it, and still looks like a sticker — v1 M2/M5
- **Evidence:** `docs/evidence/viz-asha-aria-chair.jpg` and
  `docs/evidence/viz-marathi-user-aria-chair.jpg` — I looked at both.
  Both show a flat brown rounded rectangle with "Aria Chair" printed on
  it in English, under an English header: "Your room, with our furniture:
  Aria Chair — $189.00". The Marathi caption below the photo is Marathi
  ("✨ पाहा, तुमच्याच खोलीत Aria Chair!"), but the thing I am supposed to
  look at hardest is the thing I cannot read — exactly my v1 M2 — and
  the chair itself still looks pasted-on, exactly my v1 M5.
- **Expectation violated:** the plan's §2(2) intro frame shows these two
  renders as the product's first visual proof, with only a
  "sample photos" disclosure caption. Disclosure tells me the photos
  aren't mine; it does not make the composite believable, and it does
  not make the English inside the picture readable. The milestones'
  honest framing ("illustrative preview, not to scale, not AR") protects
  the designer's reputation; it does not sell the prospect.
- **Why it stays major, not a blocker:** the milestone gap #1 already
  owns this ("compositing quality on real customer room photos is
  unproven — the #1 expectation risk") and the pilot's first job is the
  20-photo quality bar. But the v3 video plans to open with these exact
  frames as the value proposition — a board member shown this as "see
  furniture in YOUR room" will not feel the promise, and neither would
  I.

### M3. The walkthrough plan skips the order-confirm → placed → tracking beat
- **Doc:** `docs/videos/v3-presentation-plan.md` §2, frames 1–8.
- **Detail:** the plan walks designer onboarding → catalog add → prospect
  photo → placement → localized preview delivery (frames 1–6), then jumps
  to DB records (frame 7) and the photo quality gate (frame 8). The order
  confirmation, order placement, and order tracking — the v2 script's
  most rushed beat ("ordering, quote line items, confirmation, and
  cancellation in 40 seconds") — are not frames in v3 at all.
- **Expectation violated:** the video bar — "complete unhurried
  walkthrough … each shown to completion." Skipping the order loop in a
  video whose business section is about lead-fee vs take-rate means the
  video never shows the moment that produces the lead.

---

## Minor

- **"3️⃣ परफेक्ट — ग्राहकाला पाठवा"** (v1 minor, unfixed):
  `locales/mr.json` `d_studio_adjust`. "परफेक्ट" is English wearing
  Devanagari clothes; a real person writes "छान! ग्राहकाला पाठवा" or
  "मस्त — ग्राहकाला पाठवा". (Same word in `p_photo_ok` — "✅ परफेक्ट,
  धन्यवाद!" — is colloquially fine in speech, but the button deserves
  the real word.)
- **"उत्पादन" still feels like a textbook** (v1 minor, unfixed):
  `d_studio_pick_product` "ठेवण्यासाठी उत्पादन निवडा",
  `d_cat_name_ask` "उत्पादनाचं नाव काय?", `d_catalog` "तुमचा कॅटलॉग".
  In chat a person says "वस्तू निवडा".
- **Narration register** (v1 M7): the plan's "Must say" lines are
  board-register ("the tap writes an order row and notifies the
  designer" — §4) with no register guidance for user-facing reuse; noted,
  not blocking, since the stated audience is the board.
- **`d_new_order` Marathi** ("स्थिती बदलण्यासाठी ऑर्डर्स उघडा") uses
  "उघडा" correctly as the verb "open it" — this one is fine; the joke
  is only the adjective "उघडी/उघड्या".

---

## Trust answers (per the rubric)

**(a) Would I trust this with my money / room photo after watching the
planned video?** **Not yet.** I would trust the *people* — the
"explicitly not AR" honesty, the "illustrative preview, not to scale"
framing, the "platform takes nothing in MVP" disclosure all build
credibility. But I would not share my room photo or confirm a ₹189
order, for the same two reasons as v1: the preview picture still looks
pasted-on with English printed in it (M2), and the booking flow still
never tells me how or when I pay (M1). Credibility of the team is not
yet trust in the transaction.

**(b) Language and locale naturalness in the planned narration beats:**
The Marathi prospect chat the video will hold on screen is warm and
natural — "📸 छान! तुमच्या खोलीचा एक स्पष्ट फोटो पाठवा (लाइट लावा, फोन
हलवू नका)" is lovely — *except* where the failures above sit: "Total" on
the money screen (B1), English statuses in tracking (B2), "उघडी ऑर्डर"
(B3). The plan's §2(4) claim that the External User lessons were applied
is contradicted by its own evidence frames.

**(c) Moments where a real user would get confused, scared, or stuck:**
Pressing "ऑर्डर पक्की करा" with no payment story (M1) — the freeze
moment. Tracking an order whose status says "received" in English (B2) —
confusion about whose order was received by whom. Seeing "उघडी ऑर्डर"
(B3) — the laugh that costs trust.

**(d) Is "money moves directly between people" explainable to a
non-technical user?** The plan explains it to the *board* beautifully
(§4 money-flow diagram, "no platform take in MVP", lead-fee vs take-rate
from measured data). But a non-technical **prospect** is never told it:
the in-chat story has no payment line, so the user cannot repeat back
"who do I pay and when?" The money story is explainable; it just is not
explained to the person paying.
