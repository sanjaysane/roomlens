# Review loop — walkthrough videos v1 → v2 (2026-09-06)

Evidence of the 7-persona review swarm for the narrated end-to-end walkthrough
videos, committed here so the GitHub history itself shows which persona gave
what input and what improvement resulted.

## Videos covered by this repo

- RoomLens — Prospect Journey (Marathi): `roomlens-prospect-mr-v2.mp4` (3m32s)
- RoomLens — Designer Journey (English): `roomlens-designer-en-v2.mp4` (3m22s)

(The BiteFlow videos — customer-en, cook-mr — are documented in the
sanjaysane/biteflow repo under the same `docs/review-loop/` path. The persona
review files cover all four videos; this README maps which findings apply to
RoomLens.)

## Fix IDs applied to this repo's videos (from TRIAGE.md)

- roomlens-prospect-mr: A1, A2, A4, A5, A6, A15, A16, A17, A19, A20, A23
- roomlens-designer-en: A2, A4, A6, A11, A12

## Files

- `FRAMEWORK.md` — the reusable 7-persona review loop
  (build → review → triage → rebuild → re-review → release)
- `v1/` — the 7 persona review reports; all 7 returned NEEDS WORK
- `TRIAGE.md` — accept/reject per finding, with reasons
  (23 accepted A1–A23, 8 rejected/deferred R1–R8)
- `CHANGELOG-v1-v2.md` — every v2 change mapped to the finding that caused it
- `v2/` — re-review sign-offs (senior-engineer, board-director)
- `RELEASE.md` — release notes and known issues carried forward

No code was changed by this loop. The v2 fixes are narration re-records,
caption re-renders, on-video disclosures, and corrected manifest descriptions —
the review swarm's rule was: fix in v2 what the video can fix; disclose what
the code can't; never fake engine output and never invent numbers.
