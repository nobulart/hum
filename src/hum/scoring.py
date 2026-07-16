"""Evidence-derived scoring. Unknown signals are ZERO, not a positive default.

This is the core fix for v0.1's "every dream survives" defect: a plain one-line
fragment with no observed signal scores near the floor and will not surface under a
budget. Only *observed* recurrence, consequence, evidence, user signal, or active
relevance contribute weight.
"""
from __future__ import annotations

import math

BASE = 0.25                 # existence is weakly significant; everything else is earned
ALPHA = 0.15               # recurrence growth rate in ALPHA*log(1+r)
HIGH_CONSEQUENCE = {"WARNING", "CONTRADICTION"}
REFERENCE = 1.6            # normalisation divisor for ranking/display


def score(frag, prior_recurrence: int) -> dict:
    fm = frag.fm
    r = max(1, int(fm.get("recurrence_count", 1) or 1))

    # recurrence only when observed more than once
    recurrence_score = ALPHA * math.log(1 + r) if r > 1 else 0.0

    # novelty / utility: zero unless explicitly provided (observed)
    novelty = float(fm.get("novelty", 0.0) or 0.0)
    utility = float(fm.get("utility", 0.0) or 0.0)

    # active-work connection: zero unless explicitly flagged
    active = 0.30 if str(fm.get("active", "")).lower() in ("true", "1", "yes") else 0.0

    # consequence: zero unless high-consequence type or explicitly provided
    consequence = 0.0
    if str(fm.get("type", "")).upper() in HIGH_CONSEQUENCE:
        consequence = 0.50
    consequence = max(consequence, float(fm.get("consequence", 0.0) or 0.0))

    # predictive / user signal: zero unless evidence present or user-endorsed
    evidence = fm.get("evidence") or []
    predictive = 0.40 if evidence else 0.0
    trust = str((fm.get("source", {}) or {}).get("trust_level", "")).lower()
    if trust == "user_signal":
        predictive = max(predictive, 0.50)

    # decay: 0 at first surface (age ~0); set by lifecycle for deferred re-surfaces
    decay = float(fm.get("age_decay", 0.0) or 0.0)

    cp = float(fm.get("contradiction_penalty", 0.0) or 0.0)
    pp = 0.30 if trust == "external_untrusted" else 0.0

    raw = (BASE + recurrence_score + novelty + utility + active + consequence
           + predictive - decay - cp - pp)
    total = max(0.0, min(1.0, raw / REFERENCE))

    return {
        "base_significance": BASE,
        "recurrence": round(recurrence_score, 3),
        "novelty": round(novelty, 3),
        "utility": round(utility, 3),
        "active_work_connection": round(active, 3),
        "consequence": round(consequence, 3),
        "predictive_or_user": round(predictive, 3),
        "age_decay": round(decay, 3),
        "contradiction_penalty": round(cp, 3),
        "provenance_penalty": round(pp, 3),
        "total_weight": round(total, 3),
    }
