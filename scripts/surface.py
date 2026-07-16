#!/usr/bin/env python3
"""
surface.py — DREAMS morning surfacing (v1 baseline).

Reads DREAMS.md, scores each fragment with the protocol's bounded W function,
promotes survivors (total_weight >= threshold) to SURFACE.md, and clears DREAMS.md.

This is the v1 scaffold shipped with the HUM skill-set. Scoring weights and the
surfacing threshold are EXPLICIT BASELINES, not validated constants — tune them
after the system has run a full manual cycle (see BUILD.md → Next build steps).

Dependencies: pyyaml  (pip install pyyaml)

Usage:
    python surface.py [--dreams-dir DIR] [--threshold 0.5] [--dry-run]

If --dreams-dir is omitted, operates on the current working directory.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import math
import os
import re
import sys

try:
    import yaml
except ImportError:
    sys.exit("pyyaml is required: pip install pyyaml")

# --- v1 baseline scoring constants (TUNable after first cycle) ---------------
ALPHA = 0.10            # recurrence growth rate in W = ... + alpha*log(1+r)
BASE_SIGNIFICANCE = 0.50
LONG_FORM_BONUS = 0.10  # added to base when body exceeds one line
DEFAULT_NOVELTY = 0.50
DEFAULT_UTILITY = 0.40
DEFAULT_ACTIVE = 0.30
DEFAULT_CONSEQUENCE = 0.30
WARNING_CONSEQUENCE = 0.50     # type WARNING / CONTRADICTION
DEFAULT_PREDICTIVE = 0.20
EVIDENCE_PREDICTIVE = 0.50     # when front-matter evidence is non-empty
DECAY = 0.05            # age_decay baseline
REFERENCE_MAX = 3.0     # normalisation divisor for the raw W sum
DEFAULT_THRESHOLD = 0.50

HIGH_CONSEQUENCE_TYPES = {"WARNING", "CONTRADICTION"}

FRAGMENT_RE = re.compile(
    r"^---\n(.*?)\n---\n(.*?)(?=^---|\Z)",
    re.DOTALL | re.MULTILINE,
)


def split_fragments(text: str):
    """Return list of (front_matter_dict, body_str) from a DREAMS.md document."""
    # Strip the leading header / non-front-matter preamble up to first '---' block.
    frags = []
    for m in FRAGMENT_RE.finditer(text):
        fm_raw, body = m.group(1), m.group(2)
        try:
            fm = yaml.safe_load(fm_raw) or {}
        except yaml.YAMLError:
            fm = {}
        if not isinstance(fm, dict):
            fm = {}
        frags.append((fm, body.strip()))
    return frags


def score_fragment(fm: dict, body: str) -> dict:
    """Compute the protocol's bounded W and return the full scores dict."""
    body_lines = [ln for ln in body.splitlines() if ln.strip()]
    base = BASE_SIGNIFICANCE + (LONG_FORM_BONUS if len(body_lines) > 1 else 0.0)

    r = int(fm.get("recurrence_count", 1) or 1)
    novelty = DEFAULT_NOVELTY
    utility = DEFAULT_UTILITY
    active = DEFAULT_ACTIVE
    ftype = str(fm.get("type", "")).upper()
    consequence = WARNING_CONSEQUENCE if ftype in HIGH_CONSEQUENCE_TYPES else DEFAULT_CONSEQUENCE
    evidence = fm.get("evidence") or []
    predictive = EVIDENCE_PREDICTIVE if evidence else DEFAULT_PREDICTIVE
    decay = DECAY
    contradiction_penalty = float(fm.get("contradiction_penalty", 0.0) or 0.0)
    provenance_penalty = float(fm.get("provenance_penalty", 0.0) or 0.0)

    w_raw = (
        base
        + ALPHA * math.log(1 + r)
        + novelty
        + utility
        + active
        + consequence
        + predictive
        - decay
        - contradiction_penalty
        - provenance_penalty
    )
    total_weight = max(0.0, min(1.0, w_raw / REFERENCE_MAX))

    return {
        "base_significance": round(base, 3),
        "recurrence": round(min(1.0, ALPHA * math.log(1 + r)), 3),
        "novelty": novelty,
        "utility": utility,
        "active_work_connection": active,
        "consequence": consequence,
        "predictive_or_user": predictive,
        "age_decay": decay,
        "contradiction_penalty": contradiction_penalty,
        "provenance_penalty": provenance_penalty,
        "total_weight": round(total_weight, 3),
    }


def surface(dreams_dir: str, threshold: float, dry_run: bool = False) -> dict:
    dreams_path = os.path.join(dreams_dir, "DREAMS.md")
    surface_path = os.path.join(dreams_dir, "SURFACE.md")
    if not os.path.exists(dreams_path):
        sys.exit(f"DREAMS.md not found in {dreams_dir}")

    with open(dreams_path, encoding="utf-8") as fh:
        text = fh.read()

    frags = split_fragments(text)
    if not frags:
        print("No fragments to surface.")
        return {"surfaced": 0, "total": 0}

    survivors = []
    for fm, body in frags:
        scores = score_fragment(fm, body)
        if scores["total_weight"] >= threshold:
            surfaced = dict(fm)
            surfaced["status"] = "surfaced"
            surfaced["surfaced_at"] = _dt.datetime.now().isoformat(timespec="seconds")
            surfaced["scores"] = scores
            surfaced["counterdream"] = None  # v2: auto-generate
            survivors.append((surfaced, body))

    report = {
        "total": len(frags),
        "surfaced": len(survivors),
        "threshold": threshold,
        "ids": [s[0].get("id", "?") for s in survivors],
    }

    if dry_run:
        print(f"[dry-run] {report['surfaced']}/{report['total']} fragments clear threshold {threshold}")
        for s, _ in survivors:
            print(f"  {s.get('id')}  W={s['scores']['total_weight']}")
        return report

    # Append survivors to SURFACE.md
    with open(surface_path, encoding="utf-8") as fh:
        existing = fh.read()
    header, _, rest = existing.partition("## Surfaced fragments")
    block_lines = [rest.strip(), ""] if rest.strip() else [""]
    for fm, body in survivors:
        fm_yaml = yaml.safe_dump(fm, sort_keys=False, allow_unicode=True).strip()
        block_lines.append(f"---\n{fm_yaml}\n---\n\n{body}\n")

    with open(surface_path, "w", encoding="utf-8") as fh:
        fh.write(f"{header}## Surfaced fragments\n\n" + "\n".join(block_lines) + "\n")

    # Reset DREAMS.md to header + empty Fragments section
    with open(dreams_path, "w", encoding="utf-8") as fh:
        fh.write(
            "# DREAMS.md\n\nThe night's processing layer. Read and cleared each morning.\n\n"
            "## Fragments\n"
        )

    print(f"Surfaced {report['surfaced']}/{report['total']} fragments to SURFACE.md; DREAMS.md reset.")
    return report


def main():
    ap = argparse.ArgumentParser(description="DREAMS morning surfacing (v1).")
    ap.add_argument("--dreams-dir", default=os.getcwd(),
                    help="Directory containing DREAMS.md / SURFACE.md (default: cwd)")
    ap.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD,
                    help=f"Surfacing threshold (default {DEFAULT_THRESHOLD})")
    ap.add_argument("--dry-run", action="store_true", help="Score but do not write")
    args = ap.parse_args()
    surface(args.dreams_dir, args.threshold, args.dry_run)


if __name__ == "__main__":
    main()
