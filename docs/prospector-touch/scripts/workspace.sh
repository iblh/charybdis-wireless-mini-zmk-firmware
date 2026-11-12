#!/usr/bin/env bash
# Source this file; locates the shared workspace from the canonical tracked docs folder.
prospector_workspace() {
  local current
  current="$(cd "$1" && pwd -P)"
  while [ "$current" != / ]; do
    if [ -f "$current/config/west.yml" ] && [ -d "$current/boards/shields/charybdis_dongle" ]; then
      dirname "$current"
      return
    fi
    if [ -d "$current/firmware" ] && [ -d "$current/module" ]; then
      echo "$current"
      return
    fi
    current="$(dirname "$current")"
  done
  echo 'Cannot locate the workspace; pass its absolute path as the first argument.' >&2
  return 1
}
