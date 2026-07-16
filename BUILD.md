# BUILD.md — DREAMS System (HUM)

Build log for the DREAMS (slow-cognition / subconscious) agent subsystem.
Companion to `DREAMS_PROTOCOL.md` (normative spec) and `README.md` (normative-vs-executable).

## Timeline

### v0.1.0 (2026-07-16) — conceptual scaffold
- 7-file cycle + `DREAMS_PROTOCOL.md` (hardened spec) committed to
  `nobulart/hum` before real use could shape it.
- `dreams-capture` skill shipped (stable format, no v1 assumptions).
- `scripts/surface.py` v1 baseline: parsed front matter, scored with a W function,
  wrote survivors to `SURFACE.md`, reset `DREAMS.md`.
- Storage decision: YAML front matter in Markdown (no JSON/SQLite). Dropped `DREAMS_STATE.json`.

### External review (GPT5.6-Sol-High) — classification: excellent v0.1-alpha,
*suitable for manual experimentation but NOT safe for unattended cron*.

The reviewer's core findings (all correct):
1. **Every dream survives.** v1 scoring used positive *defaults* for novelty/utility/
   active/consequence/predictive, so an ordinary one-line fragment scored ~0.74, above the
   0.5 threshold. The function could not distinguish fragments. *Fix: unknown signals = 0.*
2. **Data loss.** Append-then-reset could duplicate on rerun; non-survivors were erased;
   malformed YAML silently became `{}` and got default scores. *Fix: 4-outcome classification
   + atomic writes + quarantine.*
3. **Alpha fragments shipped as default runtime.** Persona-specific seed (interpreting
   corrections as valence) should not be every install's starting subconscious.
   *Fix: `templates/` clean + `examples/alpha-session/` for the seed.*
4. **Capture id collisions** possible across concurrent agents (sequential counter).
   *Fix: collision-proof `dream-YYYYMMDDThhmmss-XXXX` ids.*
5. **Drift** between protocol claims (dedup, recurrence, counterdreams) and executable.
   *Fix: README "normative target vs executable path" table; renamed narrative.*

Recommended sequence adopted: strict validation + quarantine, capture executable with
locking, atomic/idempotent surfacing, evidence-derived scoring, daily budget, move alpha to
examples, recurrence (exact hash), tests before cron, manual promotion.

### v0.2.0 (2026-07-16) — transactional integrity + meaningful selectivity
- **Paused the surfacing cron** (`cca7a54f6744`) immediately on review — protected the seed
  data from an unsafe automated reset. Re-enable only after tests green + this build landed.
- `src/hum/` package: `schema`, `store` (lock + atomic + run_id), `parser` (tolerant of
  malformed/embedded `---`), `scoring` (evidence-derived, zero defaults), `recurrence`
  (exact content-hash dedup + prior-file scan), `lifecycle` (4 outcomes + budget),
  `reports` (morning summary).
- `scripts/capture.py` — owns id gen, tz, validation, source normalisation, atomic append,
  duplicate detection. `dreams-capture` skill delegates to it.
- `scripts/surface.py` — classify → budget (default 5) → atomic multi-file write. High-
  consequence (WARNING/CONTRADICTION) always surfaces regardless of budget.
- **Evidence-derived scoring verified**: a plain one-line fragment with `recurrence_count:1`
  now scores < 0.4 (was 0.74). Recurrence/evidence/active raise it; untrusted provenance
  penalised.
- Four outcomes: `surfaced` → SURFACE, `deferred` → stays in DREAMS (not erased),
  `forgotten` → tombstone, `invalid` → QUARANTINE (never `{}`, never scored).
- Repo restructure: `templates/` (clean runtime), `examples/alpha-session/DREAMS.seed.md`
  (18 originating fragments preserved, not shipped as default), `config.yaml` carries
  `surfacing.budget: 5`.
- **Tests: 22/22 green** (pytest) covering malformed YAML, bad id/type, duplicate-id
  collision-free capture, tz ids, embedded `---`, empty file, budget selectivity,
  high-consequence always surfaces, quarantine-not-scored, deferred preserved, idempotent
  re-run.

## Deferred to v0.3+ (research, not yet built)
- Semantic (near-duplicate) recurrence.
- Counterdream auto-generation (currently marked `PENDING` in output).
- Cross-dream / resistance-flag machinery.
- Lucidity debt tracking, lineage graph, dream ecology / diversity pressure, control fragments.
- Scientific evaluation harness (the experiment's measurement layer).
- Promotion automation (`dreams-promote` skill) — stays manual for first several weeks.

## Verification commands
```bash
cd <repo>
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/ -q -p no:cacheprovider
python scripts/surface.py --dreams-dir . --dry-run
python scripts/capture.py --type SEED --body "test" --dry-run
```

## Deployment state
- Local install: `~/workspace/projects/hum/` (synced with this repo).
- Cron `cca7a54f6744` (07:00 surfacing) PAUSED pending this build + sign-off.
- Re-enable only after: tests green on the real install, and a manual live cycle confirms
  non-survivor preservation on the actual `DREAMS.md`.
