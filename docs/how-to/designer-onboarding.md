# Designer onboarding

Goal: go from zero to a sent visualization in one sitting. Everything happens
in WhatsApp — no dashboard, no login.

## Scene 1 — Connect your WhatsApp number

Message the RoomLens number. You'll get a welcome with two options:

```
1. I'm a designer
2. Preview furniture in my room
```

Reply `1`. Then type your **studio name** (this is the one place typing is
required — it's shown to your prospects). You're now in the designer home hub:

```
1. Catalog   2. Studio   3. Orders   4. Marketing
```

## Scene 2 — Add your first catalog item

Reply `1` (Catalog) → `1` (Add). The bot walks you through four steps:

1. **Name** — type it, e.g. `Oak Accent Chair`.
2. **Price** — type the price in your currency's main unit, e.g. `189`.
3. **Size class** — `1` floor, `2` wall, `3` tabletop.
4. **Cutout photo** — send a product photo with a transparent background
   (RGBA PNG). No background remover is built in — remove the background first
   with any tool, or the cutout pastes with its background. Reply `0` to skip.

Repeat for each product you want to sell. `0` from the catalog list goes back
to the hub.

## Scene 3 — Invite a prospect

Give prospects the RoomLens WhatsApp number (a QR code on your card or a link
works). When they message it and reply `2`, they pick your studio from the
numbered list — that's the invitation; there's no separate invite step.

## Scene 4 — Place a product into their room

When a prospect sends a room photo, you get a notification. Reply `2` (Studio)
to see pending rooms, pick the room, then:

1. **Pick the product** by number.
2. **Pick the placement preset** — `floor-center`, `left-wall`, `right-wall`,
   or `wall-hang`.
3. **Adjust** — bigger, smaller, restart, or send.

What the prospect receives is a 2D composite with a price strip — preset
positioning, not AR. Set that expectation in your own words before sending
("here's a rough preview of how it could look").

## Scene 5 — Handle the order

When the prospect confirms, you get an order notification with the total.
Reply `3` (Orders) to see the queue, pick the order, and update its status:
`1` preparing, `2` shipped, `3` delivered. The prospect can check status by
messaging the number anytime.

## Next steps

- [Marketing](..): campaigns go only to opted-in prospects via Meta-approved
  templates — create your templates in the WhatsApp Manager first.
- A prospect who replies `STOP` is suppressed from all future outreach
  automatically.
