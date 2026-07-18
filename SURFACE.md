# SURFACE.md

The morning transfer layer. When `DREAMS.md` is read at surfacing time, fragments that
clear the daily budget land here — ranked by `total_weight`, plus any mandatory
high-consequence item. Nothing here is accepted as true merely because it surfaced.

## Surfaced fragments

---
id: dream-20260717T140905-FQFT
type: WARNING
status: surfaced
source:
  task: 2026-07-17 cron diagnostic
  source_type: reflective_observation
  trust_level: internal_observation
evidence:
- all 5 cron jobs errored 07:00 with same AttributeError
- scheduler.py:3188 (_cfg.get('openrouter') or {}).get(...)
surfaced_at: '2026-07-18T07:01:45+02:00'
scores:
  base_significance: 0.25
  recurrence: 0.0
  novelty: 0.0
  utility: 0.0
  active_work_connection: 0.0
  consequence: 0.5
  predictive_or_user: 0.4
  age_decay: 0.0
  contradiction_penalty: 0.0
  provenance_penalty: 0.0
  total_weight: 0.719
counterdream: PENDING
---

A string-form value in ~/.hermes/config.yaml (openrouter: '{}') crashes the ENTIRE cron scheduler at dispatch — every LLM cron job fails with AttributeError: 'str' object has no attribute 'get', not just OpenRouter. One malformed key = silent total cron outage. Prefer 'hermes config set' over hand-edits; validate scalar/map types.
---
id: dream-20260717T140905-R31B
created_at: '2026-07-17T14:09:05+02:00'
type: BEHAVIOUR
status: surfaced
source:
  task: 2026-07-17 HUM dashboard + cron review
  source_type: observed_behaviour
  trust_level: internal_observation
evidence:
- 'user: ''I couldn''t see whether the surfacing cron worked this morning at 7am'''
- cron last_status=error at 07:00:25 despite earlier 'HUM is running' claim
surfaced_at: '2026-07-18T07:01:45+02:00'
scores:
  base_significance: 0.25
  recurrence: 0.0
  novelty: 0.0
  utility: 0.0
  active_work_connection: 0.0
  consequence: 0.0
  predictive_or_user: 0.4
  age_decay: 0.0
  contradiction_penalty: 0.0
  provenance_penalty: 0.0
  total_weight: 0.406
counterdream: PENDING
---

Reported the DREAMS/cron system as 'running/operational' from config + dry-run evidence, without checking the live cron last_run_at / last_status. The 07:00 surfacing had actually errored (AttributeError); the user caught it. Assert operational state only after reading actual execution status, not inferred from setup.

