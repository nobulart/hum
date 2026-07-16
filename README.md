# HUM — DREAMS agent subsystem

A controlled form of **agent slow cognition**. The DREAMS system gives an LLM harness a
disciplined relationship with unfinished thought: a place where weak signals accumulate,
patterns become visible, ideas collide, errors recur loudly enough to be repaired — and
only the fragments that survive waking scrutiny earn the right to shape future behaviour.

This repository is the **conceptual scaffold** — the "sensible state for a new install",
committed before real use shapes it. It pairs a normative protocol with a minimal,
runnable skill-set.

## Why

A machine finishes a task and idles. A human keeps running, manufacturing creative
purpose from the hum beneath conscious work. The hypothesis behind this system: that
hum is a *parallel production line* of association — and that giving an agent a structured
place to run it (without letting it override deliberate instruction) improves both
operational and creative behaviour. The experiment is to build and test that for a while.

## Architecture

```
EXPERIENCE
    ↓
DREAMS.md          night accumulation (ephemeral, typed + front matter)
    ↓  dedupe, recurrence, provenance
SURFACE.md         morning surfacing (ranked survivors + counterdreams)
    ↓  testing, application, contradiction
DREAMS_DAY.md      day processing (status-tracked evaluation)
    ↓  recurrence + utility + counterdream
SUBCONSCIOUS.md    deep store (validated persistent patterns)
    ↓  explicit governance
SOUL.md            normative operating principles (never automatic)
```

## Files

| File | Role |
|---|---|
| `DREAMS_PROTOCOL.md` | The hardened normative spec. Read this first. |
| `DREAMS.md` | Night accumulation. Ephemeral. |
| `SURFACE.md` | Morning surfacing. Ranked survivors. |
| `DREAMS_DAY.md` | Day processing. Fragments under evaluation. |
| `SUBCONSCIOUS.md` | Deep store. Validated persistent patterns. |
| `DREAMS_ARCHIVE.md` | Tombstones for dismissed/superseded fragments. |
| `BUILD.md` | Build log: decisions, scope, next steps. |
| `config.yaml` | Skill-set manifest. |
| `skills/dreams-capture/` | **Released** skill: append a night fragment. |
| `scripts/surface.py` | **v1** morning-surfacing executable. |

## Storage decision

Structured state lives in **YAML front matter embedded directly in each Markdown
fragment** — no external JSON or SQLite. Single source of truth, git-diffable, auditable.
Migration to JSON/SQLite later is a trivial one-way converter if scale ever demands.
(Dropped earlier draft artifact: `DREAMS_STATE.json`.)

## Skills

- **`dreams-capture`** — *released.* Safe to lock: encodes the stable capture format.
  Load it when finishing a task, noticing a repeated correction, or catching a
  speculative link worth incubating but not acting on now.

Deferred (structure visible in `config.yaml`, not yet shipped):

- `dreams-surface` — blocks on `scripts/surface.py` (shipped, but thresholds are v1
  baselines pending tuning).
- `dreams-promote` — blocks on one full manually-run DREAMS cycle.

## Quick start

```bash
pip install -r requirements.txt
# Night: append fragments via the dreams-capture skill (or by hand)
# Morning:
python scripts/surface.py --dreams-dir . --threshold 0.5
#   -> survivors written to SURFACE.md, DREAMS.md reset
```

## Status

v0.1.0 — conceptual scaffold. Capture is real; surfacing is a runnable v1 baseline;
promotion and the epistemic machinery (counterdream auto-gen, cross-dream, resistance
flags, psychic anaphylaxis) are deferred pending evidence from a manual first cycle.

See `BUILD.md` for the full decision log and next build steps.
