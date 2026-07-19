"""HUM dashboard data layer.

Reads the real HUM/DREAMS corpus through the existing ``src.hum`` parser,
schema, scoring, and recurrence machinery (no re-parsing, no duplicated logic),
then projects it to a JSON model the web UI consumes. Also merges the two-machine
corpora (Plato / Hermes) and computes a transparent convergence score.

This module is READ-ONLY with respect to the corpus: it never writes to
``HUM_DIR``. The surfacing cron owns writes.
"""
from __future__ import annotations

import os
from typing import Any, Optional

from . import parser, schema, scoring, recurrence, store
from .schema import Fragment, content_hash

# layers are scanned in this order; order is only cosmetic
LAYERS = [
    "DREAMS", "SURFACE", "DREAMS_DAY", "SUBCONSCIOUS",
    "DREAMS_ARCHIVE", "DREAMS_QUARANTINE",
]

# Type -> discrete hue (hex). Stable, high-separation palette for minimal-clutter reading.
TYPE_COLORS = {
    "OBSERVATION": "#4cc9f0",
    "BEHAVIOUR": "#4895ef",
    "ASSOCIATION": "#560bad",
    "QUESTION": "#f72585",
    "CONTRADICTION": "#ff6b35",
    "RESISTANCE": "#e63946",
    "SEED": "#2ec4b6",
    "WARNING": "#ffd166",
}
MACHINE_COLORS = {"plato": "#22d3ee", "hermes": "#f59e0b", "shared": "#f8fafc"}


def _read(path: str) -> str:
    return store.read_text(path) if os.path.exists(path) else ""


def _record(layer: str, fm: dict, body: str, ch: str, scores: dict) -> dict:
    src = (fm.get("source") or {}) if isinstance(fm.get("source"), dict) else {}
    refs = fm.get("references") or src.get("references") or []
    if isinstance(refs, str):
        refs = [refs]
    return {
        "id": str(fm.get("id", "")),
        "layer": layer,
        "type": str(fm.get("type", "?")).upper(),
        "status": str(fm.get("status", "?")),
        "created_at": fm.get("created_at"),
        "updated_at": fm.get("updated_at"),
        "total_weight": scores["total_weight"],
        "scores": scores,
        "recurrence_count": int(fm.get("recurrence_count", 1) or 1),
        "first_seen": fm.get("first_seen"),
        "last_seen": fm.get("last_seen"),
        "trust_level": str(src.get("trust_level", "unknown")),
        "task": src.get("task"),
        "references": list(refs),
        "evidence_for": fm.get("evidence_for") or [],
        "evidence_against": fm.get("evidence_against") or [],
        "content_hash": ch,
        "text": body,
    }


def _edges(fragments: list[dict]) -> list[dict]:
    """Derive intra-machine edges: reference, recurrence, contradiction,
    and same-record co-occurrence (fragments parsed from the same layer file
    are genuinely related and need a link so the layout holds together)."""
    by_id = {f["id"]: f for f in fragments if f["id"]}
    hash_groups: dict[str, list[str]] = {}
    for f in fragments:
        hash_groups.setdefault(f["content_hash"], []).append(f["id"])
    edges: list[dict] = []

    for f in fragments:
        for ref in f.get("references", []):
            if ref in by_id and ref != f["id"]:
                edges.append({"source": f["id"], "target": ref, "kind": "reference"})
        # contradiction: a fragment whose evidence_against text names a known id
        for ev in f.get("evidence_against", []) or []:
            if isinstance(ev, str):
                for tid in by_id:
                    if tid != f["id"] and tid in ev:
                        edges.append({"source": f["id"], "target": tid,
                                      "kind": "contradiction"})

    # recurrence: same content hash appearing more than once -> link the copies
    for ch, ids in hash_groups.items():
        if len(ids) > 1:
            for i in range(len(ids)):
                for j in range(i + 1, len(ids)):
                    edges.append({"source": ids[i], "target": ids[j],
                                  "kind": "recurrence"})

    # same-record co-occurrence: fragments sharing a layer file are parsed
    # from the same DREAMS/SURFACE record and are linked so the graph is connected.
    by_layer: dict[str, list[str]] = {}
    for f in fragments:
        by_layer.setdefault(f.get("layer", ""), []).append(f["id"])
    for ids in by_layer.values():
        for i in range(len(ids) - 1):
            edges.append({"source": ids[i], "target": ids[i + 1],
                          "kind": "co-occurs"})

    return edges


def build_machine_model(hum_dir: str, machine_id: str = "plato",
                        host: Optional[str] = None,
                        pulled_at: Optional[str] = None) -> dict:
    """Build the JSON model for a single machine's HUM_DIR."""
    import yaml

    fragments: list[dict] = []
    invalid = 0
    by_layer: dict[str, int] = {}
    by_type: dict[str, int] = {}
    by_status: dict[str, int] = {}
    by_trust: dict[str, int] = {}
    weight_hist = [0] * 10
    hashes: set[str] = set()

    prior = recurrence.scan_store(hum_dir)

    for layer in LAYERS:
        text = _read(os.path.join(hum_dir, f"{layer}.md"))
        if not text.strip():
            continue
        for b in parser.parse_document(text):
            if not b["fm_ok"]:
                invalid += 1
                continue
            try:
                fm = yaml.safe_load(b["raw_fm"]) or {}
            except Exception:
                invalid += 1
                continue
            if schema.validate_front_matter(fm):
                invalid += 1
                continue
            body = b["body"]
            ch = content_hash(body)
            frag = Fragment(fm, body, fm_ok=True)
            frag.content_hash = ch
            pc, _first = recurrence.lookup(prior, ch)
            frag.scores = scoring.score(frag, pc)
            rec = _record(layer, fm, body, ch, frag.scores)
            fragments.append(rec)
            hashes.add(ch)

            by_layer[layer] = by_layer.get(layer, 0) + 1
            by_type[rec["type"]] = by_type.get(rec["type"], 0) + 1
            by_status[rec["status"]] = by_status.get(rec["status"], 0) + 1
            by_trust[rec["trust_level"]] = by_trust.get(rec["trust_level"], 0) + 1
            idx = min(9, int(rec["total_weight"] * 10))
            weight_hist[idx] += 1

    return {
        "machine_id": machine_id,
        "host": host,
        "hum_dir": hum_dir,
        "pulled_at": pulled_at,
        "n_valid": len(fragments),
        "n_invalid": invalid,
        "facets": {
            "by_layer": by_layer,
            "by_type": by_type,
            "by_status": by_status,
            "by_trust": by_trust,
            "weight_hist": weight_hist,
        },
        "fragments": fragments,
        "edges": _edges(fragments),
        "content_hashes": sorted(hashes),
    }


def _jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 1.0
    return len(a & b) / len(a | b)


def convergence(plato: dict, hermes: dict) -> dict:
    """Transparent composite of how similar the two corpora are (0..1)."""
    tp = set(plato["facets"]["by_type"]) or set()
    th = set(hermes["facets"]["by_type"]) or set()
    rp = set(plato["facets"]["by_trust"]) or set()
    rh = set(hermes["facets"]["by_trust"]) or set()
    hp = set(plato.get("content_hashes", []))
    hh = set(hermes.get("content_hashes", []))
    shared = sorted(hp & hh)

    n_p = plato["n_valid"]
    n_h = hermes["n_valid"]
    count_sym = 1.0 - abs(n_p - n_h) / max(n_p, n_h, 1)

    type_j = _jaccard(tp, th)
    trust_j = _jaccard(rp, rh)
    # composite: mean of the three transparent components
    symmetry = round((type_j + trust_j + count_sym) / 3.0, 3)

    return {
        "type_jaccard": round(type_j, 3),
        "trust_jaccard": round(trust_j, 3),
        "trust_overlap": sorted(rp & rh),
        "shared_content_hashes": shared,
        "shared_count": len(shared),
        "count_symmetry": round(count_sym, 3),
        "symmetry_index": symmetry,
    }


def merge_models(plato: dict, hermes: dict) -> dict:
    """Combine both machines into one origin-tagged model for the canvas."""
    plato_hashes = set(plato.get("content_hashes", []))
    hermes_hashes = set(hermes.get("content_hashes", []))
    shared = plato_hashes & hermes_hashes

    fragments = []
    for f in plato["fragments"]:
        r = dict(f)
        r["origin"] = "plato"
        r["shared"] = f["content_hash"] in shared
        fragments.append(r)
    for f in hermes["fragments"]:
        r = dict(f)
        r["origin"] = "hermes"
        r["shared"] = f["content_hash"] in shared
        fragments.append(r)

    # cross-machine "shared" edges: fragments with the same content hash on both
    by_hash: dict[str, list[dict]] = {}
    for f in fragments:
        by_hash.setdefault(f["content_hash"], []).append(f)
    edges = list(plato["edges"]) + list(hermes["edges"])
    for ch, group in by_hash.items():
        if ch in shared and len(group) > 1:
            ids = [g["id"] for g in group]
            for i in range(len(ids)):
                for j in range(i + 1, len(ids)):
                    edges.append({"source": ids[i], "target": ids[j], "kind": "shared"})

    return {
        "fragments": fragments,
        "edges": edges,
        "shared_content_hashes": sorted(shared),
    }


def build_merged(plato: dict, hermes: Optional[dict]) -> dict:
    """Top-level model the UI consumes: per-machine + merged + convergence."""
    if hermes is None:
        hermes = build_machine_model(plato["hum_dir"], machine_id="hermes",
                                      host="(unavailable)")
    return {
        "generated_at": _now(),
        "machines": {"plato": plato, "hermes": hermes},
        "merged": merge_models(plato, hermes),
        "convergence": convergence(plato, hermes),
    }


def _now() -> str:
    import datetime as _dt
    return _dt.datetime.now().astimezone().isoformat(timespec="seconds")


# ---- remote pull (config.yaml-independent, read-only rsync over SSH) --------

def pull_hermes(host: str, remote_dir: str, cache_dir: str,
                timeout: int = 30) -> tuple[bool, str]:
    """rsync the remote HUM_DIR into a local cache. Read-only.

    Returns (ok, message). Never writes to the remote.
    """
    import subprocess

    os.makedirs(cache_dir, exist_ok=True)
    remote = f"{host}:{remote_dir.rstrip('/')}/"
    cmd = [
        "rsync", "-az", "--delete",
        "-e", "ssh -o BatchMode=yes -o StrictHostKeyChecking=no",
        remote, cache_dir.rstrip("/") + "/",
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return False, f"rsync to {host} timed out after {timeout}s"
    except FileNotFoundError:
        return False, "rsync binary not found"
    if proc.returncode != 0:
        return False, f"rsync failed ({proc.returncode}): {proc.stderr.strip() or proc.stdout.strip()}"
    return True, f"pulled {host}:{remote_dir} -> {cache_dir}"


def default_hum_dir() -> str:
    return os.environ.get("HUM_DIR") or os.path.expanduser("~/.hermes/hum")
