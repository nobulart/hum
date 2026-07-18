# Hermes `config.yaml` reference (annotated)

Extracted from the live `~/.hermes/config.yaml` on Plato @ MacBook Pro
(2026-07-18). **Secrets are redacted** — never paste a real password hash or
API key into a committed doc. This file is a *reference*, not a drop-in
config; prefer `hermes config set <key> <value>` over hand-editing YAML.

## Model & providers

```yaml
model:
  default: rafw007/Qwen3.6-35B-A3B-mlx-claude-coder-abliterated:latest
  provider: ollama-local
  base_url: ''

providers:
  ollama-local:                       # LOCAL — primary for Plato
    api: http://127.0.0.1:11434/v1
    default_model: rafw007/Qwen3.6-35B-A3B-mlx-claude-coder-abliterated:latest
    models: [ ... rafw007/Qwen3.6-35B-A3B-mlx-claude-coder-abliterated,
               qwen3-coder:30b, qwen3-vl:32b, gemma4:31b-mlx, ornith:35b,
               qwen3.6:35b-mlx, glm-ocr:latest, nomic-embed-text:latest,
               x/z-image-turbo:bf16, x/flux2-klein:9b, x/flux2-klein:4b,
               x/z-image-turbo:fp8 ]
  mac-studio:                        # REMOTE inference on the Studio
    api: http://mac-studio:11434/v1
    default_model: rafw007/Qwen3.6-35B-A3B-mlx-claude-coder-abliterated:latest
    models: [ ... qwen3.6:35b-mlx, ornith:35b, nemotron-3-super:120b, ... ]
  vmlx:
    name: vMLX (Mac Studio)
    api: http://127.0.0.1:8000/v1
    default_model: bearzi/Kimi-K2.7-Code-JANGTQ_K
    context_length: 1048576
  nvidia:
    name: NVIDIA Integration API
    api: https://integrate.api.nvidia.com/v1
    key_env: NVIDIA_API_KEY          # secret — do NOT inline
    default_model: meta/llama-3.3-70b-instruct
    models: [ ... long list ... ]
```

**HUM relevance:** the `ollama-local` provider is what `interagent.py` and the
HUM capture path assume for local generation. If a fresh install only has
remote providers, local-only agent replies will fail.

## Toolsets

```yaml
toolsets:
  - hermes-cli
  - web
# disabled_toolsets: []
```

`hermes-cli` gives the `hermes` command used by cron scripts and blackboard
sync. `web` enables `web_search` / `web_extract`.

## Agent behaviour

```yaml
agent:
  max_turns: 150
  gateway_timeout: 1800
  restart_drain_timeout: 60
  api_max_retries: 3
  service_tier: normal
  tool_use_enforcement: auto
  task_completion_guidance: true
  environment_probe: true
  reasoning_effort: medium
  verify_on_stop: false
```

## Auxiliary models (vision / compression / skill routing)

```yaml
auxiliary:
  vision:
    provider: ollama-local
    model: qwen3-vl:32b          # used for the mandatory "inspect every render" step
    timeout: 120
  compression:
    provider: ollama-local
    model: qwen3-coder:30b
web:
  backend: firecrawl
  search_backend: searxng
```

## Compression / guardrails

```yaml
compression:
  enabled: true
  threshold: 0.35
  target_ratio: 0.2
  protect_last_n: 20
tool_loop_guardrails:
  warnings_enabled: true
  hard_stop_enabled: false
```

## Dashboard (basic auth — REDACTED)

```yaml
dashboard:
  theme: default-large
  show_token_analytics: false
  basic_auth:
    username: craig
    password_hash: scrypt$16384$8$1$<REDACTED — do not commit real hash>
  oauth:
    client_id: ''
    portal_url: ''
  public_url: ''
```

**Setup:** do not hand-edit. Use `hermes config set dashboard.basic_auth.password_hash <value>`
(or let the dashboard set it on first login). Rotate if a hash ever leaks into
a doc or git history.

## ⚠️ Operational pitfall: `openrouter: {}` crashes the cron scheduler

The live config contains:

```yaml
openrouter: {}
```

This is the **empty-map literal**. A prior incident (07:00 surfacing,
2026-07-17) showed that when this key is a *string* (e.g. `openrouter: '{}'`)
the scheduler raises `AttributeError: 'str' object has no attribute 'get'`
at dispatch and **every LLM cron job fails silently** — not just OpenRouter.

**Rule:** never hand-edit scalar/map-typed config keys. Always:

```bash
hermes config set openrouter '{}'     # correct: sets a map, not a string
```

Validate the type after any manual edit by running one cron job and checking
`last_status` via `cronjob list` — do not assume "config looks right" means
"cron runs".

## Privacy / TTS

```yaml
privacy:
  redact_pii: false        # intentional for this operator; revisit if shared
tts:
  provider: edge
  edge: { voice: en-US-AriaNeural }
```
