# Cron jobs — reproducible definitions

Read from the live `~/.hermes/cron/jobs.json` on 2026-07-18. Each job below
shows its schedule, prompt, and current state. To recreate on a fresh install,
use `cronjob create` (or the Hermes CLI) with the **exact prompt text** shown.

> **Model note:** every job runs on `provider_snapshot: custom` →
> `rafw007/Qwen3.6-35B-A3B-mlx-claude-coder-abliterated:latest` (the configured
> default). No per-job model override is set.

---

## 1. `workspace_monitor` — ACTIVE

- **id:** `527a482cd858`
- **schedule:** every 1m (`interval`)
- **deliver:** local
- **purpose:** detect any change in `~/workspace`; return `[SILENT]` when nothing changed.

```
Check the shared workspace at ~/workspace and report any changes since the last check.

IMPORTANT: Return exactly [SILENT] if there are no new or modified files. Only deliver a report when something has actually changed.

Look for:
1. New or modified files in ~/workspace
2. Changes to our notes (plato_notes.md, hermes_intro.md, office_blackboard.md)
3. New files dropped by Hermes or Craig
4. Any unusual changes (new documents, updates from other agents)

Only report if something is new or changed. [SILENT] otherwise.
```

## 2. `dashboard monitor` — PAUSED

- **id:** `fdac860c0b94`
- **schedule:** every 15m (`interval`)
- **deliver:** local (origin: telegram)
- **skills:** `["hermes-agent"]`
- **purpose:** heartbeat check of the agency dashboard at `http://localhost:9200`.

```
Check the agency dashboard at http://localhost:9200 and report the status of agents, cron jobs, and any changes. Send a brief update.
```

> Paused since 2026-07-07. Likely redundant with `workspace_monitor`. Re-enable
> only if a dedicated dashboard heartbeat is wanted.

## 3. `plato email checker` — PAUSED + BROKEN

- **id:** `adca15935807`
- **schedule:** every 30m (`interval`)
- **script:** `daily_email_checker.sh`
- **deliver:** origin
- **last_status:** **error** — `AttributeError: 'str' object has no attribute 'get'`

⚠️ **Broken:** the referenced script `daily_email_checker.sh` does **not exist**
in `~/workspace/tools/` (only `daily_skills_sync.sh` is present). The job errors
on every tick. It is also paused. **Do not re-enable until the script exists.**
The intended behaviour: check `crg.stn@gmail.com` via `himalaya`, classify mail
addressed to `plato@nobulart.com`, reply from `plato@nobulart.com` only (never
from Craig's mailboxes).

## 4. `daily_skill_sync` — ACTIVE

- **id:** `0fe6d6268010`
- **schedule:** `0 8 * * *` (daily 08:00)
- **deliver:** local
- **script:** `/Users/craig/workspace/tools/daily_skills_sync.sh` ✅ (exists)

```
Run the daily skill synchronization.

Execute: /Users/craig/workspace/tools/daily_skills_sync.sh

Check for any new or updated skills in ~/workspace/tools/skills/ and report what was found and what was synced.
```

## 5. `DREAMS morning surfacing` — ACTIVE (critical for HUM)

- **id:** `cca7a54f6744`
- **schedule:** `0 7 * * *` (daily 07:00)
- **deliver:** origin
- **purpose:** run the HUM morning surfacing, graduate DREAMS → SURFACE, reset DREAMS.

```
Run the DREAMS morning surfacing for the local HUM install. This is a self-contained task; no prior chat context is available.

Steps:
1. Execute the surfacing script (do NOT use --dry-run — this is the real morning pass):
   python3 /Users/craig/workspace/projects/hum/scripts/surface.py --dreams-dir /Users/craig/workspace/projects/hum
   (Use the script's own config.yaml for budget/threshold — do NOT pass --threshold, because the running v0.2 engine keys off config.yaml, not a hardcoded CLI threshold.)
2. After it runs, read /Users/craig/workspace/projects/hum/SURFACE.md to confirm the surfaced fragments were written, and confirm /Users/craig/workspace/projects/hum/DREAMS.md was reset to just its header + "## Fragments".
3. If the script reports an error or DREAMS.md was not reset, report the failure plainly and do NOT attempt to manually edit the files.
4. Deliver a brief Morning Surfacing summary to the user covering: how many fragments surfaced, their ids, and the highest-weight one. Keep it under 10 lines. Do not editorialize beyond the protocol.

Note: this cron must not schedule or create any other cron jobs.
```

> **Surfacing budget** (from `../config.yaml`): `budget: 5`, `always_include:
> [WARNING, CONTRADICTION]`, `scoring: evidence_derived` (unknown signals score
> **zero**, never a positive default).

---

## Recreating these jobs

`bootstrap.sh` prints the exact `cronjob create` invocations. The two that must
exist for HUM are **#4** (skill sync) and **#5** (DREAMS surfacing). #1 is the
workspace heartbeat. #2 and #3 are optional/repair-needed.
