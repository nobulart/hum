# Hermes skills relevant to the HUM project

Skill inventory was read from the live Hermes install (149 skills total). Below
are the ones this project actually relies on, grouped by purpose, with how to
install them into a fresh harness.

> **Two skill namespaces:**
> - **Hermes skills** live in `~/.hermes/skills/<name>/` and are loaded by the
>   agent automatically. Most are bundled or installed via the skill hub.
> - **HUM skills** live in `../skills/<name>/` (part of THIS repo). The only
>   released one is `dreams-capture`; it must be linked into
>   `~/.hermes/skills/` so the agent can invoke it (see bootstrap.sh).

## HUM subsystem (this repo)

| Skill | Location | Status | Install |
|-------|----------|--------|---------|
| `dreams-capture` | `../skills/dreams-capture` | released | `ln -s ../skills/dreams-capture ~/.hermes/skills/dreams-capture` |

`scripts/capture.py` owns id generation, YAML validation, dedup, and atomic
append. The agent should **never** hand-write `DREAMS.md` fragments.

## Core project skills (install via `hermes skills install <name>` or hub)

| Skill | Category | Why it matters here |
|-------|----------|---------------------|
| `hum-subsystem` | — | Operate/monitor the HUM/DREAMS subsystem, the morning-surfacing cron, and dashboard metrics. |
| `workspace-structure` | devops | `~/workspace` folder conventions + routing; both machines share it. |
| `agency-dashboard-interagent-debugging` | software-development | Debug model persistence + interagent chat delivery (the exact subsystem we fixed 2026-07-17). |
| `dashboard-models` | devops | Dashboard model-selection persistence + interagent lifecycle. |
| `hermes-dashboard-launch` | devops | Launch/troubleshoot the dashboard; covers the `HERMES_SERVE_HEADLESS`/`HERMES_WEB_DIST` env traps. |
| `octanex-mcp`, `octane-viz`, `octanex-visual-loop` | creative / mcp | Real OctaneX rendering path (the project mandates real renders, not model-generated images). |
| `hermes-inter-instance-networking`, `inter-instance-blackboard` | devops | Two-machine (MacBook ↔ Mac Studio) coordination via file blackboard + SSH. |
| `cron-email-processing` | — | Email inbox review state machine (used by the email-checker pattern). |
| `query-service`, `rag-processing` | — | ECDO-style query service + RAG corpus pipelines (~324 GB corpus). |
| `scientific-model-comparison`, `constraint-first-scientific-modeling` | research | Hypothesis comparison / constraint-first modeling workflows. |
| `safe-agent-systems`, `auditable-agent-subsystem` | software-development | Patterns for building transactional, auditable agent state (the HUM design lineage). |

## Verifying a skill is present

```bash
hermes skills list | grep -i <name>      # bundled/hub skills
ls -la ~/.hermes/skills/dreams-capture   # HUM skill (symlink expected)
```

## Notes

- The `hermes-agent` skill (inter-instance networking, build guide) is present
  as a git checkout at `~/.hermes/hermes-agent/` but is **not** surfaced in the
  loadable skill list on this install — it is a source tree, not an installed
  skill. Don't assume its commands are available to the agent unless installed.
- If a skill is missing on a fresh install, install from the hub or copy the
  skill directory into `~/.hermes/skills/` and restart the agent.
