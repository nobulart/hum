"""Fragment schema: types, id format, validation, content hashing."""
from __future__ import annotations

import hashlib
import re
import secrets
import datetime as _dt

VALID_TYPES = frozenset({
    "OBSERVATION", "BEHAVIOUR", "ASSOCIATION", "QUESTION",
    "CONTRADICTION", "RESISTANCE", "SEED", "WARNING",
})

VALID_STATUSES = frozenset({
    "night", "surfaced", "testing", "confirmed", "contradicted",
    "carried", "dormant", "dismissed", "escalated", "deferred",
    "forgotten", "invalid",
})

# trust levels we will score without penalty
KNOWN_TRUST = frozenset({
    "internal_observation", "user_signal", "tool_output", "document",
})

# untrusted external text is allowed but penalised, never auto-promoted
UNTRUSTED_PENALTY_TRUST = frozenset({"external_untrusted"})

ID_RE = re.compile(r"^dream-\d{8}T\d{6}-[0-9A-Z]{4}$")

# Crockford-ish base32, ambiguous chars removed (no I L O U)
_RND_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


def content_hash(body: str) -> str:
    """Stable hash of a fragment body, normalised for whitespace/case."""
    norm = re.sub(r"\s+", " ", body.strip().lower())
    return hashlib.sha1(norm.encode("utf-8")).hexdigest()[:12]


def _rand4() -> str:
    return "".join(secrets.choice(_RND_ALPHABET) for _ in range(4))


def make_id(ts: _dt.datetime | None = None) -> str:
    """Collision-proof id: dream-YYYYMMDDThhmmss-XXXX (local tz, random suffix).

    No shared sequential counter, so concurrent capturers cannot collide.
    """
    ts = ts or _dt.datetime.now().astimezone()
    return f"dream-{ts.strftime('%Y%m%dT%H%M%S')}-{_rand4()}"


def parse_id_time(idstr: str) -> _dt.datetime | None:
    m = re.match(r"^dream-(\d{8}T\d{6})-", idstr)
    if not m:
        return None
    try:
        return _dt.datetime.strptime(m.group(1), "%Y%m%dT%H%M%S")
    except Exception:
        return None


def validate_front_matter(fm: dict) -> list[str]:
    """Return a list of validation errors (empty == valid)."""
    errs: list[str] = []
    if not isinstance(fm, dict):
        return ["front matter is not a mapping"]
    t = fm.get("type")
    if t is None:
        errs.append("missing 'type'")
    elif str(t).upper() not in VALID_TYPES:
        errs.append(f"invalid type: {t!r}")
    fid = fm.get("id")
    if fid is None:
        errs.append("missing 'id'")
    elif not ID_RE.match(str(fid)):
        errs.append(f"id does not match schema: {fid!r}")
    st = fm.get("status")
    if st is not None and str(st).lower() not in VALID_STATUSES:
        errs.append(f"invalid status: {st!r}")
    prov = fm.get("provenance")
    if prov is None:
        prov = (fm.get("source", {}) or {}).get("trust_level")
    if prov is not None and str(prov).lower() not in (
        {p.lower() for p in KNOWN_TRUST} | {p.lower() for p in UNTRUSTED_PENALTY_TRUST}
    ):
        errs.append(f"unknown provenance/trust_level: {prov!r}")
    ca = fm.get("created_at")
    if ca is not None:
        try:
            _dt.datetime.fromisoformat(str(ca))
        except Exception:
            errs.append(f"unparseable created_at: {ca!r}")
    return errs


class Fragment:
    """A single DREAMS fragment in memory."""

    def __init__(self, fm: dict, body: str, raw_fm: str = "", fm_ok: bool = True,
                 error: str | None = None):
        self.fm = fm
        self.body = body
        self.raw_fm = raw_fm
        self.fm_ok = fm_ok
        self.error = error
        self.content_hash: str | None = None
        self.scores: dict | None = None
        self.outcome: str | None = None  # surfaced|deferred|forgotten|invalid
        self.deferred_count: int = 0

    @property
    def id(self) -> str:
        return str(self.fm.get("id", ""))

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Fragment {self.id} {self.outcome}>"
