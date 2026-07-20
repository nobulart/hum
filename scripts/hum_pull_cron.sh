#!/usr/bin/env bash
# hum_pull_cron.sh — refresh the Hermes (Mac Studio) HUM corpus cache that the
# local HUM dashboard serves under its "hermes" column.
#
# Runs as a watchdog cron: SILENT on success, prints + exits non-zero on
# failure (so the scheduler alerts). No LLM, no tokens.
#
# The HUM dashboard (dashboard/app.py, launched by the Hermes desktop app)
# owns the HERMES_* env wiring (HERMES_HOST=mac-studio.local,
# HERMES_CACHE_DIR=/tmp/hum-studio) and exposes a POST /api/pull route that
# performs a READ-ONLY rsync from Studio and rebuilds the in-memory model
# (plus an SSE push to any open UI). We delegate to that route rather than
# duplicating the rsync + env logic, so the cron stays in lockstep with the
# dashboard's configuration.
#
# Override the endpoint with HUM_PULL_URL if the bind/port ever changes.
set -uo pipefail

URL="${HUM_PULL_URL:-http://127.0.0.1:8650/api/pull}"

# Dashboard's do_pull() runs an rsync with a 30s subprocess timeout; give the
# client comfortably more headroom so a slow-but-healthy pull (Studio under
# load from heavy jobs) never trips the curl timeout and reports a false
# "unreachable".
resp=$(curl -sS -m 120 -X POST "$URL" 2>/dev/null) || true
if [ -z "$resp" ]; then
  echo "HUM Studio pull FAILED: dashboard unreachable at $URL (is the HUM dashboard running?)"
  exit 1
fi

if printf '%s' "$resp" | grep -q '"ok": *true'; then
  exit 0   # silent success — watchdog pattern
fi

msg=$(printf '%s' "$resp" | sed -n 's/.*"message": *"\([^"]*\)".*/\1/p')
echo "HUM Studio pull FAILED: ${msg:-unknown error (resp: ${resp:0:120})}"
exit 1
