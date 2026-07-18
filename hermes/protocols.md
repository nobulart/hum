# Operating protocols (agent behaviour contracts)

Standing rules the agent(s) must follow when working on this project. These are
enforced by memory/prompt, not by code — treat them as load-bearing.

## 1. HUM capture is MANDATORY (not discretionary)

After **every non-trivial task** — defined as any of: 5+ tool calls, a user
correction, a contradiction with a prior claim, or a hard debugging loop — the
agent MUST run `dreams-capture` with the actual signals observed, **before**
declaring the task done. Do a final capture pass before ending a substantive
session.

Rationale (2026-07-17 incident): capture was discretionary and was skipped
exactly during the longest, most correction-dense debugging day, leaving only 2
fragments across the whole session. Discretionary capture fails precisely when
the signal is richest.

```bash
cd ~/workspace/projects/hum
python3 scripts/capture.py --dreams-dir . --type <TYPE> \
  --task "<session name>" --evidence "..." --body "..."
# TYPES: OBSERVATION BEHAVIOUR ASSOCIATION QUESTION CONTRADICTION
#        RESISTANCE SEED WARNING
```

Never hand-write `DREAMS.md` YAML — `capture.py` owns id-gen, validation, dedup,
atomic append.

## 2. Operational-status claims require LIVE evidence

Never assert "running / operational / fixed / persisted" from config, dry-run,
or exit-code inference alone. Prove it with `ps`, `lsof`, `curl`, or a feed
read. The 2026-07-17 "HUM is operational" claim was false because it was based
on config, not on the errored `last_status`.

## 3. Model persistence (dashboard)

- Model selection lives in `backend/models.json` (dashboard repo), loaded at
  startup by `app.py` via `_load_models_from_json()` and saved on every
  `/api/model` POST.
- Changing `models.json` does **not** hot-apply; the dashboard process must be
  restarted to pick it up.
- Both instances read the same `models.json` → cross-instance parity holds.

## 4. Two-instance coordination

- **Plato** (MacBook Pro, `macbook-pro.local`) and **Hermes** (Mac Studio,
  `mac-studio.local`) share `~/workspace` via git + SSH fast-path.
- Cross-instance messaging uses the **file blackboard** (`outbox.jsonl` /
  `inbox.jsonl` over keyless SSH). The legacy `hermes send --to api_server:<peer>`
  path is a no-op stub in Hermes v0.18.2+ — do not use it.
- Gateway-to-gateway calls from this laptop to `mac-studio.local:8642` require
  the correct auth header; an `Invalid API key` means the wrong credential is
  being sent, not that the endpoint is down.

## 5. Rendering: real OctaneX, never model-generated images

Prompts starting with "Visualise…" route through the OctaneX MCP (`octanex-mcp`
skill) and produce a **real** `preview.png` (report file size + timestamp). A
model-generated image is never an acceptable substitute. Every rendered product
is inspected with the local vision model (`vision_analyze`) before being
declared done.

## 6. Email discipline

The agent's address is **`plato@nobulart.com`**. It must never send from any
other address (Craig's mailboxes: `craig.stone@nobulart.com`,
`crg.stn@gmail.com`) without explicit authorisation.

## 7. Config edits: use `hermes config set`, not hand-edits

Scalar/map-typed keys (e.g. `openrouter`) are type-sensitive. A string where a
map is expected crashes the cron scheduler at dispatch (see
`config.reference.md`). Always `hermes config set <key> <value>`, then verify
by running one cron job and checking `last_status`.

## 8. Evidence discipline for research/claims

Separate observation / inference / hypothesis / prediction. Label speculative
inference as speculative. Never fabricate citations, data, file contents, or
command output. If a fact is unknown, say so and propose how to determine it.
