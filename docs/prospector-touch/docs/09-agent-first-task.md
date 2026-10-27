# 09 — First Codex / Work Session: Execute This

## Goal

Resume from the real, successful UF2 boot. Inventory before changes. Identify highest leverage gap: touch/brightness/wake and stability. Do not regress keyboard HID.

## 1. Read repository state

```bash
cd ~/Workspace/Lab/prospector-pro
bash prospector-pro-handoff/scripts/verify-workspace.sh

git -C firmware branch --show-current
git -C module branch --show-current
git -C firmware status --short
git -C module status --short
```

Inspect actual `firmware/config/west.yml`, `firmware/build.yaml`, `firmware/config/dongle_prospector/dongle_prospector_touch.*`, `module/boards/shields/prospector_adapter/src/touch_settings.c`, `brightness.c` and layout hooks. Do not edit until baseline and any uncommitted changes documented.

## 2. Establish compiler feedback loop

Preflight:

```bash
docker version
docker compose version
uname -m
```

From workspace root:

```bash
bash prospector-pro-handoff/scripts/build-touch-only.sh
```

The script invokes Docker Compose based on `firmware/local-build/docker-compose.yml`, mounts `module` source, runs local West update/build and writes `firmware/build/prospector-touch/zephyr/zmk.uf2`. This wrapper is newly authored and only syntax-checked in the handoff environment; debug any platform/SDK issue from real output. It may require Docker Desktop running, network for dependencies, several GB storage, and more time first build.

After stable single-target local build, create a tested version pin; GitHub Actions final verification still relevant.

## 3. First physical validation (user action)

Without touching BLE pairing, ask user to record current screen after boot, test `SET`, swipe, 5-minute idle and replug behavior. Verify TP_IRQ wire. Do not infer UI correctness from screen powering on.

## 4. Recommended first code work

- Prevent LVGL slider handler from blocking UI due to synchronous fading: move target brightness application to work queue, coalesce rapid slider events.
- Verify `settings_load` occurs and saved brightness applies at safe initialization time.
- Verify touch input pointer mapping and wake-first-touch behavior.
- Implement polished settings screen and runtime theme registry only after touch input reliable; compile-time Operator remains default fallback.
- Add minimal logging/perf metrics without harming HID or unnecessarily enabling USB logging in battery devices.

## 5. Change policy

For each change, produce: a small diff, successful local build log, flashed UF2 name/hash, observed hardware test result, updated QA status. After confirmed stable behavior, push feature branch, run CI, pin SHAs/tags. Never run archived patch script on these existing clones.
