"""Morning surfacing report."""
from __future__ import annotations

from .schema import Fragment


def morning_summary(res: dict, budget: int) -> str:
    surf = res["surfaced"]
    if not surf:
        return "Morning Surfacing: no fragments met the surfacing budget."
    ranked = sorted(surf, key=lambda f: f.scores["total_weight"], reverse=True)
    top = ranked[0]
    lines = [
        f"Morning Surfacing — {len(surf)} surfaced (budget {budget})",
        f"Highest weight: {top.id} W={top.scores['total_weight']} "
        f"[{top.fm.get('type')}]",
    ]
    for f in ranked:
        lines.append(f"  • {f.id}  W={f.scores['total_weight']}  {_type(f)}")
    if res["deferred"]:
        lines.append(f"Deferred: {len(res['deferred'])}")
    if res["invalid"]:
        lines.append(f"Quarantined (invalid): {len(res['invalid'])}")
    return "\n".join(lines)


def _type(f: Fragment) -> str:
    return str(f.fm.get("type", "?"))
