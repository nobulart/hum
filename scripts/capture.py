#!/usr/bin/env python3
"""capture.py — DREAMS night fragment capture (v0.2, transactional).

Owns fragment creation end-to-end:
  id generation (dream-YYYYMMDDThhmmss-XXXX, collision-proof)
  timestamp + local timezone
  type validation
  source normalisation
  YAML serialization
  file locking + atomic append
  duplicate detection (by content hash)

Usage:
    python capture.py --type SEED --body "text" [--task NAME] [--active]
    python capture.py --type OBSERVATION --file note.md
"""
from __future__ import annotations

import argparse
import datetime as _dt
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from hum import schema, store, parser  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description="Capture a DREAMS night fragment.")
    ap.add_argument("--dreams-dir", default=os.getcwd(),
                    help="Directory with DREAMS.md (default: cwd)")
    ap.add_argument("--type", required=True,
                    choices=sorted(schema.VALID_TYPES),
                    help="Primary fragment type")
    ap.add_argument("--body", help="Fragment text (or use --file)")
    ap.add_argument("--file", help="Read body from a file")
    ap.add_argument("--task", default="interactive", help="Source task/session name")
    ap.add_argument("--trust", default="internal_observation",
                    choices=sorted({*schema.KNOWN_TRUST, *schema.UNTRUSTED_PENALTY_TRUST}),
                    help="Provenance / trust level")
    ap.add_argument("--active", action="store_true",
                    help="Flag active-work connection (raises scoring)")
    ap.add_argument("--evidence", action="append", default=[],
                    help="Evidence line (repeatable)")
    ap.add_argument("--dry-run", action="store_true", help="Validate but do not write")
    args = ap.parse_args()

    body = args.body
    if args.file:
        with open(args.file, encoding="utf-8") as fh:
            body = fh.read().strip()
    if not body:
        sys.exit("error: provide --body or --file")

    now = _dt.datetime.now().astimezone()
    fm = {
        "id": schema.make_id(now),
        "created_at": now.isoformat(timespec="seconds"),
        "type": args.type.upper(),
        "status": "night",
        "source": {
            "task": args.task,
            "source_type": "observed_behaviour" if args.type.upper() == "BEHAVIOUR"
                           else "reflective_observation",
            "trust_level": args.trust,
        },
    }
    if args.active:
        fm["active"] = True
    if args.evidence:
        fm["evidence"] = args.evidence

    errs = schema.validate_front_matter(fm)
    if errs:
        sys.exit("validation error: " + "; ".join(errs))

    # duplicate detection
    h = schema.content_hash(body)
    dpath = os.path.join(args.dreams_dir, "DREAMS.md")
    block = parser.serialize_block(fm, body)
    if os.path.exists(dpath):
        import yaml
        for b in parser.parse_document(store.read_text(dpath)):
            if b["fm_ok"]:
                try:
                    if schema.content_hash(b["body"]) == h:
                        print(f"[skip] duplicate of existing fragment "
                              f"(hash {h}); not appended")
                        return
                except Exception:
                    pass

    if args.dry_run:
        print("[dry-run] would append:\n" + block)
        return

    with store.FileLock(dpath):
        existing = store.read_text(dpath) if os.path.exists(dpath) else (
            "# DREAMS.md\n\nThe night's processing layer. Read and cleared each "
            "morning.\n\n## Fragments\n")
        head, _, rest = existing.partition("## Fragments")
        prefix = head if rest else existing
        new_text = prefix + "## Fragments\n\n" + block + (
            rest if rest else "")
        store.atomic_write(dpath, new_text)
    print(f"captured {fm['id']} ({args.type})")


if __name__ == "__main__":
    main()
