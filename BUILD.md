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

### v0.3 — Scientific evaluation harness (NEXT BUILD)
The system is an experiment ("build and test that for a while") but has **no
measurement layer** — there is no way to tell whether a surfaced or promoted
fragment ever improved behaviour. This is the gap that blocks the core hypothesis.
It is *infrastructure, not psychological machinery*, so it respects the v0.1→v0.2
reviewer's "no more machinery yet" constraint and produces the ground truth that
later makes promotion automation safe.

Scope:
- Extend `src/hum/schema.py` with outcome/feedback fields on `DREAMS_DAY.md`
  fragments (applied?, outcome, utility_delta, evidence_refs).
- `scripts/evaluate.py` (or `src/hum/metrics.py`): reads `DREAMS_DAY.md` +
  `SUBCONSCIOUS.md`, computes promotion precision/recall vs later recorded outcomes,
  emits a weekly report.
- Append evaluation summary to the morning report (per-week: N promoted, M
  confirmed, K contradicted).
- Tests: synthetic outcome dataset → expected precision/recall.
- Acceptance: harness runs on the live `~/.hermes/hum` data without crashing;
  report produced; no new volatiles introduced into the repo.

### Deferred beyond v0.3
- Semantic (near-duplicate) recurrence.
- Counterdream auto-generation (currently marked `PENDING` in output).
- Cross-dream / resistance-flag machinery.
- Lucidity debt tracking, lineage graph, dream ecology / diversity pressure, control fragments.
- Promotion automation (`dreams-promote` skill) — stays manual for the first
  several weeks until the evaluation harness has produced outcome data.

## Verification commands
```bash
cd <repo>
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/ -q -p no:cacheprovider
python scripts/surface.py --dreams-dir . --dry-run
python scripts/capture.py --type SEED --body "test" --dry-run
```

## Deployment state (updated 2026-07-18)
- **Runtime home is `~/.hermes/hum`, NOT the git repo.** The git repo
  (`~/workspace/projects/hum`) holds only non-volatile scaffold (code, templates,
  protocol, docs). Per-install runtime volatiles (DREAMS.md, SURFACE.md,
  DREAMS_DAY.md, SUBCONSCIOUS.md, DREAMS_ARCHIVE.md, DREAMS_QUARANTINE.md) live in
  `~/.hermes/hum` on each machine. This was enforced after commit `76a5e17`
  accidentally re-committed volatiles; `.gitignore` now excludes them and both
  `HUM_DIR` (dashboard + surface cron) point at `~/.hermes/hum`.
- `bootstrap.sh` was fixed: it now `rsync`s the repo into `HUM_DIR`, refuses to use
  the repo itself as `HUM_DIR`, and preserves existing volatiles. It defaults
  `HUM_DIR` to `~/.hermes/hum`.
- Cron `cca7a54f6744` (07:00 surfacing) is **ACTIVE** on both MacBook (Plato) and
  Mac Studio (Hermes), both pointed at `~/.hermes/hum`. Re-enable gate from v0.2.0
  (tests green + manual live cycle) is satisfied: 22/22 pytest green on the real
  install, and a live surfacing pass confirmed non-survivor preservation.
- MacBook dashboard (`app.py` default) and Studio dashboard (launchd plist
  `EnvironmentVariables`) both set `HUM_DIR=/Users/craig/.hermes/hum`.
