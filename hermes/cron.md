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
   python3 /Users/craig/.hermes/hum/scripts/surface.py --dreams-dir /Users/craig/.hermes/hum
   (Use the script's own config.yaml for budget/threshold — do NOT pass --threshold, because the running v0.2 engine keys off config.yaml, not a hardcoded CLI threshold.)
2. After it runs, read /Users/craig/.hermes/hum/SURFACE.md to confirm the surfaced fragments were written, and confirm /Users/craig/.hermes/hum/DREAMS.md was reset to just its header + "## Fragments".
3. If the script reports an error or DREAMS.md was not reset, report the failure plainly and do NOT attempt to manually edit the files.
4. Deliver a brief Morning Surfacing summary to the user covering: how many fragments surfaced, their ids, and the highest-weight one. Keep it under 10 lines. Do not editorialize beyond the protocol.

Note: this cron must not schedule or create any other cron jobs.
```

> **Surfacing budget** (from `../config.yaml`): `budget: 5`, `always_include:
> [WARNING, CONTRADICTION]`, `scoring: evidence_derived` (unknown signals score
> **zero**, never a positive default).

---

## 6. `DREAMS hourly auto-capture` — ACTIVE (companion to manual capture)

- **id:** *(created via `cronjob create` — see below)*
- **schedule:** `every 1h` (`interval`)
- **deliver:** origin (returns exactly `[SILENT]` on quiet hours — no ping)
- **purpose:** automatically distil DREAMS fragments from recent work sessions
  that have gone idle ≥60 min, so slow cognition accumulates without manual
  triggering (protocol §1 made manual capture mandatory; this is the automated
  complement).

```text
Run the HUM DREAMS hourly auto-capture cycle for this machine's sessions.

This is a self-contained task; no prior chat context is available. Goal: surface
DREAMS fragments from recent work sessions that have gone idle, so slow cognition
accumulates without manual triggering.

Steps:
1. Discover candidates:
   python3 /Users/craig/.hermes/hum/scripts/auto_capture.py discover --idle-min 60 --min-tools 5
   If it prints [] or an empty list, there is nothing to do. Print exactly
   [SILENT] and stop.
2. For EACH candidate session in the list:
   a. Extract a condensed transcript:
      python3 /Users/craig/.hermes/hum/scripts/auto_capture.py extract <id> --max-chars 12000
   b. Read it and decide whether any fragment-worthy signal is present, using the
      DREAMS types (OBSERVATION, BEHAVIOUR, ASSOCIATION, QUESTION, CONTRADICTION,
      RESISTANCE, SEED, WARNING). Capture only a concrete observation, a repeated
      correction/behaviour, an unresolved tension, or a speculative cross-domain
      link — NOT routine progress chatter. Be selective; skip low-substance material.
   c. For each genuine signal, capture via the canonical executable (never hand-write
      DREAMS.md):
      python3 /Users/craig/.hermes/hum/scripts/capture.py --dreams-dir /Users/craig/.hermes/hum \
        --type <TYPE> --task "<session title or id>" \
        --body "<one concise fragment sentence>" [--evidence "..."] [--active]
      Use --task from the session title (fall back to session id). Keep bodies to one
      or two sentences. Prefer --evidence when a claim rests on a repeated event.
   d. ALWAYS commit the watermark for the session whether or not you captured anything,
      so it is not re-examined every hour:
      python3 /Users/craig/.hermes/hum/scripts/auto_capture.py commit <id> <last_msg_ts>
      (use the last_msg_ts from the discovery JSON).
3. If you captured one or more fragments, deliver a SHORT summary (under 12 lines):
   how many sessions examined, how many fragments captured, and each fragment's
   id+type. If you examined sessions but captured nothing, print exactly [SILENT].
   Never hand-edit DREAMS.md or any HUM file directly. Do not create other cron jobs.

Note: this cron must not schedule or create any other cron jobs.
```

> **Mechanics.** The helper (`scripts/auto_capture.py`) reads the authoritative
> session store `~/.hermes/state.db` (`sessions` + `messages`, epoch-float
> `messages.timestamp`), not the legacy `sessions.json` mirror. A per-session
> watermark in `~/.hermes/hum/auto_capture_state.json` makes capture idempotent:
> each session is processed at most once per activity burst, so an idle session
> is never re-captured. At install, `seed-history` watermarked all ~1085 existing
> sessions, so the job captures ONLY sessions with activity **after** deployment
> (i.e. genuinely *new* sessions) — no history backfill. `cron`/`subagent`
> sources are excluded; sessions with <5 tool calls are skipped (matches the
> protocol's "non-trivial" definition). Machine scope: this job covers THIS
> instance's `state.db` only; mirror it on the peer (Hermes/Studio) for full
> coverage.

## 7. `HUM Studio pull (dashboard refresh)` — ACTIVE (feeds the dashboard's Studio pane)

- **id:** `828bc5b11c60`
- **schedule:** `every 15m` (`interval`)
- **no_agent:** true (watchdog shell script, no LLM)
- **script:** `~/.hermes/scripts/hum_pull_cron.sh` (2-line wrapper → canonical
  `projects/hum/scripts/hum_pull_cron.sh`)
- **purpose:** keep the dashboard's "hermes" (Mac Studio) column current by
  POST-ing `http://127.0.0.1:8650/api/pull` (read-only rsync Studio →
  `/tmp/hum-studio`, then in-memory rebuild + SSE push). **Without this job the
  Studio pane and `convergence` score silently freeze at the last manual pull.**

```text
Silent on success (watchdog), prints + exits 1 on failure so the scheduler
alerts. Client curl timeout is 120s — comfortably above the dashboard's internal
30s rsync timeout — so a slow-but-healthy pull under Studio load never reports a
false "unreachable".
```

> **Why it exists:** the dashboard's `hermes` corpus is a *pulled cache*
> (`HERMES_CACHE_DIR`, set by the launcher to `/tmp/hum-studio`), not a live
> mount. The pull is manual-only otherwise. Verified live: before this job the
> cache was last pulled 2026-07-18; after first run `hermes n_valid` went
> 5 → 16 and `convergence` 0.462 → 0.771.

## Recreating these jobs

`bootstrap.sh` prints the exact `cronjob create` invocations. The jobs that must
exist for HUM are **#4** (skill sync), **#5** (DREAMS surfacing), **#6**
(hourly auto-capture), and **#7** (Studio pull). #1 is the workspace heartbeat.
#2 and #3 are optional/repair-needed. Before first run of #6, execute once:
`python3 ~/.hermes/hum/scripts/auto_capture.py seed-history` (prevents history
backfill). #7's canonical script lives at `scripts/hum_pull_cron.sh`; the
scheduler wrapper is `~/.hermes/scripts/hum_pull_cron.sh` (the scheduler requires
scripts physically inside its own dir, so the wrapper execs the repo copy to keep
a single source of truth).
