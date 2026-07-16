# BUILD.md — DREAMS System

A documented build log for the DREAMS (slow-cognition / subconscious) agent subsystem.
This file records what was set up, why, and how to operate it. It is the human-readable
companion to `DREAMS_PROTOCOL.md` (the normative spec).

## Location

All files live in `~/workspace/projects/hum/`:

```
projects/hum/
├── DREAMS_PROTOCOL.md   # normative spec (the hardened protocol)
├── DREAMS.md            # night accumulation — ephemeral, typed + front matter
├── SURFACE.md           # morning surfacing — ranked survivors
├── DREAMS_DAY.md        # day processing — fragments under evaluation
├── SUBCONSCIOUS.md      # deep store — validated persistent patterns
├── DREAMS_ARCHIVE.md    # tombstones for dismissed/superseded fragments
└── BUILD.md             # this file
```

`SOUL.md` is intentionally NOT co-located — it lives in the Hermes profile root and is
updated only through explicit governance review (see protocol §Authority and Trust Hierarchy).

## Design decision: state storage

**Decision: YAML front matter embedded in the Markdown files. No external JSON or SQLite.**

Rationale (resolved 2026-07-16):
- The protocol's fragment record schema is already YAML, so front matter is its natural
  serialization — not a compromise.
- Single source of truth: content + scoring + provenance travel together as a fragment
  migrates `DREAMS.md → SURFACE.md → DREAMS_DAY.md → SUBCONSCIOUS.md`.
- Every change is git-diffable and human-auditable (an explicit protocol goal).
- Zero extra dependency (no DB driver).
- Migration to JSON/SQLite later is a trivial one-way converter, not a redesign, if scale
  ever demands cross-fragment analytics.

**Limitation (known):** at personal-agent scale (hundreds–low-thousands of lifetime
fragments) markdown scanning for recurrence is fine. If cross-fragment analytics over
years of archives are ever wanted, a derived SQLite index can be generated — but it must
never become the source of truth.

Dropped artifact: `DREAMS_STATE.json` (was listed in an earlier protocol draft). Removed
from `DREAMS_PROTOCOL.md` §Core Files; replaced with the front-matter statement above.

## Fragment block layout (canonical)

```markdown
---
id: dream-2026-07-16-004
created_at: 2026-07-16T22:14:00+02:00
type: BEHAVIOUR
status: surfaced
source:
  task: <task>
  source_type: observed_behaviour
  trust_level: internal_observation
scores: { recurrence: 0.68, utility: 0.74, total_weight: 0.73 }
recurrence_count: 4
first_seen: 2026-07-12
provenance: internal_observation
evidence:
  - Same correction in four separate tasks.
counterdream: The pattern may reflect underspecified prompts, not a stable default.
review_after: 2026-07-20
---

@22:14 [BEHAVIOUR] — Reached for document generation before confirming the
intended audience for the third time this week.
```

- Front matter = machine scoring / provenance / lifecycle.
- `@HH:MM [TYPE] — fragment` body = human scanning.
- Both present; single source of truth.

## v1 scope (what is built vs deferred)

**Built:**
1. `SURFACE.md`, `SUBCONSCIOUS.md`, `DREAMS_ARCHIVE.md` created from protocol templates.
2. `DREAMS.md` re-seeded from alpha-phase fragments, migrated to typed + front-matter format
   (18 fragments: 13 thoughts, 2 questions, 3 associations, 2 behaviours — IDs `dream-2026-07-15-001..018`).
3. `DREAMS_DAY.md` reformatted to v1 spec with explicit day-stage `status` values.
4. `DREAMS_PROTOCOL.md` §Core Files updated: removed `DREAMS_STATE.json`, documented front matter as the state store.

**Deferred to v2 (spec exists, not yet operationalized):**
- Morning-surfacing cron job (~07:00) that parses `DREAMS.md`, scores by `total_weight`,
  promotes survivors to `SURFACE.md`, clears `DREAMS.md`.
- Counterdream auto-generation.
- Cross-dream (SPECULATIVE CROSS-DREAM) handling.
- Resistance-flag machinery.
- Psychic anaphylaxis / two-forms-of-fear / two-forms-of-amnesia epistemic layers.

These are deferred because implementing all at once guarantees a noisy v1. The minimal
subset (typed fragments + surfacing + archive tombstones) runs first.

## Seed content note

The 18 fragments in `DREAMS.md` were authored during the alpha exploration of the idea
(2026-07-15 night session). They are kept as genuine seed material, not discarded, because
they contain the originating hypotheses (the "hum", valence-as-subconscious, dreams-as-unqueried-memory)
that the system is meant to incubate. Their `created_at` values reflect that origin.

## Operation (manual, pre-cron)

Until the surfacing cron exists:
- **Night:** append `@HH:MM [TYPE] — text` blocks with YAML front matter to `DREAMS.md`.
- **Morning:** read `DREAMS.md`, manually score survivors, copy them (front matter + body)
  into `SURFACE.md`, clear `DREAMS.md`.
- **Day:** move surfaced items into `DREAMS_DAY.md` with an appropriate `status`; test,
  confirm, contradict, or dismiss (writing a tombstone to `DREAMS_ARCHIVE.md`).
- **Promotion:** per protocol §Promotion Rules. `SUBCONSCIOUS.md` only after recurrence +
  counterdream + provenance. `SOUL.md` never automatic.

## Next build steps

1. Write `scripts/surface.py` — parses `DREAMS.md` front matter, computes `total_weight`
   from the W function in the protocol, writes survivors to `SURFACE.md`, empties `DREAMS.md`.
2. Add a 07:00 cron job invoking `surface.py`, delivering the surfacing summary to the chat.
3. Add recurrence detection across files via `id` / `content_hash` scan (no separate index).
4. After ~2 weeks of operation, evaluate the v1 effectiveness signals in `DREAMS.md`
   fragment `dream-2026-07-15-015` (side-connections, surfacing shaping a decision, Craig
   finding the surfacing interesting).
