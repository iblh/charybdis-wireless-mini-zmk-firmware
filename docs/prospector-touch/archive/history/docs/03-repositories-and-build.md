# 03 — Git Repositories, Build, UF2 / 仓库与构建

## Two real forks and audited revisions (2026-10-23)

| Directory on Mac | Fork | Branch | Git SHA at handoff |
|---|---|---|---|
| `~/Workspace/Lab/prospector-pro/firmware` | https://github.com/iblh/charybdis-wireless-mini-zmk-firmware | feat/touch-no-sensor | `f4daf0be2b6f80fe41268e294e505ca79913f5cf` |
| `~/Workspace/Lab/prospector-pro/module` | https://github.com/iblh/prospector-zmk-module | feat/touch-no-sensor | `ecbb1df8bd4972f324ae0981f378c6bf4e97bf3f` |

Upstreams: `280Zo/charybdis-wireless-mini-zmk-firmware` and `280Zo/prospector-zmk-module`; UI derived from `carrefinho/prospector-zmk-module` feat/new-status-screens; official ZMK is `zmkfirmware/zmk`; PMW3610 module from `280Zo/zmk-pmw3610-driver`.

`firmware/config/west.yml` references: `zmkfirmware/zmk@main`, `280Zo/zmk-pmw3610-driver@main`, `iblh/prospector-zmk-module@feat/touch-no-sensor`. User previously fixed missing `iblh` remote declaration. **Next release: pin exact compatible commit SHAs** rather than floating mains for reproducibility.

## Proven successful CI

- **Failed baseline:** https://github.com/iblh/charybdis-wireless-mini-zmk-firmware/actions/runs/39888780214. Only two touch builds failed; linker unresolved LVGL Slider/Button symbols.
- **Successful run:** https://github.com/iblh/charybdis-wireless-mini-zmk-firmware/actions/runs/39911723815 ; `success` on branch `feat/touch-no-sensor`, firmware SHA above.
- Important artifact: `firmware-dongle_prospector_nano_no_sensor-qwerty` (GitHub artifact ID 12482963870, as reported by API at handoff).
- Inside ZIP: `charybdis_dongle prospector_adapter-qwerty.uf2`.
- User downloaded that artifact, flashed it to NICENANO and observed display turn on. A verified copy of the downloadable artifact and three UF2 files is preserved under `artifacts/ci-39911723815-qwerty/`. Dongle UF2 SHA256: `b5236a43ac9812124f711ba7baa1e66884f91385a0c84abd13fdd4b9cb2d48c2` (UF2 header nRF52840 / 0x26000).
- Do not accidentally flash `charybdis_left_dongle` / `charybdis_right_dongle` into Dongle board. Need separate pairing procedure once keyboard is available.

## Build matrix

Entry in `firmware/build.yaml`: `dongle_prospector_nano_no_sensor` board `nice_nano//zmk`; shields `charybdis_left_dongle`, `charybdis_right_dongle`, and stacked `"charybdis_dongle prospector_adapter"` with QWERTY/Colemak-DH. For the stacked Dongle, extra configs are listed in order:

```text
config/dongle_prospector/dongle_prospector_common.conf
config/dongle_prospector_layouts/dongle_prospector_layout_operator.conf
config/dongle_prospector/dongle_prospector_no_sensor.conf
config/dongle_prospector/dongle_prospector_touch.conf
```

Extra overlays:

```text
config/dongle_prospector/dongle_prospector_no_sensor.overlay
config/dongle_prospector/dongle_prospector_touch.overlay
```

Touch config enables: `CONFIG_PROSPECTOR_TOUCH_UI=y`, `CONFIG_INPUT_CST816S=y`, `CONFIG_INPUT_CST816S_INTERRUPT=y`, `CONFIG_LV_Z_POINTER_INPUT=y`, **`CONFIG_LV_USE_BUTTON=y`, `CONFIG_LV_USE_BAR=y`, `CONFIG_LV_USE_SLIDER=y`**, no ambient light, brightness 65, steps 5, idle 300000 milliseconds (5 min), `CONFIG_ZMK_STUDIO=n` for RAM.

## Remote builds

Actions workflow `firmware/.github/workflows/build.yml` has manual `workflow_dispatch`. Run on branch `feat/touch-no-sensor` via GitHub UI or:

```bash
gh workflow run build.yml --repo iblh/charybdis-wireless-mini-zmk-firmware --ref feat/touch-no-sensor
```

A "rerun failed jobs" on a prior run uses old commits, so create a *new run* after editing/pushing code.

GitHub public standard runners are normally free of Actions-minute fees. User observed quota/billing concern, but this successful CI means immediate local build is not required just to flash; local is preferred for many quick iterations. Avoid full CI matrix for every small display edit.

## Local build

`firmware/local-build/{README.md,docker-compose.yml,build_setup.sh}` exists upstream. The upstream script loops over the full build matrix, using yq/jq and many sandbox copies. It is wasteful for quick changes. This handoff includes `scripts/build-touch-only.sh` and `scripts/build-touch-only-container.sh`, targeting one QWERTY no-sensor Prospector artifact, with the *local module checkout* overlaid after West update. See `docs/09-agent-first-task.md` for exact invocation. **Scripts were syntax-checked here, but cannot be Docker-executed in the present environment.** If container compatibility fails, adapt based on real log.

## Proven upload

```bash
# Board connected with proper 3.3V/GND; double tap RESET/GND
ls /Volumes/NICENANO
cp -X 'path/to/charybdis_dongle prospector_adapter-qwerty.uf2' /Volumes/NICENANO/
```

ZMK generates UF2 itself, unlike earlier Arduino HEX→UF2 conversion. Never re-run or modify the early Arduino linker settings as a ZMK "fix".
