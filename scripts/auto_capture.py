#!/usr/bin/env python3
"""auto_capture.py — discover idle Hermes sessions and extract a condensed
transcript for DREAMS fragment auto-capture.

Part of the HUM/DREAMS subsystem. Invoked by the hourly auto-capture cron job.
This helper is the deterministic, LLM-free half of the pipeline; it:

  1. --discover : query ~/.hermes/state.db and return JSON of sessions that are
                  idle >= IDLE_MIN, have >= MIN_TOOLS tool calls, are not from
                  excluded sources (default: cron/subagent), and have NEW
                  activity since their last capture (per-session watermark in
                  HUM_DIR/auto_capture_state.json).
  2. --extract  : dump a bounded, condensed transcript (user prompts + assistant
                  text + tool names/result tails) for one session so the cron
                  agent can distill fragment-worthy signals.
  3. --commit   : advance the per-session watermark so a session is not
                  reprocessed until NEW activity arrives.
  4. --seed-history : write a watermark for EVERY existing session at the current
                  moment. Run this ONCE at install so the cron never backfills
                  the entire (possibly huge) session history on its first run.
                  After seeding, only sessions with activity AFTER seeding
                  qualify. Resumed old sessions re-qualify via new activity.

Idempotency / history model:
  A session qualifies for capture only when its last-message timestamp EXCEEDS
  its stored watermark. On install, --seed-history sets every session's
  watermark to its current last-message time, so all history is excluded. When
  the cron captures a session it --commit s the watermark to that session's
  last-message time. If the user later resumes a captured session, new messages
  push last_msg past the watermark and the session qualifies again (a fresh
  activity burst earns fresh fragments). A session that simply stays idle is
  never re-captured.

Machine scope:
  This script reads THIS machine's ~/.hermes/state.db only. On a two-instance
  setup (Plato/MacBook + Hermes/Studio) each machine keeps its own sessions;
  deploy this script + a companion cron on the peer to cover its sessions.
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import datetime as _dt

STATE_DB = os.path.expanduser("~/.hermes/state.db")
HUM_DIR = os.path.expanduser("~/.hermes/hum")
WATERMARK = os.path.join(HUM_DIR, "auto_capture_state.json")

DEFAULT_EXCLUDE = ("cron", "subagent")
# Epoch seed (1970) used as "never captured" sentinel for brand-new sessions.
_NEVER = 0.0


def _now() -> _dt.datetime:
    return _dt.datetime.now().astimezone()


def _epoch_to_dt(ep) -> _dt.datetime:
    return _dt.datetime.fromtimestamp(float(ep), _dt.timezone.utc).astimezone()


def load_watermarks() -> dict:
    if os.path.exists(WATERMARK):
        try:
            with open(WATERMARK, encoding="utf-8") as fh:
                return json.load(fh)
        except Exception:
            return {}
    return {}


def save_watermarks(wm: dict) -> None:
    os.makedirs(HUM_DIR, exist_ok=True)
    tmp = WATERMARK + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(wm, fh, indent=2)
    os.replace(tmp, WATERMARK)


def _all_sessions_last_msg() -> dict[str, float]:
    """session_id -> last message epoch timestamp."""
    if not os.path.exists(STATE_DB):
        return {}
    con = sqlite3.connect(STATE_DB)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute(
        "SELECT s.id AS id, MAX(m.timestamp) AS last_msg "
        "FROM sessions s LEFT JOIN messages m ON m.session_id = s.id "
        "GROUP BY s.id"
    )
    out = {r["id"]: r["last_msg"] for r in cur.fetchall() if r["last_msg"] is not None}
    con.close()
    return out


def discover(idle_min: float = 60.0, min_tools: int = 5,
             exclude_sources=DEFAULT_EXCLUDE, profile: str | None = None) -> list[dict]:
    if not os.path.exists(STATE_DB):
        return []
    now = _now()
    con = sqlite3.connect(STATE_DB)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute(
        "SELECT s.id, s.source, s.profile_name, s.title, s.message_count, "
        "s.tool_call_count, MAX(m.timestamp) AS last_msg "
        "FROM sessions s LEFT JOIN messages m ON m.session_id = s.id "
        "WHERE s.source IS NOT NULL GROUP BY s.id"
    )
    rows = cur.fetchall()
    con.close()

    wm = load_watermarks()
    out: list[dict] = []
    for r in rows:
        src = r["source"]
        if src in exclude_sources:
            continue
        if profile is not None and r["profile_name"] != profile:
            continue
        last = r["last_msg"]
        if last is None:
            continue
        idle = (now - _epoch_to_dt(last)).total_seconds() / 60.0
        if idle < idle_min:
            continue
        tools = r["tool_call_count"] or 0
        if tools < min_tools:
            continue
        w = wm.get(r["id"])
        # Qualify only if there is NEW activity since last capture.
        # New sessions have no watermark (treated as _NEVER) and qualify.
        wm_ts = float(w.get("last_msg_ts", _NEVER)) if w else _NEVER
        if wm_ts >= float(last):
            continue
        out.append({
            "id": r["id"],
            "source": src,
            "title": r["title"],
            "message_count": r["message_count"],
            "tool_call_count": tools,
            "last_msg_ts": last,
            "last_msg_iso": _epoch_to_dt(last).isoformat(timespec="seconds"),
            "idle_min": round(idle, 1),
            "watermark_ts": wm_ts,
        })
    out.sort(key=lambda x: x["last_msg_ts"])
    return out


def extract(session_id: str, max_chars: int = 12000) -> str:
    if not os.path.exists(STATE_DB):
        return ""
    con = sqlite3.connect(STATE_DB)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute(
        "SELECT role, content, tool_name, timestamp FROM messages "
        "WHERE session_id = ? ORDER BY timestamp ASC",
        (session_id,),
    )
    parts: list[str] = []
    for r in cur.fetchall():
        role = r["role"]
        content = (r["content"] or "").strip()
        if role == "user":
            if content:
                parts.append(f"[USER {_epoch_to_dt(r['timestamp']).strftime('%H:%M')}] {content[:1500]}")
        elif role == "assistant":
            if content and len(content) > 40:
                parts.append(f"[ASSISTANT] {content[:800]}")
        elif role == "tool":
            tn = r["tool_name"] or "tool"
            if content:
                parts.append(f"[TOOL:{tn}] …{content[-400:]}")
    con.close()
    text = "\n\n".join(parts)
    if len(text) > max_chars:
        text = "...[earlier context truncated]...\n\n" + text[-max_chars:]
    return text


def commit(session_id: str, last_msg_ts: float) -> dict:
    wm = load_watermarks()
    wm[session_id] = {
        "last_msg_ts": float(last_msg_ts),
        "captured_at": _now().isoformat(timespec="seconds"),
    }
    save_watermarks(wm)
    return wm[session_id]


def seed_history() -> int:
    """Write a watermark for every existing session equal to its current last
    message time. Returns the number of sessions seeded. Excludes nothing — the
    discover() source filter still applies at capture time."""
    last = _all_sessions_last_msg()
    wm = load_watermarks()
    stamped = _now().isoformat(timespec="seconds")
    n = 0
    for sid, ts in last.items():
        if wm.get(sid, {}).get("last_msg_ts") is None:
            wm[sid] = {"last_msg_ts": float(ts), "captured_at": None,
                       "seeded_at": stamped}
            n += 1
    save_watermarks(wm)
    return n


def main() -> None:
    ap = argparse.ArgumentParser(description="HUM DREAMS auto-capture helper.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("discover", help="List idle, uncaptured candidate sessions (JSON).")
    d.add_argument("--idle-min", type=float, default=60.0)
    d.add_argument("--min-tools", type=int, default=5)
    d.add_argument("--exclude-sources", default=",".join(DEFAULT_EXCLUDE),
                   help="Comma-separated sources to skip (default: cron,subagent).")
    d.add_argument("--profile", default=None, help="Restrict to a Hermes profile.")

    e = sub.add_parser("extract", help="Dump a bounded transcript for one session.")
    e.add_argument("session_id")
    e.add_argument("--max-chars", type=int, default=12000)

    c = sub.add_parser("commit", help="Advance watermark for a session.")
    c.add_argument("session_id")
    c.add_argument("last_msg_ts", type=float)

    s = sub.add_parser("seed-history",
                       help="Watermark ALL existing sessions so the cron skips history.")

    args = ap.parse_args()
    if args.cmd == "discover":
        excl = tuple(s.strip() for s in args.exclude_sources.split(",") if s.strip()) \
            or DEFAULT_EXCLUDE
        cands = discover(idle_min=args.idle_min, min_tools=args.min_tools,
                         exclude_sources=excl, profile=args.profile)
        print(json.dumps(cands, indent=2))
    elif args.cmd == "extract":
        print(extract(args.session_id, max_chars=args.max_chars))
    elif args.cmd == "commit":
        print(json.dumps(commit(args.session_id, args.last_msg_ts), indent=2))
    elif args.cmd == "seed-history":
        n = seed_history()
        print(json.dumps({"seeded": n, "watermark": WATERMARK}, indent=2))


if __name__ == "__main__":
    main()
