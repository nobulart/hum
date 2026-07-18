#!/usr/bin/env bash
#
# bootstrap.sh — bring up a Hermes harness for the HUM subsystem.
#
# Non-destructive and idempotent:
#   1. Builds the HUM_DIR install from the repo (rsync: code + templates + config),
#      NEVER clobbering existing runtime volatiles (DREAMS.md, SURFACE.md, etc.).
#   2. Links the dreams-capture skill into ~/.hermes/skills (if missing).
#   3. Verifies the Hermes config has the ollama-local provider.
#   4. Prints the exact commands to recreate the cron jobs (cannot be done
#      from a plain shell without the Hermes CLI — these are printed, not run).
#
# CRITICAL: HUM_DIR is the runtime home for PER-INSTALL volatiles. It MUST NOT
# be the git repo (doing so re-commits dream data). Default below is
# ~/.hermes/hum, which is correct and git-ignored by convention. If you pass the
# repo path as HUM_DIR, you will reintroduce the volatiles-in-repo bug.
#
# Usage:
#   bash hermes/bootstrap.sh [HUM_DIR]
#   (HUM_DIR defaults to ~/.hermes/hum)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
HUM_DIR="${1:-$HOME/.hermes/hum}"

# Guard against the volatiles-in-repo footgun.
if [ "$(cd "$HUM_DIR" && pwd)" = "$(cd "$REPO_DIR" && pwd)" ]; then
  echo "ERROR: HUM_DIR must not be the git repo ($REPO_DIR)." >&2
  echo "       Pass a separate path, e.g. ~/.hermes/hum" >&2
  exit 1
fi

echo "== HUM bootstrap =="
echo "REPO_DIR = $REPO_DIR"
echo "HUM_DIR  = $HUM_DIR"
echo

# --- 1. Build HUM_DIR install from repo (preserve existing volatiles) ------
echo "[1/4] Build HUM_DIR from repo (preserving runtime volatiles)"
mkdir -p "$HUM_DIR"

# Sync code/config/templates from repo. Use rsync if present so that existing
# runtime files (DREAMS*.md, SURFACE.md, etc.) are NOT overwritten by repo
# templates. `rsync -a` copies; the explicit excludes protect volatiles.
if command -v rsync >/dev/null 2>&1; then
  rsync -a \
    --exclude '.git' \
    --exclude 'hermes' \
    --exclude 'DREAMS.md' --exclude 'SURFACE.md' --exclude 'DREAMS_DAY.md' \
    --exclude 'SUBCONSCIOUS.md' --exclude 'DREAMS_ARCHIVE.md' \
    --exclude 'DREAMS_QUARANTINE.md' \
    "$REPO_DIR/" "$HUM_DIR/"
else
  # Fallback: cp tree minus volatiles (less robust — prefers rsync).
  cp -R "$REPO_DIR/src" "$REPO_DIR/scripts" "$REPO_DIR/templates" \
        "$REPO_DIR/config.yaml" "$REPO_DIR/README.md" "$REPO_DIR/BUILD.md" \
        "$REPO_DIR/DREAMS_PROTOCOL.md" "$REPO_DIR/LICENSE" "$REPO_DIR/requirements.txt" \
        "$REPO_DIR/docs" "$REPO_DIR/examples" "$REPO_DIR/skills" "$HUM_DIR/" 2>/dev/null || true
fi

# Ensure every runtime volatile file exists (seed from templates only if absent).
for f in DREAMS.md SURFACE.md DREAMS_DAY.md SUBCONSCIOUS.md DREAMS_ARCHIVE.md DREAMS_QUARANTINE.md; do
  if [ -f "$HUM_DIR/$f" ]; then
    echo "  exists : $f (preserved)"
  elif [ -f "$HUM_DIR/templates/$f" ]; then
    cp "$HUM_DIR/templates/$f" "$HUM_DIR/$f"
    echo "  created: $f (from template)"
  else
    echo "  WARN   : $f missing and no template found"
  fi
done
chmod 600 "$HUM_DIR"/*.md 2>/dev/null || true
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
echo "HUM_DIR is now: $HUM_DIR"
echo "Next: run one manual surfacing pass to confirm the engine works:"
echo "  python3 $HUM_DIR/scripts/surface.py --dreams-dir $HUM_DIR"
