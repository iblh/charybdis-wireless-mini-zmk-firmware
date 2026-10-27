#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
source "$HERE/scripts/workspace.sh"
WORKSPACE="${1:-$(prospector_workspace "$HERE")}"
mkdir -p "$WORKSPACE"
WORKSPACE="$(cd "$WORKSPACE" && pwd)"
for spec in 'firmware|https://github.com/iblh/charybdis-wireless-mini-zmk-firmware.git' 'module|https://github.com/iblh/prospector-zmk-module.git'; do
  dest="${spec%%|*}"; url="${spec#*|}"
  if [ -e "$WORKSPACE/$dest" ]; then
    echo "SKIP: $WORKSPACE/$dest already exists; will not overwrite or reset"
  else
    echo "Cloning $url (feat/touch-no-sensor) -> $WORKSPACE/$dest"
    git clone --branch feat/touch-no-sensor --single-branch "$url" "$WORKSPACE/$dest"
  fi
done
if [ ! -e "$WORKSPACE/AGENTS.md" ]; then
  cp "$HERE/AGENTS.md" "$WORKSPACE/AGENTS.md"
  echo "Installed AGENTS.md to $WORKSPACE"
else
  echo 'Existing AGENTS.md preserved; review and merge instructions if desired.'
fi
bash "$HERE/scripts/verify-workspace.sh" "$WORKSPACE"
