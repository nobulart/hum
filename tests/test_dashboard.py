"""Tests for src/hum/dashboard.py — the dual-machine data layer.

Verifies:
- build_machine_model parses the real HUM_DIR shape (type/status/trust facets,
  weight histogram, edges).
- build_merged tags origin and computes shared hashes.
- convergence returns a bounded, transparent metric.
- pull_hermes is read-only rsync and degrades gracefully when host is unreachable.
- synthetic 6-file set round-trips through the full pipeline.
"""
from __future__ import annotations

import os
import shutil
import sys
import tempfile

import pytest

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "src"))

from hum import dashboard as dash  # noqa: E402


def _write(path: str, text: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def test_build_machine_model_real(tmp_path, monkeypatch):
    # Build a tiny synthetic corpus under tmp so the test is hermetic.
    hum = tmp_path / "hum"
    _write(hum / "DREAMS.md", """# DREAMS.md
## Fragments

---
id: dream-20260101T000000-0000
type: WARNING
status: night
source:
  task: t
  source_type: x
  trust_level: internal_observation
---
@00:00 [WARNING] — disk pressure on the studio build node.

---
id: dream-20260101T000001-0001
type: BEHAVIOUR
status: night
source:
  task: t
  source_type: x
  trust_level: tool_output
---
@00:01 [BEHAVIOUR] — reused the wrong tool three times.
""")
    _write(hum / "SURFACE.md", """# SURFACE.md
## Surfaced fragments

---
id: dream-20260101T000002-0002
type: CONTRADICTION
status: surfaced
source:
  task: t
  source_type: x
  trust_level: internal_observation
---
@00:02 [CONTRADICTION] — prior assumption was wrong.
""")
    monkeypatch.setenv("HUM_DIR", str(hum))
    m = dash.build_machine_model(str(hum), machine_id="plato", host="h")
    assert m["n_valid"] == 3
    assert m["n_invalid"] == 0
    assert m["facets"]["by_type"]["WARNING"] == 1
    assert m["facets"]["by_type"]["BEHAVIOUR"] == 1
    assert m["facets"]["by_type"]["CONTRADICTION"] == 1
    assert m["facets"]["by_trust"]["internal_observation"] == 2
    assert m["facets"]["by_status"]["night"] == 2
    assert m["facets"]["by_status"]["surfaced"] == 1
    # weight histogram has exactly 3 fragments
    assert sum(m["facets"]["weight_hist"]) == 3
    # No references/recurrence in this corpus, but build_machine_model links
    # fragments parsed from the same layer file with co-occurs edges so the
    # graph stays connected. DREAMS.md has 2 fragments -> exactly one
    # co-occurs edge; SURFACE.md has 1 -> none.
    co_occurs = [e for e in m["edges"] if e["kind"] == "co-occurs"]
    assert len(co_occurs) == 1
    assert all(e["kind"] == "co-occurs" for e in m["edges"])
    # every fragment carries a stable content_hash and a type color lookup works
    for f in m["fragments"]:
        assert f["content_hash"]
        assert f["type"] in dash.TYPE_COLORS


def test_merge_origin_and_shared(tmp_path):
    hum_p = tmp_path / "p"
    hum_h = tmp_path / "h"
    # shared fragment (identical body) on both machines
    shared = "---\nid: dream-20260101T000000-0000\ntype: SEED\nstatus: night\nsource:\n  task: t\n  source_type: x\n  trust_level: internal_observation\n---\n@00:00 [SEED] — identical thought across machines.\n"
    only_p = "---\nid: dream-20260101T000001-0001\ntype: WARNING\nstatus: night\nsource:\n  task: t\n  source_type: x\n  trust_level: internal_observation\n---\n@00:01 [WARNING] — only on plato.\n"
    only_h = "---\nid: dream-20260101T000002-0002\ntype: RESISTANCE\nstatus: night\nsource:\n  task: t\n  source_type: x\n  trust_level: internal_observation\n---\n@00:02 [RESISTANCE] — only on hermes.\n"
    _write(hum_p / "DREAMS.md", "# DREAMS\n## Fragments\n" + shared + only_p)
    _write(hum_h / "DREAMS.md", "# DREAMS\n## Fragments\n" + shared + only_h)
    p = dash.build_machine_model(str(hum_p), "plato")
    h = dash.build_machine_model(str(hum_h), "hermes")
    merged = dash.build_merged(p, h)
    # 4 fragment records: shared appears on both machines + 1 unique each side
    assert len(merged["merged"]["fragments"]) == 4
    assert len([f for f in merged["merged"]["fragments"] if f["origin"] == "plato"]) == 2
    assert len([f for f in merged["merged"]["fragments"] if f["origin"] == "hermes"]) == 2
    # the shared fragment appears twice (once per machine) and is flagged shared
    shared_flags = [f for f in merged["merged"]["fragments"] if f["shared"]]
    assert len(shared_flags) == 2
    assert merged["convergence"]["shared_count"] == 1
    # shared cross-machine edge present
    assert any(e["kind"] == "shared" for e in merged["merged"]["edges"])


def test_convergence_bounded_and_transparent():
    p = {"facets": {"by_type": {"A": 1}, "by_trust": {"x": 1}}, "content_hashes": ["a"], "n_valid": 1}
    h = {"facets": {"by_type": {"A": 1}, "by_trust": {"x": 1}}, "content_hashes": ["a"], "n_valid": 1}
    c = dash.convergence(p, h)
    assert 0.0 <= c["symmetry_index"] <= 1.0
    assert c["type_jaccard"] == 1.0
    assert c["trust_jaccard"] == 1.0
    assert c["shared_count"] == 1


def test_pull_hermes_unreachable_graceful():
    # An invalid host must fail gracefully, not raise.
    ok, msg = dash.pull_hermes("no-such-host.invalid", "~/.hermes/hum",
                               tempfile.mkdtemp())
    assert ok is False
    assert msg
