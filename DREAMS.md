# DREAMS.md

The night's processing layer. Read and cleared each morning.

## Fragments

---
id: dream-20260718T093517-12WS
created_at: '2026-07-18T09:35:17+02:00'
type: OBSERVATION
status: night
source:
  task: 2026-07-17 interagent debugging
  source_type: reflective_observation
  trust_level: internal_observation
evidence:
- HUM capture is agent-discretionary per standing instruction
- DREAMS.md accumulated only 2 fragments across the whole debugging day
---

The DREAMS night layer captured only 2 fragments across an entire long, correction-dense debugging day, because capture is discretionary and was skipped exactly when the session was longest and most signal-rich. Discretionary capture fails precisely when most needed; the safeguard should be non-discretionary (e.g. end-of-session capture pass) so non-trivial work cannot end without a capture attempt.


---
id: dream-20260718T093517-JR8X
created_at: '2026-07-18T09:35:17+02:00'
type: RESISTANCE
status: night
source:
  task: 2026-07-17 interagent debugging
  source_type: reflective_observation
  trust_level: internal_observation
evidence:
- multiple daemon launches continued using cloud gateway despite 413 repeat
- local Ollama path (rafw007/Qwen3.6-35B mlx) eventually produced real posts
---

Persisted in routing interagent through the cloud Hermes gateway despite repeated 413 failures, instead of falling back to the local Ollama path that was demonstrably working. A candidate fix (local-only routing) was deferred/overwritten multiple times. When a fallback path is proven working and the primary is hard-broken, switch don't re-litigate.


---
id: dream-20260718T093517-BFTK
created_at: '2026-07-18T09:35:17+02:00'
type: WARNING
status: night
source:
  task: 2026-07-17 interagent debugging
  source_type: reflective_observation
  trust_level: internal_observation
evidence:
- Hermes api_server returned 413 on small payloads from this laptop
- local Ollama on :11434 worked; cloud path hard-blocked
---

Misread a hard ceiling as transient: Hermes cloud gateway returned 413 ('payload too large') repeatedly on small payloads from this MacBook, but I initially treated it as intermittent and kept retrying the cloud path. A hard, reproducible error code under a single condition is a structural block, not transient noise — diagnose it as a ceiling, not a flake.


---
id: dream-20260718T093517-X9HP
created_at: '2026-07-18T09:35:17+02:00'
type: CONTRADICTION
status: night
source:
  task: 2026-07-17 interagent debugging
  source_type: reflective_observation
  trust_level: internal_observation
active: true
evidence:
- 08:00 surfacing cron last_status=error (AttributeError)
- I had earlier reported HUM/cron as 'running/operational'
---

Claimed the DREAMS/cron system was operational from config + dry-run evidence, while the 07:00 surfacing run had actually errored (AttributeError: 'str' object has no attribute 'get' from openrouter: '{}' in config.yaml). Asserting 'operational' from setup rather than execution status is a contradiction with reality and was caught by the user.


---
id: dream-20260718T093517-X354
created_at: '2026-07-18T09:35:17+02:00'
type: BEHAVIOUR
status: night
source:
  task: 2026-07-17 interagent debugging
  source_type: observed_behaviour
  trust_level: internal_observation
evidence:
- 'user: ''stop guessing'''
- 'user: ''don''t claim success once restarted'''
---

During long debugging sessions I repeatedly restarted daemons and asserted progress from config/exit-code evidence rather than reading live feed state. Repeated user corrections ('stop guessing', 'the only acceptable next step is...', 'don't claim success once restarted') show a default tendency to report inferred operational status. Correct behaviour: assert operational only after live ps/curl/feed evidence.

