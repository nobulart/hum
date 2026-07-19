# HUM Dashboard — Design Proposal (v2: real data + dual-machine)

A web-based, minimal-clutter interactive canvas for exploring the HUM/DREAMS
data corpus and its slow-cognition processes — **on both Plato (MacBook Pro)
and Hermes (Mac Studio)**, in the same UI, with built-in comparison.

> Status: **design proposal** (not yet built). Grounded in (a) a full read of the
> `src/hum` package, (b) **live parsing of the real `~/.hermes/hum` on both
> machines** via `src/hum` (empirical snapshot below), and (c) **live npm registry
> versions** captured 2026-07-18 (web search/Firecrawl were unavailable this
> session, so narrative is from knowledge; versions are from the npm registry).

---

## 1. TL;DR — recommendation

- **Backend:** reuse the existing `src/hum` package (parser, schema, scoring,
  recurrence) behind a thin read-only server. Run the server on **Plato**
  (MacBook). It builds a model of the **local** `HUM_DIR` and, on demand/on a
  timer, **rsyncs the remote `HUM_DIR` from `mac-studio.local`** (passwordless
  SSH confirmed working) into a local cache, then builds the Hermes model too.
  No server is required on the Studio — this is config.yaml-independent and
  respects the "don't reconfigure Studio" principle.
- **Frontend:** **Vite + TS + React 19 + react-three-fiber (three.js)** as the
  single exploration canvas, **d3** for force math + facet micro-charts,
  **zustand** for state.
- **Primary view:** a **force-directed fragment graph** (nodes=fragments,
  edges=reference/recurrence/contradiction), color = fragment *type*, size =
  *weight*, plus a **machine-origin halo** (Plato vs Hermes vs shared).
- **Dual-machine:** a top-level machine selector **Plato | Hermes | Both**, plus
  facet **compare panels** and a **convergence score** that quantify how
  similar the two agents' dream corpora are.
- **Process view:** a toggleable **lifecycle layer-flow**, rendered as two
  parallel lanes (one per machine) so cross-machine process divergence is visible.

---

## 2. What the real data looks like (empirical, 2026-07-18)

Parsed with `src/hum` from the live `HUM_DIR` on each host:

| Metric | **Plato** (`/Users/craig/.hermes/hum`) | **Hermes** (`~/.hermes/hum` on mac-studio.local) |
|---|---|---|
| Valid fragments | **10** | **5** |
| Invalid / quarantined | **0** | **2** |
| By layer | DREAMS 5, SURFACE 5 | DREAMS 4, SURFACE 1 |
| By type | WARNING 3, OBSERVATION 2, BEHAVIOUR 2, CONTRADICTION 2, RESISTANCE 1 | CONTRADICTION 2, OBSERVATION 2, RESISTANCE 1 |
| By trust | internal_observation 9, tool_output 1 | internal_observation 3, tool_output 1, **user_signal 1** |
| Weight bins (0–1) | 5×[0.4–0.5], 4×[0.7–0.8], 1×[0.9–1.0] | spread: [0.1–0.2],[0.4–0.5],[0.6–0.7],[0.7–0.8],[0.9–1.0] |
| Recurrence | none (10 distinct hashes) | none (5 distinct hashes) |
| Reference edges | 0 | 0 |

**Why this matters for the design:**
1. **The corpora have already diverged.** Plato is WARNING/BEHAVIOUR-heavy;
   Hermes is CONTRADICTION/RESISTANCE-heavy with a `user_signal` fragment Plato
   lacks. A side-by-side comparison is not speculative — it surfaces this
   immediately.
2. **Data-hygiene divergence:** Hermes has 2 invalid/quarantined fragments;
   Plato has none. The dashboard should show quarantine state per machine.
3. **Scale is currently tiny (~5–10 fragments each).** The graph is *sparse*
   (no reference/recurrence edges yet), so the **facet + flow views carry more
   signal than the graph** at this stage. Design for thousands, but don't
   over-promise the graph early.
4. **No `references` field is populated,** so association edges are empty. The
   schema has no explicit link field (deferred to v0.3+). Recurrence/contradiction
   edges are derivable; association edges need a schema addition or NLP.

---

## 3. The HUM data model (recap, for the build)

Each *fragment* (YAML front matter + `@HH:MM [TYPE] — body`):
`id`, `created_at`, `type` ∈ {OBSERVATION, BEHAVIOUR, ASSOCIATION, QUESTION,
CONTRADICTION, RESISTANCE, SEED, WARNING}, `status` ∈ {night, surfaced, testing,
confirmed, contradicted, carried, dormant, dismissed, escalated, deferred,
forgotten, invalid}, `source`{task, source_type, trust_level, references[]},
`scores`{…, **total_weight** 0–1}, `recurrence_count`, `first_seen`,
`last_seen`, `evidence_for/against[]`, `content_hash`.

Six layers (files): `DREAMS` → `SURFACE` → `DREAMS_DAY` → `SUBCONSCIOUS`, plus
`DREAMS_ARCHIVE` (tombstones) and `DREAMS_QUARANTINE` (invalid).

**Insight targets:** corpus shape (type/status/trust/weight/recurrence) ·
topology (who links/contradicts/recurs) · flow (layer transitions over time) ·
hygiene (quarantine/promotion/decay) · **cross-machine symmetry** (do Plato &
Hermes dream alike?).

---

## 4. Visualization style — comparison & recommendation

| # | Style | HUM fit | Clutter |
|---|---|---|---|
| 1 | **Force-directed graph** (nodes=fragments, edges=links, origin halo) | ★★★ primary | medium (focus+context controls it) |
| 2 | **Lifecycle layer-flow** (two parallel machine lanes) | ★★★ process view | low |
| 3 | **Faceted compare panels** (type/trust/weight side-by-side) | ★★★ comparison | low |
| 4 | **Timeline / recurrence strip** | ★★ temporal | low |
| 5 | **3D semantic space** (weight=height, type=cluster) | ★★ immerse toggle | high (ortho default) |
| 6 | **Sunburst / treemap** | ★ optional hierarchy | medium |

**Recommendation:** #1 default canvas; #2 + #3 are the **dual-machine** payoff;
#4 collapsible; #5 opt-in immerse; #6 nice-to-have.

---

## 5. Tech stack research — live versions (npm, 2026-07-18)

| Package | Version | Role |
|---|---|---|
| `three` | 0.185.1 | Core 3D (WebGL + WebGPU/TSL) |
| `@react-three/fiber` | 9.6.1 | React renderer for three (React 19) |
| `@react-three/drei` | 10.7.7 | Controls, Html, instances |
| `@react-three/postprocessing` | 3.0.4 | Bloom/DOF (optional polish) |
| `d3` | 7.9.0 | Force math, scales, micro-charts |
| `sigma` | 3.0.3 | WebGL 2D graph @ scale (fallback if 3D rejected) |
| `three-mesh-bvh` | 0.9.12 | Raycast/hover acceleration |
| `zustand` | 5.0.14 | State |
| `vite` | 8.1.5 | Build/dev |
| `@tanstack/react-query` | 5.101.2 | Data cache (optional) |

**Engine / framework / backend comparisons** (full tables in v1 doc) — unchanged
conclusion: **three.js + R3F** for the canvas, **d3** for charts/force, **React +
R3F** for UI (reuses your existing Agency Dashboard stack), and a **stdlib
`http.server` + `websockets` backend that wraps `src/hum`** (no FastAPI needed).
Remote fetch adds **zero** new dependencies (plain `subprocess` + `rsync` over SSH).

---

## 6. Architecture — dual-machine, single UI

```
┌──────────────────────────────────────────────────────────────────┐
│  Browser (Vite + React + R3F canvas + d3 facet panels)             │
│   machine selector:  [ Plato | Hermes | Both ]                     │
│   ├─ Graph view (force-directed, origin halo)        [default]     │
│   ├─ Flow view  (two parallel lifecycle lanes)       [toggle]     │
│   ├─ Compare panels (Plato vs Hermes facet deltas)   [Both mode]   │
│   ├─ Timeline strip                                          │
│   └─ Inspector + ⌘K bar (collapsed by default)             │
└───────────┬──────────────────────────────┬──────────────────────┘
            │ GET /api/hum  │ WS /ws/hum    │ POST /api/pull (refresh Hermes)
            ▼               ▼                ▼
┌──────────────────────────────────────────────────────────────────┐
│  Python server on PLATO  (wraps src/hum — no re-parse)             │
│   build_model(local HUM_DIR)              → machines.plato         │
│   rsync mac-studio.local:~/.hermes/hum → cache/hum-studio         │
│   build_model(cache/hum-studio)          → machines.hermes         │
│   merge() → origin tags + convergence metrics                      │
│   watches both dirs; pushes on change                              │
└───────┬──────────────────────────────────────────┬───────────────┘
        ▼ (read-only)                             ▼ (rsync pull, SSH)
  /Users/craig/.hermes/hum                  mac-studio.local:~/.hermes/hum
  (Plato, local)                            (Hermes, remote — no server)
```

### Why pull-via-rsync (not a second server)
- **Config.yaml-independent** — uses existing SSH trust + the `HUM_DIR`
  convention already employed by the surfacing cron. No new yaml, no new
  daemon on Studio.
- **Single source of truth for the UI** — one instance, one WS, one model merge.
- **Cron-safe & read-only** — the dashboard never writes either `HUM_DIR`; the
  surfacing cron owns writes. Pull is a read-only rsync into a cache dir.
- Verified working: `ssh mac-studio.local` succeeded passwordless; `rsync -az
  mac-studio.local:~/.hermes/hum/ /tmp/hum-studio/` returned exit 0.

### Backend model emitted (`GET /api/hum`)

```jsonc
{
  "generated_at": "ISO-8601",
  "machines": {
    "plato":  { "host": "macbook-pro.local", "hum_dir": "/Users/craig/.hermes/hum",
                "pulled_at": null, "n_valid": 10, "n_invalid": 0,
                "facets": { "by_type": {...}, "by_trust": {...}, "weight_hist": [...], "by_layer": {...} },
                "process": { "last_surface": "...", "next_surface": "...", "stage_counts": {...} },
                "fragments": [ /* full fragment records */ ] },
    "hermes": { "host": "mac-studio.local", "hum_dir": "<cache>/hum-studio",
                "pulled_at": "ISO-8601", "n_valid": 5, "n_invalid": 2, "facets": {...},
                "process": {...}, "fragments": [ ... ] }
  },
  "merged": {
    "fragments": [ /* each tagged origin: ["plato"] | ["hermes"] | ["plato","hermes"] (shared content_hash) */ ],
    "edges": [ { "source": "id", "target": "id", "kind": "reference|recurrence|contradiction" } ],
    "convergence": {
      "type_jaccard": 0.0,          // no shared types in current data
      "shared_content_hashes": [],  // empty now; fills as recurrence appears
      "trust_overlap": ["internal_observation","tool_output"],
      "symmetry_index": 0.42        // composite 0..1 of corpus similarity
    }
  }
}
```

`build_model()` lives in a new `src/hum/dashboard.py` importing `parser`,
`schema`, `scoring`, `recurrence`, `store` — **scoring/recurrence inherited
verbatim**; the dashboard only projects to JSON. A `merge()` helper computes
origin tags (by `content_hash`) and the convergence metrics.

---

## 7. Dual-machine UX (the core new requirement)

- **Machine selector (top bar):** `Plato` · `Hermes` · `Both`. Default `Both`
  so divergence is visible from first load.
- **Graph — Both mode:** each node gets an **origin halo** — Plato = cyan,
  Hermes = amber, shared-by-hash = white. Currently no shared hashes, so you'll
  see two loosely-grouped clusters → a visual read of "these agents dream apart."
- **Compare panels:** side-by-side facet histograms (type, trust, weight, status,
  quarantine) with **delta highlighting** (e.g. WARNING: Plato 3 vs Hermes 0 →
  red; user_signal: Hermes 1 vs Plato 0 → amber). This is where the empirical
  divergences in §2 become obvious at a glance.
- **Convergence badge:** one 0–1 score + breakdown (type Jaccard, trust overlap,
  shared hashes). Low score = the agents are developing distinct subconsciouses.
- **Flow — two lanes:** Plato and Hermes pipelines shown in parallel; stage
  counts (`night/surfaced/day/subconscious/quarantine`) per machine; hygiene
  divergences (Hermes quarantine=2) flagged.
- **Diff view:** "On Hermes only" / "On Plato only" / "Quarantined on Hermes".
- **Pull control:** a refresh button (and auto-pull every N s / on WS trigger)
  re-rsyncs Studio and updates the model live.

---

## 8. Phased plan

| Phase | Work | Acceptance |
|---|---|---|
| **0 — Model** | `src/hum/dashboard.py`: `build_model(hum_dir)`, `merge(plato, hermes)`, `convergence()`. Unit-tested against real `HUM_DIR` + a synthetic 6-file set | JSON matches §6 schema; 22/22 existing tests green |
| **1 — Server** | `dashboard/app.py`: stdlib `http.server` + `websockets`; `GET /api/hum`, `WS /ws/hum`; `HUM_DIR` env | `curl` returns valid model; WS pushes on file change |
| **1.5 — Remote pull** | `pull_hermes()` = `rsync` over SSH into cache; `POST /api/pull`; auto-pull timer; read-only, config.yaml-independent | Pulls Studio corpus; both machines in one model |
| **2 — Canvas** | Vite+React+R3F; force-directed graph (d3-force-3d); type color, weight size, **origin halo**; hover inspector; ⌘K | Renders both corpora; hover/click/filter < 16ms |
| **3 — Compare & process** | Machine selector; facet compare panels w/ deltas; convergence badge; two-lane flow view; timeline; diff view | Toggle Plato/Hermes/Both; facets filter canvas |
| **4 — Polish** | drei controls, subtle postprocessing, WebGPU toggle, empty/loading/quarantine/diverged states | Clean idle; WebGPU renders identically |
| **5 — Live** | Point at real `~/.hermes/hum` (both); cron-safe read-only; optional launchd plist | Runs locally; survives a surfacing pass |

**Definition of done:** a local URL showing the **real** HUM corpus from **both
machines** as an interactive, clutter-minimal canvas with graph + compare +
process views, reading exclusively through `src/hum`, with zero duplicated
parsing and zero writes to either `HUM_DIR`.

---

## 9. Risks & open questions

- **WebGPU maturity** — WebGL default; TSL enhancement only.
- **Edge semantics for `association`** — v0.2 has no explicit link field;
  recurrence/reference/contradiction edges derivable now, association needs schema
  addition or NLP (deferred to v0.3+).
- **Sparse early graph** — at current scale (~5–10 frags, no refs) the graph is
  disconnected; facets/flow carry the signal. Don't oversell the graph early.
- **Remote pull latency/staleness** — rsync is fast on LAN; cache freshness shown
  via `pulled_at`. Add manual refresh + timer.
- **SSH dependency** — pull requires passwordless SSH to Studio (confirmed
  working). If it breaks, Plato-only mode must degrade gracefully.
- **Cross-machine fragment matching** — exact `content_hash` match is trivial;
  *semantic* near-dup (the real "do they dream the same thought?") needs v0.3+
  semantic recurrence. v2 comparison is aggregate + exact-hash only.
- **Clutter creep** — guardrail: new panels default to collapsed.

## 10. What could not be verified

Web search (SearXNG) + Firecrawl were unavailable this session. Library
*versions* are from the **live npm registry** (authoritative for "latest");
library *commentary* is from knowledge. Re-run web research once the search
backend is reachable to enrich with current benchmarks.
