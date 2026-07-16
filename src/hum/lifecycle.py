"""Lifecycle: classify fragments into four outcomes and apply a surfacing budget.

Outcomes (per review v0.2):
  surfaced   -> SURFACE.md
  deferred   -> remains in DREAMS.md with updated review metadata
  forgotten  -> hash-only tombstone in DREAMS_ARCHIVE.md
  invalid    -> DREAMS_QUARANTINE.md (never silently defaulted)

Surfacing uses a BUDGET (top-N by total_weight) plus mandatory inclusion of any
high-consequence WARNING/CONTRADICTION. This replaces the meaningless absolute
threshold of v0.1.
"""
from __future__ import annotations

import datetime as _dt

from . import scoring, recurrence
from .parser import serialize_block
from .schema import validate_front_matter, content_hash, Fragment

HIGH_CONSEQUENCE = {"WARNING", "CONTRADICTION"}
DEFER_AFTER = 3  # surface attempts before a non-selected fragment is forgotten


def classify(dreams_dir: str, budget: int, now: _dt.datetime | None = None):
    """Read DREAMS.md, score, classify. Returns a dict of outcomes + report.

    Pure-ish: parses and scores but does NOT write. Writing is done by the
    caller via store.atomic_write so the whole run is transactional.
    """
    now = now or _dt.datetime.now().astimezone()
    from . import store, parser
    import yaml

    text = store.read_text(f"{dreams_dir}/DREAMS.md")
    raw_blocks = parser.parse_document(text)
    prior = recurrence.scan_store(dreams_dir)

    frags: list[Fragment] = []
    for b in raw_blocks:
        if not b["fm_ok"]:
            frags.append(Fragment({}, b["body"], b["raw_fm"], fm_ok=False,
                                  error=b.get("error", "malformed front matter")))
            continue
        try:
            fm = yaml.safe_load(b["raw_fm"]) or {}
        except Exception as e:
            frags.append(Fragment({}, b["body"], b["raw_fm"], fm_ok=False, error=str(e)))
            continue
        # ensure id exists (capture.py assigns; legacy may lack)
        if not fm.get("id"):
            fm["id"] = f"dream-{now.strftime('%Y%m%dT%H%M%S')}-LEGACY"
        frag = Fragment(fm, b["body"], b["raw_fm"], fm_ok=True)
        errs = validate_front_matter(fm)
        if errs:
            frag.fm_ok = False
            frag.error = "; ".join(errs)
            frags.append(frag)
            continue
        frag.content_hash = content_hash(frag.body)
        pc, first = recurrence.lookup(prior, frag.content_hash)
        if pc and pc >= 1 and int(fm.get("recurrence_count", 1) or 1) < 2:
            fm["recurrence_count"] = max(2, pc + 1)
            if not fm.get("first_seen") and first:
                fm["first_seen"] = str(first)[:10]
        frag.scores = scoring.score(frag, pc)
        frags.append(frag)

    surfaced: list[Fragment] = []
    deferred: list[Fragment] = []
    forgotten: list[Fragment] = []
    invalid: list[Fragment] = []

    valid = [f for f in frags if f.fm_ok]
    # rank by total_weight desc
    valid.sort(key=lambda f: f.scores["total_weight"], reverse=True)
    high_consequence = [f for f in valid
                        if str(f.fm.get("type", "")).upper() in HIGH_CONSEQUENCE]
    others = [f for f in valid if f not in high_consequence]

    # mandatory high-consequence always surfaces
    chosen_ids = {id(f) for f in high_consequence}
    for f in high_consequence:
        surfaced.append(f)

    remaining_budget = max(0, budget - len(surfaced))
    for f in others:
        if remaining_budget > 0:
            surfaced.append(f)
            remaining_budget -= 1
        else:
            f.deferred_count = int(f.fm.get("deferred_count", 0) or 0) + 1
            if f.deferred_count >= DEFER_AFTER:
                forgotten.append(f)
            else:
                deferred.append(f)

    invalid.extend(f for f in frags if not f.fm_ok)
    # nothing is auto-forgotten without a deferral history in v0.2 (preserve
    # non-survivors by default); only deferred-then-exhausted become tombstones

    return {
        "frags": frags, "surfaced": surfaced, "deferred": deferred,
        "forgotten": forgotten, "invalid": invalid, "now": now,
    }


def render_outputs(res: dict, dreams_dir: str) -> dict[str, str]:
    """Build the new file contents for each outcome file (no writes yet)."""
    surfaced_md = _append_blocks(f"{dreams_dir}/SURFACE.md", res["surfaced"],
                                 res["now"])
    # deferred stay in DREAMS.md (updated metadata)
    deferred_md = _deferred_dreams(res["deferred"], res["now"])
    quarantine_md = _invalid_blocks(res["invalid"])
    archive_md = _tombstones(res["forgotten"], res["now"])
    return {
        "SURFACE.md": surfaced_md,
        "DREAMS.md": deferred_md,
        "DREAMS_QUARANTINE.md": quarantine_md,
        "DREAMS_ARCHIVE.md": archive_md,
    }


def _append_blocks(path: str, frags: list[Fragment], now: _dt.datetime) -> str:
    from . import store, parser
    header = "# SURFACE.md\n\nThe morning transfer layer. Surfaced fragments, ranked.\n\n## Surfaced fragments\n\n"
    existing = store.read_text(path) if __import__("os").path.exists(path) else ""
    head, _, rest = existing.partition("## Surfaced fragments")
    if not head.strip():
        head = header
    elif "## Surfaced fragments" not in existing:
        head = existing + "\n## Surfaced fragments\n"
    lines = []
    for f in frags:
        fm = dict(f.fm)
        fm["status"] = "surfaced"
        fm["surfaced_at"] = now.isoformat(timespec="seconds")
        fm["scores"] = f.scores
        # No automatic counterdream yet (v2). Mark as pending.
        if "counterdream" not in fm:
            fm["counterdream"] = "PENDING"
        lines.append(serialize_block(fm, f.body))
    sep = "" if not rest.strip() else "\n"
    return head + "## Surfaced fragments\n\n" + sep.join(lines) + "\n"


def _deferred_dreams(frags: list[Fragment], now: _dt.datetime) -> str:
    header = ("# DREAMS.md\n\nThe night's processing layer. Read and cleared each "
              "morning.\n\n## Fragments\n\n")
    lines = []
    for f in frags:
        fm = dict(f.fm)
        fm["status"] = "deferred"
        fm["review_after"] = (now + _dt.timedelta(days=2)).strftime("%Y-%m-%d")
        lines.append(serialize_block(fm, f.body))
    return header + "\n".join(lines) + "\n"


def _invalid_blocks(frags: list[Fragment]) -> str:
    header = "# DREAMS_QUARANTINE.md\n\nFragments excluded from surfacing due to malformed or invalid metadata. Not scored, not erased.\n\n## Quarantined\n\n"
    lines = []
    for f in frags:
        body = f.body or "(no body)"
        note = f.error or "invalid"
        lines.append(f"<!-- error: {note} -->\n```\n{f.raw_fm}\n---\n{body}\n```\n")
    return header + "\n".join(lines) + "\n"


def _tombstones(frags: list[Fragment], now: _dt.datetime) -> str:
    from . import store
    header = "# DREAMS_ARCHIVE.md\n\nMinimal tombstones for dismissed or superseded fragments.\n\n## Tombstones\n\n"
    lines = []
    for f in frags:
        h = f.content_hash or content_hash(f.body)
        fm = {
            "id": f.id or "unknown",
            "dismissed_at": now.strftime("%Y-%m-%d"),
            "reason": "deferred_then_exhausted",
            "content_hash": h,
        }
        lines.append(serialize_block(fm, f.body[:120]))
    return header + "\n".join(lines) + "\n"
