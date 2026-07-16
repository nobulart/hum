"""Recurrence detection (exact content hash). Semantic near-dup is deferred to v2+."""
from __future__ import annotations

import os

from . import parser
from .schema import content_hash

# files scanned for *prior* appearances (DREAMS.md is excluded to avoid
# counting the fragment against itself during its own surfacing run)
_PRIOR_FILES = [
    "SURFACE.md", "DREAMS_DAY.md", "SUBCONSCIOUS.md",
    "DREAMS_ARCHIVE.md", "DREAMS_QUARANTINE.md",
]


def scan_store(dreams_dir: str) -> dict[str, list[tuple[str, dict]]]:
    """content_hash -> list of (filename, front_matter) across prior files."""
    import yaml
    store: dict[str, list[tuple[str, dict]]] = {}
    for fn in _PRIOR_FILES:
        p = os.path.join(dreams_dir, fn)
        if not os.path.exists(p):
            continue
        for b in parser.parse_document(open(p, encoding="utf-8").read()):
            if not b["fm_ok"]:
                continue
            try:
                fm = yaml.safe_load(b["raw_fm"]) or {}
            except Exception:
                continue
            h = content_hash(b["body"])
            store.setdefault(h, []).append((fn, fm))
    return store


def lookup(store: dict[str, list[tuple[str, dict]]], h: str):
    """Return (prior_count, first_seen) for a content hash."""
    hits = store.get(h, [])
    count = len(hits)
    first = None
    for _fn, fm in hits:
        fs = fm.get("first_seen") or fm.get("created_at")
        if fs and (first is None or str(fs) < str(first)):
            first = fs
    return count, first
