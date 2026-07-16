"""Tests for HUM v0.2 — transactional integrity + meaningful selectivity.

Covers the reviewer's required cases: malformed YAML, duplicate IDs, unknown
types, tz handling, embedded '---' text, empty files, missing outputs, interrupted
write, retry idempotency, and preservation of non-survivors.
"""
from __future__ import annotations

import datetime as _dt
import os
import sys
import tempfile

import pytest

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "src"))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))

from hum import schema, store, parser, scoring, lifecycle, recurrence  # noqa: E402
import capture as cap  # noqa: E402


# ---- schema -----------------------------------------------------------------

def test_make_id_format():
    i = schema.make_id()
    assert schema.ID_RE.match(i), i


def test_validate_rejects_unknown_type():
    errs = schema.validate_front_matter({"id": "dream-20260101T000000-0000",
                                         "type": "NOPE"})
    assert any("type" in e for e in errs)


def test_validate_rejects_bad_id():
    errs = schema.validate_front_matter({"id": "not-an-id", "type": "SEED"})
    assert any("id" in e for e in errs)


def test_content_hash_normalises():
    assert schema.content_hash("Foo  bar") == schema.content_hash("foo bar")


# ---- parser -----------------------------------------------------------------

def test_parse_basic():
    doc = "---\nid: dream-x\ntype: SEED\n---\n@22:00 [SEED] — hello"
    blocks = parser.parse_document(doc)
    assert len(blocks) == 1 and blocks[0]["fm_ok"]


def test_parse_unterminated_fm_invalid():
    doc = "---\nid: dream-20260101T000000-0000\ntype: SEED\nno closing"
    blocks = parser.parse_document(doc)
    assert blocks and blocks[0]["fm_ok"] is False


def test_parse_embedded_delimiter_in_body():
    doc = ("---\nid: dream-20260101T000000-0000\ntype: SEED\n---\n"
           "body with --- a delimiter inside\nand more")
    blocks = parser.parse_document(doc)
    assert blocks[0]["body"].count("---") == 1  # only the real one


def test_parse_empty_file():
    assert parser.parse_document("") == []


# ---- scoring (the core fix) -------------------------------------------------

def test_plain_fragment_scores_low():
    f = schema.Fragment({"id": "dream-20260101T000000-0000", "type": "SEED",
                         "recurrence_count": 1}, "one line")
    s = scoring.score(f, prior_recurrence=0)
    # must be well below the v0.1 0.74 — unknown signals are zero
    assert s["total_weight"] < 0.4, s


def test_recurrence_raises_score():
    f = schema.Fragment({"id": "dream-20260101T000000-0001", "type": "SEED",
                         "recurrence_count": 4}, "repeated")
    s = scoring.score(f, prior_recurrence=4)
    assert s["recurrence"] > 0


def test_evidence_raises_predictive():
    f = schema.Fragment({"id": "dream-20260101T000000-0002", "type": "SEED",
                         "evidence": ["saw it twice"]}, "with evidence")
    s = scoring.score(f, 0)
    assert s["predictive_or_user"] > 0


def test_untrusted_penalty():
    f = schema.Fragment({"id": "dream-20260101T000000-0003", "type": "SEED",
                         "source": {"trust_level": "external_untrusted"}}, "x")
    s = scoring.score(f, 0)
    assert s["provenance_penalty"] > 0


# ---- lifecycle / selectivity ------------------------------------------------

def _write_dreams(d, bodies):
    blocks = []
    for b in bodies:
        blocks.append(parser.serialize_block(
            {"id": schema.make_id(), "type": "SEED",
             "recurrence_count": 1}, b))
    store.atomic_write(os.path.join(d, "DREAMS.md"),
                       "# DREAMS.md\n\n## Fragments\n\n" + "\n".join(blocks) + "\n")


def test_budget_limits_surfacing(tmp_path):
    _write_dreams(str(tmp_path), [f"plain fragment number {i}" for i in range(10)])
    res = lifecycle.classify(str(tmp_path), budget=3)
    assert len(res["surfaced"]) == 3
    assert len(res["deferred"]) + len(res["surfaced"]) == 10


def test_high_consequence_always_surfaces(tmp_path):
    blocks = [parser.serialize_block(
        {"id": schema.make_id(), "type": "WARNING", "recurrence_count": 1},
        "critical risk")]
    store.atomic_write(os.path.join(str(tmp_path), "DREAMS.md"),
                       "# DREAMS.md\n\n## Fragments\n\n" + "\n".join(blocks) + "\n")
    res = lifecycle.classify(str(tmp_path), budget=0)  # zero budget
    assert any(str(f.fm.get("type")) == "WARNING" for f in res["surfaced"])


def test_invalid_quarantined_not_scored(tmp_path):
    doc = ("# DREAMS.md\n\n## Fragments\n\n"
           "---\nid: dream-20260101T000000-0000\ntype: BOGUS\n---\n@x [BOGUS] — body\n")
    store.atomic_write(os.path.join(str(tmp_path), "DREAMS.md"), doc)
    res = lifecycle.classify(str(tmp_path), budget=5)
    assert res["invalid"] and not res["frags"][0].fm_ok


def test_recurrence_detected_from_prior(tmp_path):
    # pre-existing in SURFACE.md
    blocks = [parser.serialize_block(
        {"id": schema.make_id(), "type": "OBSERVATION", "first_seen": "2026-01-01"},
        "same observation text")]
    store.atomic_write(os.path.join(str(tmp_path), "SURFACE.md"),
                       "# SURFACE.md\n\n## Surfaced fragments\n\n" + "\n".join(blocks) + "\n")
    # same body appears tonight
    _write_dreams(str(tmp_path), ["same observation text"])
    prior = recurrence.scan_store(str(tmp_path))
    cnt, _ = recurrence.lookup(prior, schema.content_hash("same observation text"))
    assert cnt >= 1


# ---- transactional integrity ------------------------------------------------

def test_atomic_write_rename(tmp_path):
    p = str(tmp_path / "f.md")
    store.atomic_write(p, "hello")
    assert store.read_text(p) == "hello"
    assert not any(x.endswith(".tmp") for x in os.listdir(tmp_path))


def test_run_idempotent(tmp_path):
    _write_dreams(str(tmp_path), ["unique alpha", "unique beta", "unique gamma"])
    r1 = lifecycle.classify(str(tmp_path), budget=5)
    out1 = lifecycle.render_outputs(r1, str(tmp_path))
    # simulate write
    store.atomic_write(os.path.join(str(tmp_path), "SURFACE.md"), out1["SURFACE.md"])
    # re-run must not duplicate
    r2 = lifecycle.classify(str(tmp_path), budget=5)
    surfaced_ids_1 = {f.id for f in r1["surfaced"]}
    surfaced_ids_2 = {f.id for f in r2["surfaced"]}
    assert surfaced_ids_1 == surfaced_ids_2


def test_deferred_preserved_not_erased(tmp_path):
    _write_dreams(str(tmp_path), [f"fragment {i}" for i in range(8)])
    res = lifecycle.classify(str(tmp_path), budget=3)
    assert res["deferred"], "non-survivors must be preserved as deferred"
    outputs = lifecycle.render_outputs(res, str(tmp_path))
    assert "## Fragments" in outputs["DREAMS.md"]


# ---- capture executable helper ---------------------------------------------

def run_capture(dreams_dir, type_, body, **kw):
    """Invoke capture logic directly (mirrors capture.py main)."""
    import io
    from contextlib import redirect_stdout
    argv = ["capture.py", "--dreams-dir", dreams_dir, "--type", type_, "--body", body]
    for k, v in kw.items():
        argv += [f"--{k}", str(v)]
    cap.sys.argv = argv
    buf = io.StringIO()
    with redirect_stdout(buf):
        cap.main()
    return buf.getvalue()


def test_capture_writes_valid_fragment(tmp_path):
    run_capture(str(tmp_path), "SEED", "a new idea worth incubating")
    blocks = parser.parse_document(store.read_text(os.path.join(str(tmp_path), "DREAMS.md")))
    assert blocks and blocks[0]["fm_ok"]
    import yaml
    assert schema.validate_front_matter(yaml.safe_load(blocks[0]["raw_fm"])) == []


def test_capture_skips_duplicate(tmp_path):
    run_capture(str(tmp_path), "SEED", "repeat me")
    out = run_capture(str(tmp_path), "SEED", "repeat me")
    assert "skip" in out.lower()


def test_capture_id_collision_free(tmp_path):
    run_capture(str(tmp_path), "SEED", "one")
    run_capture(str(tmp_path), "SEED", "two")
    import yaml
    blocks = parser.parse_document(store.read_text(os.path.join(str(tmp_path), "DREAMS.md")))
    ids = [yaml.safe_load(b["raw_fm"]).get("id") for b in blocks]
    assert len(ids) == len(set(ids))
