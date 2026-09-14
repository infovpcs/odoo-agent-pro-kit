#!/usr/bin/env bash
#
# Install (or remove) the odoo-agent-pro-kit agent preset for the DeepSeek
# Harness (DSH).
#
# The preset is copied into the harness home's user preset root, which is the
# only root DSH treats as yours to author:
#
#   ${DSH_HOME:-$HOME/.dsh}/.agent-presets/odoo-agent-pro-kit/
#
# DSH discovers presets from the filesystem on every roster read, so a new
# preset appears without restarting the harness.
#
# Usage:
#   ./install.sh              install or refresh the preset
#   ./install.sh --uninstall  remove it
#   ./install.sh --dry-run    print what would happen, change nothing
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SOURCE_DIR="$SCRIPT_DIR/preset"

PRESET_ID="odoo-agent-pro-kit"
DSH_HOME_DIR="${DSH_HOME:-$HOME/.dsh}"
PRESET_ROOT="$DSH_HOME_DIR/.agent-presets"
TARGET_DIR="$PRESET_ROOT/$PRESET_ID"

MODE="install"
for arg in "$@"; do
  case "$arg" in
    --uninstall) MODE="uninstall" ;;
    --dry-run) MODE="dry-run" ;;
    -h|--help)
      sed -n '2,20p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    *)
      echo "unknown argument: $arg" >&2
      exit 2
      ;;
  esac
done

say() { printf '%s\n' "$*"; }

if [ ! -f "$SOURCE_DIR/agent.cordis.yml" ] || [ ! -f "$SOURCE_DIR/odoo-kit.mjs" ]; then
  echo "FAIL: preset sources missing under $SOURCE_DIR" >&2
  exit 1
fi

if [ "$MODE" = "uninstall" ]; then
  if [ ! -d "$TARGET_DIR" ]; then
    say "Nothing to remove: $TARGET_DIR does not exist."
    exit 0
  fi
  say "Removing $TARGET_DIR"
  rm -rf "$TARGET_DIR"
  say "Done. Sessions that already selected this preset keep their composed agent until restarted."
  exit 0
fi

if [ "$MODE" = "dry-run" ]; then
  say "Would install preset '$PRESET_ID':"
  say "  from: $SOURCE_DIR"
  say "  to:   $TARGET_DIR"
  say "  kit root recorded in: $TARGET_DIR/kit-root.txt -> $REPO_ROOT"
  exit 0
fi

mkdir -p "$TARGET_DIR"

# Copy only what the preset needs. `kit-root.txt` is written fresh so a moved
# checkout is picked up by re-running this script.
for file in agent.cordis.yml preset.yml odoo-kit.mjs; do
  cp "$SOURCE_DIR/$file" "$TARGET_DIR/$file"
done
printf '%s\n' "$REPO_ROOT" > "$TARGET_DIR/kit-root.txt"

say "Installed preset '$PRESET_ID'"
say "  preset root : $TARGET_DIR"
say "  kit root    : $REPO_ROOT"

# Report which knowledge bundles were found, so a missing checkout is obvious
# before the first session rather than at the first odoo_kb_* call.
say ""
say "Odoo documentation knowledge bases:"
for short in 17 18 19; do
  bundle="$HOME/odoo-workspaces/knowledge-$short/odoo$short-okf"
  if [ -d "$bundle" ]; then
    say "  $short.0: $bundle"
  else
    say "  $short.0: not found (odoo_kb_* tools for this version will be unavailable)"
  fi
done

say ""
say "Next steps:"
say "  1. Start a DSH session and pick the '$PRESET_ID' preset."
say "  2. Confirm the Odoo tools, skills, and the five lifecycle commands are listed."
say "  3. Optional — point the odoo_* discovery tools at a database by exporting"
say "     ODOO19_URL / ODOO19_DB_NAME / ODOO19_DB_USER / ODOO19_DB_PASSWORD"
say "     (or the ODOO_* names, or ODOO17_*/ODOO18_* for those versions)."
say ""
say "See $SCRIPT_DIR/INSTALL.md for the full verification walkthrough."
