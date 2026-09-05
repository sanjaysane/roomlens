# Security Policy

## Supported versions

| Version | Supported |
|---|---|
| 0.1.x (current) | ✅ |
| < 0.1 | ❌ |

## Reporting a vulnerability

**Do not open a public issue.** Email the maintainer privately (see
`git log` for current contact, or use the GitHub "Report a vulnerability"
button if private vulnerability reporting is enabled). Include:

- what you found and where (file / endpoint),
- steps to reproduce (no real phone numbers or tokens),
- your assessment of impact.

We will acknowledge within 72 hours, keep you updated on the fix, and credit
you (if you want) when the fix ships.

## Known gap — webhook signature validation

`POST /webhook` currently does **not** validate Meta's
`X-Hub-Signature-256` HMAC signature. The verify-token handshake on
`GET /webhook` is implemented, but a POST forgery from anyone who discovers
the callback URL would be processed as a real message — potentially
triggering renders and outbound WhatsApp sends. Signature validation is on
the production checklist in `docs/DEPLOYMENT.md` and should land before any
public deployment. If you are deploying before it lands, restrict the
endpoint to Meta's published IP ranges as a stopgap.

## Scope notes

- The app never logs message bodies, tokens, or phone numbers beyond what is
  needed for routing (see `main.py` error logging: it logs the phone and the
  exception repr only).
- **No secrets in issues or PRs.** `.env.example` is a template; never commit
  a real `.env`. Tokens rotate via environment, never via code.
- Media (room photos, renders) is user data: treat production media stores
  as sensitive; see `docs/how-to/media-retention.md`.
- The quality gate (`assess_quality`) runs on-device/in-process heuristics
  only; no room image is sent to any third-party vision service.
