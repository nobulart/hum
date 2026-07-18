#!/usr/bin/env bash
#
# bootstrap.sh — bring up a fresh Hermes harness for the HUM subsystem.
#
# Non-destructive and idempotent:
#   1. Lays down the HUM file structure from ../templates (only if missing).
#   2. Links the dreams-capture skill into ~/.hermes/skills (if missing).
#   3. Verifies the Hermes config has the ollama-local provider.
#   4. Prints the exact commands to recreate the cron jobs (cannot be done
#      from a plain shell without the Hermes CLI — these are printed, not run).
#
# Usage:
#   bash hermes/bootstrap.sh [HUM_DIR]
#   (HUM_DIR defaults to the parent of this script's directory.)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HUM_DIR="${1:-$(cd "$SCRIPT_DIR/.." && pwd)}"

echo "== HUM bootstrap =="
echo "HUM_DIR = $HUM_DIR"
echo

# --- 1. HUM file layout from templates -------------------------------------
echo "[1/4] HUM file layout (from templates/)"
for f in DREAMS.md SURFACE.md DREAMS_DAY.md SUBCONSCIOUS.md DREAMS_ARCHIVE.md DREAMS_QUARANTINE.md; do
  if [ -f "$HUM_DIR/$f" ]; then
    echo "  exists : $f"
  elif [ -f "$HUM_DIR/templates/$f" ]; then
    cp "$HUM_DIR/templates/$f" "$HUM_DIR/$f"
    echo "  created: $f"
  else
    echo "  WARN   : $f missing and no template found"
  fi
done
echo

# --- 2. Link dreams-capture skill -------------------------------------------
echo "[2/4] dreams-capture skill"
SRC="$HUM_DIR/skills/dreams-capture"
DST="$HOME/.hermes/skills/dreams-capture"
if [ ! -d "$SRC" ]; then
  echo "  WARN   : source skill not found at $SRC"
elif [ -e "$DST" ]; then
  echo "  exists : $DST"
else
  ln -s "$SRC" "$DST"
  echo "  linked : $DST -> $SRC"
fi
echo

# --- 3. Verify Hermes provider config ---------------------------------------
echo "[3/4] Hermes provider check"
CFG="$HOME/.hermes/config.yaml"
if [ ! -f "$CFG" ]; then
  echo "  WARN   : $CFG not found — install Hermes first"
elif grep -q 'ollama-local' "$CFG"; then
  echo "  ok     : ollama-local provider present"
else
  echo "  WARN   : ollama-local provider MISSING from $CFG"
fi
echo

# --- 4. Print cron setup (manual step) --------------------------------------
echo "[4/4] Cron jobs to create (run these via the Hermes CLI / cronjob tool)"
echo
echo "  # DREAMS morning surfacing (daily 07:00) — CRITICAL"
echo "  cronjob create --schedule '0 7 * * *' \\"
echo "    --prompt 'Run the DREAMS morning surfacing for the local HUM install. Execute: python3 $HUM_DIR/scripts/surface.py --dreams-dir $HUM_DIR then read SURFACE.md and confirm DREAMS.md was reset. Deliver a brief summary under 10 lines.'"
echo
echo "  # daily skill sync (daily 08:00)"
echo "  cronjob create --schedule '0 8 * * *' \\"
echo "    --prompt 'Execute: $HOME/workspace/tools/daily_skills_sync.sh and report what was synced.'"
echo
echo "  # workspace monitor (every 1m)"
echo "  cronjob create --schedule 'every 1m' \\"
echo "    --prompt 'Check ~/workspace for changes; return [SILENT] if none.'"
echo
echo "  # OPTIONAL — dashboard monitor (every 15m, paused by default)"
echo "  # OPTIONAL — plato email checker (BROKEN: daily_email_checker.sh missing; do not enable)"
echo
echo "== done =="
echo "Next: run one manual surfacing pass to confirm the engine works:"
echo "  python3 $HUM_DIR/scripts/surface.py --dreams-dir $HUM_DIR"
