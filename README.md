# HUM — DREAMS agent subsystem

A controlled form of **agent slow cognition**. The DREAMS system gives an LLM harness a
disciplined relationship with unfinished thought: a place where weak signals accumulate,
patterns become visible, ideas collide, errors recur loudly enough to be repaired — and
only the fragments that survive waking scrutiny earn the right to shape future behaviour.

This repository is the conceptual scaffold **and** a runnable v0.2 implementation.

## Why

A machine finishes a task and idles. A human keeps running, manufacturing creative
purpose from the hum beneath conscious work. The hypothesis behind this system: that hum
is a *parallel production line* of association — and that giving an agent a structured
place to run it (without letting it override deliberate instruction) improves both
operational and creative behaviour. The experiment is to build and test that for a while.

## Normative target vs currently executable path

The `DREAMS_PROTOCOL.md` describes the **full normative target** (counterdreams, cross-dreams,
resistance flags, psychic anaphylaxis, lineage, dream ecology, scientific evaluation). Not
all of it is executable yet. This table is the honest drift between spec and code:

| Capability (protocol)        | Status in v0.2 code                          |
|---|---|
| Night capture (typed + FM)   | ✅ `scripts/capture.py` + `dreams-capture` skill |
| Morning surfacing            | ✅ `scripts/surface.py` (budget + ranking)   |
| Eligibility gates / schema   | ✅ `src/hum/schema.py`                        |
| Evidence-derived scoring     | ✅ `src/hum/scoring.py` (unknown = 0)         |
| Recurrence (exact hash)      | ✅ `src/hum/recurrence.py`                    |
| Quarantine of invalid        | ✅ `DREAMS_QUARANTINE.md`                     |
| Atomic / idempotent writes   | ✅ `src/hum/store.py`                         |
| Day processing / promotion   | ⚠️ manual (protocol defines rules; no automation) |
| Counterdream auto-gen        | ❌ deferred (marked `PENDING` in output)     |
| Semantic recurrence          | ❌ deferred (exact hash only)                |
| Cross-dream / resistance      | ❌ deferred                                   |
| Scientific evaluation harness| ❌ deferred                                   |

**Unattended cron is NOT yet recommended** until promotion is automated and the evaluation
harness exists. Run manually or with the cron paused (see Quick start).

## Architecture

```
EXPERIENCE
    ↓
DREAMS.md          night accumulation (capture.py, typed + front matter)
    ↓  dedup, recurrence scan, evidence scoring, budget
SURFACE.md         morning surfacing (ranked survivors + mandatory high-consequence)
    ↓  testing, application, contradiction
DREAMS_DAY.md      day processing (status-tracked evaluation)
    ↓  recurrence + utility + counterdream
SUBCONSCIOUS.md    deep store (validated persistent patterns)
    ↓  explicit governance
SOUL.md            normative operating principles (never automatic)
```

Invalid fragments never enter the flow silently — they go to `DREAMS_QUARANTINE.md`.

## Files

| File | Role |
|---|---|
| `DREAMS_PROTOCOL.md` | The hardened normative spec. Read this first. |
| `DREAMS.md` | Night accumulation (generated from `templates/DREAMS.md`). Lives in `~/.hermes/hum`. |
| `SURFACE.md` | Morning surfacing. Ranked survivors. Lives in `~/.hermes/hum`. |
| `DREAMS_DAY.md` | Day processing. Fragments under evaluation. Lives in `~/.hermes/hum`. |
| `SUBCONSCIOUS.md` | Deep store. Validated persistent patterns. Lives in `~/.hermes/hum`. |
| `DREAMS_ARCHIVE.md` | Tombstones for dismissed/superseded fragments. Lives in `~/.hermes/hum`. |
| `DREAMS_QUARANTINE.md` | Invalid fragments — never scored or erased. Lives in `~/.hermes/hum`. |
| `BUILD.md` | Build log: decisions, scope, next steps. |
| `config.yaml` | Skill-set manifest + surfacing config (`budget: 5`). |
| `src/hum/` | Implementation package (schema, store, parser, scoring, recurrence, lifecycle, reports). |
| `scripts/capture.py` | Night capture executable. |
| `scripts/surface.py` | Morning surfacing executable. |
| `templates/` | Clean runtime file templates (no persona-specific content). |
| `examples/alpha-session/` | Historically important originating fragments (NOT default runtime). |
| `tests/` | pytest suite — transactional integrity + selectivity. |

## Storage decision

Structured state lives in **YAML front matter embedded directly in each Markdown
fragment** — no external JSON or SQLite. Single source of truth, git-diffable, auditable.
Migration to JSON/SQLite later is a trivial one-way converter if scale ever demands.

## Skills

- **`dreams-capture`** — *released.* Delegates to `scripts/capture.py` (id generation,
  validation, atomic append, duplicate detection). Load it when finishing a task, noticing
  a repeated correction, or catching a speculative link worth incubating but not acting on now.

Deferred (structure visible in `config.yaml`, not yet shipped as skills):
- `dreams-surface` — the executable exists (`scripts/surface.py`); promote to a skill after v1 stability.
- `dreams-promote` — promotion stays manual for the first several weeks.

## Quick start

```bash
# Runtime home is ~/.hermes/hum (NOT this repo — see Deployment state in BUILD.md).
# Bring it up from the repo scaffold:
bash hermes/bootstrap.sh            # builds ~/.hermes/hum, links skill, prints cron cmds

# Create an isolated venv (PEP 668: base Python is externally managed):
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt pytest

# Night — capture a fragment (collision-proof id, validated, atomic):
.venv/bin/python scripts/capture.py --type SEED --body "a connection worth incubating" --task mytask

# Morning — surface (budget + ranking; writes SURFACE.md, resets DREAMS.md):
.venv/bin/python scripts/surface.py --dreams-dir ~/.hermes/hum

# Or just see the classification without writing:
.venv/bin/python scripts/surface.py --dreams-dir ~/.hermes/hum --dry-run

# Run the test suite (validates integrity + selectivity):
.venv/bin/python -m pytest tests/ -q -p no:cacheprovider
```

> **Note:** the base interpreter is externally managed (PEP 668), so `pip install`
> into it fails. Always use a venv (`.venv/bin/pip`, `.venv/bin/python`) as shown.
> `requirements.txt` lists `pyyaml`; `pytest` is needed only for the suite.

## Status

**v0.2.0** — transactional integrity + meaningful selectivity. Capture and surfacing are
real and tested. The next milestone (per external review) is **transactional integrity and
meaningful selectivity, not more psychological machinery** — which this release delivers.
Promotion and the epistemic machinery remain manual/deferred.

See `BUILD.md` for the full decision log and the v0.3+ roadmap.
