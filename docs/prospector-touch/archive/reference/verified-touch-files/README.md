# Verified touch-file reference snapshots

These files are included for cross-checking/disaster recovery and are NOT intended to overwrite current local fork sources. The current firmware's config is the source of truth. `touch_settings.c` and overlay were extracted from original patch; matching branch content was checked at handoff. `dongle_prospector_touch.conf` includes the three LVGL9 config flags added after initial CI failure; it reflects the successful build on 2026-10-23.

If Git HEAD differs, inspect `git diff` and source provenance before taking any action.
