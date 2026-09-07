# FAQ

## 1. Is RoomLens AR?

No. RoomLens does **2D preset-based compositing**: a product cutout is pasted
onto your room photo at one of four fixed presets (`floor-center`, `left-wall`,
`right-wall`, `wall-hang`) with a bigger/smaller scale control. There is no
plane detection, no depth estimation, no perspective reconstruction, and no
guaranteed real-world scale. We say this up front rather than letting the
preview imply precision it doesn't have.

## 2. Which languages are supported?

English, Spanish, and Hindi — 85 locale keys each, kept in parity by an
automated test. Send `language` / `idioma` / `भाषा` at any point to switch
mid-conversation; you return to where you were.

## 3. My parents aren't tech-savvy. Can they use it?

That's the core design goal. The prospect flow is numbered menus
(`1` pick a designer, send a photo, `1` order / `2` change, `1` confirm 👍).
No app to install, no account, no forms, no required typing — just WhatsApp
and single-digit replies.

## 4. Can I send a video of my room instead of a photo?

Yes — send a short clip. We extract the first frame with ffmpeg and composite
onto it. If the video can't be decoded, you'll get an honest "please send a
still photo" reply, not a broken render.

## 5. My photo was rejected as "too dark." Why?

A dark, blurry, or tiny photo would produce a misleading preview, so the
quality gate asks for a retake instead of rendering onto garbage. This is
deliberate — a bad overlay is worse than a polite re-ask. Tips: turn the room
lights on, hold the phone steady, stand in a doorway to capture the whole wall.

## 6. How do pricing and quotes work?

The designer sets a price per product (stored in cents). When a visualization
is sent, a quote is built from the placed products plus a delivery charge. The
prospect sees line items and a total, then confirms with `1` to place the
order. Amounts are displayed in the viewer's language currency: ₹ for Marathi
and Hindi, $ for English and Spanish.

## 7. How does ordering work for the prospect?

Review the preview: `1` order, `2` ask to change placement, `3` ask to change
product, `4` talk to the designer. Choose `1`, check the quote, reply `1` to
confirm (👍) or `2` to cancel (👎). You can check order status anytime by
messaging the number.

## 8. What does STOP do?

`STOP` from any point instantly opts you out of all business-initiated
messages (campaigns, follow-ups, win-backs). No confirmation dance, no delay.

## 9. Will I get spam from the designer?

Only if you opted in. After your first accepted photo we ask once
("Reply `1` for design tips & offers"). Campaigns go only to opted-in
prospects, only through Meta pre-approved templates, and `STOP` ends them.

## 10. What data is kept, and for how long?

Room photos and renders are stored as files (local `MEDIA_DIR` by default, or
Supabase in prod); the database keeps references plus conversation state,
quotes, and orders. See [docs/how-to/media-retention.md](how-to/media-retention.md)
for what's stored where, retention guidance, and how to request deletion.

## 11. What does self-hosting cost?

The stack is one Python container + one PostgreSQL 16 container. On a small
VPS or a modest cloud VM that's a few dollars a month plus the WhatsApp
conversation charges from Meta (Meta bills per 24-hour conversation window;
check current WhatsApp Business pricing). No per-seat or per-render license.

## 12. Do I need Meta approval?

Yes. You need a WhatsApp Business Account, an approved phone number, and —
for any business-initiated message (campaigns, win-backs) — **approved message
templates** in the Meta WhatsApp Manager. User-initiated conversations (a
prospect messaging you first) work without templates. Template approval is
part of the deployment checklist.

## 13. Does it work offline?

No. Every message round-trips through the webhook, the database, and the
Meta WhatsApp Cloud API. No connectivity → no conversation.

## 14. Can the designer use their own product photos?

Yes. During catalog setup the designer uploads a product cutout (RGBA PNG
with transparency). Background removal is not built in — use any background
remover before uploading, or the cutout will paste with its background.
