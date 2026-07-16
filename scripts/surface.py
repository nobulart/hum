#!/usr/bin/env python3
"""surface.py — DREAMS morning surfacing (v0.2, transactional + selective).

Reads DREAMS.md, scores each fragment with EVIDENCE-DERIVED weights (unknown
signals are zero, not a positive default), classifies into four outcomes
(surfaced / deferred / forgotten / invalid), applies a daily BUDGET, and writes
all outputs atomically. Re-runs are idempotent via run_id + idempotent appends.

This implements the minimum claims associated with "surfacing" (dedup, prior-file
recurrence scan, ranked selection, quarantine). Counterdream auto-generation and
semantic recurrence are deferred to v2.

Usage:
    python surface.py [--dreams-dir DIR] [--budget N] [--dry-run]
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from hum import store, lifecycle, reports  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description="DREAMS morning surfacing (v0.2).")
    ap.add_argument("--dreams-dir", default=os.getcwd(),
                    help="Directory with DREAMS.md etc. (default: cwd)")
    ap.add_argument("--budget", type=int, default=5,
                    help="Max top fragments to surface per cycle (default 5); "
                         "high-consequence items always included")
    ap.add_argument("--dry-run", action="store_true",
                    help="Classify and print report, write nothing")
    args = ap.parse_args()

    dpath = os.path.join(args.dreams_dir, "DREAMS.md")
    if not os.path.exists(dpath):
        sys.exit(f"DREAMS.md not found in {args.dreams_dir}")

    rid = store.run_id()
    res = lifecycle.classify(args.dreams_dir, args.budget)

    if args.dry_run:
        print(f"[dry-run run_id={rid}]")
        print(reports.morning_summary(res, args.budget))
        return

    outputs = lifecycle.render_outputs(res, args.dreams_dir)
    with store.FileLock(dpath):
        # atomic: write every output, then the (possibly emptied) DREAMS.md last
        for fname, content in outputs.items():
            if fname == "DREAMS.md":
                continue
            if content.strip():
                store.atomic_write(os.path.join(args.dreams_dir, fname), content)
        # DREAMS.md is either deferred fragments or empty header
        dreams_content = outputs["DREAMS.md"]
        if not res["deferred"]:
            dreams_content = ("# DREAMS.md\n\nThe night's processing layer. Read and "
                              "cleared each morning.\n\n## Fragments\n")
        store.atomic_write(dpath, dreams_content)

    print(f"[run_id={rid}] " + reports.morning_summary(res, args.budget))


if __name__ == "__main__":
    main()
