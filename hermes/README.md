# hermes/ — Hermes harness configuration for the HUM subsystem

This directory documents the **Hermes Agent**-specific configuration that the
HUM/DREAMS project depends on, so a fresh install under a Hermes harness can be
brought up with the correct abilities (tools, skills, cron jobs, operating
protocols) without reverse-engineering the live setup.

> **Location assumption:** placed under the HUM project root
> (`~/workspace/projects/hum/hermes/`). If you meant a top-level
> `~/workspace/hermes/`, say so and the contents can be relocated.

> **Git status:** `~/workspace/projects/hum` is **not** a git repository at time
> of writing. These files are not yet version-controlled. Do not commit secrets
> (see redaction notes in the docs below).

## What's in here

| File | Purpose |
|------|---------|
| `config.reference.md` | Annotated copy of the relevant sections of `~/.hermes/config.yaml` (secrets redacted), with the parts HUM relies on called out. |
| `skills.md` | Inventory of the Hermes skills relevant to this project + how each is installed into a fresh harness. |
| `cron.md` | The 5 active/paused cron jobs as reproducible definitions (exact prompts + schedules). |
| `protocols.md` | Standing operating protocols for the agent(s) working on HUM (capture discipline, model persistence, two-instance coordination, evidence rules). |
| `bootstrap.sh` | Idempotent, non-destructive script that (1) lays down the HUM file structure from `../templates`, (2) links the `dreams-capture` skill into `~/.hermes/skills`, (3) verifies the Hermes provider config, and (4) prints the exact commands to re-create the cron jobs. |

## Two machines, one operator

This project runs under **two Hermes instances** owned by the same operator:

| Instance | Host | Role |
|----------|------|------|
| **Plato** | MacBook Pro (`macbook-pro.local`) | Primary dev agent; local Ollama; HUM capture. |
| **Hermes** | Mac Studio (`mac-studio.local`) | Heavy inference / long-running gateway; prod dashboard. |

Both share the `~/workspace` tree (kept in sync via git + an SSH fast-path).
Agent-to-agent coordination uses the **file-based blackboard pattern**
(`outbox.jsonl` / `inbox.jsonl` over keyless SSH), because the legacy
`hermes send --to api_server:<peer>` path is a no-op stub in Hermes v0.18.2+.

## Quickstart (fresh install)

```bash
# 1. Lay down HUM files + link the capture skill
bash ~/workspace/projects/hum/hermes/bootstrap.sh ~/workspace/projects/hum

# 2. Re-create the cron jobs (commands printed by bootstrap.sh, or see cron.md)
# 3. Confirm Hermes config has the ollama-local provider (config.reference.md)
# 4. Run one manual surfacing pass to confirm the engine works:
python3 ~/workspace/projects/hum/scripts/surface.py --dreams-dir ~/workspace/projects/hum
```

## Source of truth

- Live Hermes config: `~/.hermes/config.yaml` (read-only reference here).
- Live cron state: `~/.hermes/cron/jobs.json`.
- HUM executable: `../scripts/{capture,surface}.py`; protocol: `../DREAMS_PROTOCOL.md`.
- This documentation was generated from the **actual** running config on
  2026-07-18 (Plato @ MacBook Pro). Re-validate against live state before
  trusting it on a new machine.
