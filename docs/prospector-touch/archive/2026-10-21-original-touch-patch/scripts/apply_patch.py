#!/usr/bin/env python3
"""Patch a personal fork of 280Zo's firmware and Prospector module.
No git operations; make a backup or work on a new git branch first.
Usage: python3 scripts/apply_patch.py /path/to/firmware /path/to/module
"""
from pathlib import Path
import sys, shutil

if len(sys.argv) != 3:
    sys.exit(__doc__)
fw = Path(sys.argv[1]).resolve()
mod = Path(sys.argv[2]).resolve()
root = Path(__file__).resolve().parents[1]

for p in [fw / 'build.yaml', fw / 'config/west.yml', mod / 'boards/shields/prospector_adapter/CMakeLists.txt']:
    if not p.is_file():
        sys.exit(f'Expected upstream file not found: {p}')

for src in (root / 'firmware').rglob('*'):
    if src.is_file():
        dest = fw / src.relative_to(root / 'firmware')
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
for src in (root / 'module_fork').rglob('*'):
    if src.is_file():
        dest = mod / src.relative_to(root / 'module_fork')
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)

build = fw / 'build.yaml'
s = build.read_text()
name = '  - name: dongle_prospector_nano_no_sensor\n'
start = s.find(name)
if start < 0:
    sys.exit('Cannot locate no-sensor build; inspect upstream build.yaml manually.')
end = s.find('\n  - name:', start + len(name))
if end < 0:
    end = len(s)
segment = s[start:end]
confanchor = '          - dongle_prospector/dongle_prospector_no_sensor.conf\n'
overlayanchor = '          - dongle_prospector/dongle_prospector_no_sensor.overlay\n'
if confanchor not in segment or overlayanchor not in segment:
    sys.exit('Upstream matrix structure changed: refusing to insert unsafe patch.')
if 'dongle_prospector_touch.conf' not in segment:
    segment = segment.replace(confanchor, confanchor + '          - dongle_prospector/dongle_prospector_touch.conf\n')
if 'dongle_prospector_touch.overlay' not in segment:
    segment = segment.replace(overlayanchor, overlayanchor + '          - dongle_prospector/dongle_prospector_touch.overlay\n')
s = s[:start] + segment + s[end:]
build.write_text(s)

cmake = mod / 'boards/shields/prospector_adapter/CMakeLists.txt'
s = cmake.read_text()
line = '  zephyr_library_sources_ifdef(CONFIG_PROSPECTOR_TOUCH_UI src/touch_settings.c)\n'
if line not in s:
    anchor = '  zephyr_library_sources(src/brightness.c)\n'
    if anchor not in s:
        sys.exit('Cannot patch CMakeLists.txt; source list changed upstream.')
    s = s.replace(anchor, anchor + line)
cmake.write_text(s)

for name in ['classic','radii','field','operator']:
    f = mod / f'boards/shields/prospector_adapter/src/layouts/{name}/status_screen.c'
    if not f.is_file():
        sys.exit(f'Layout file missing: {f}')
    text = f.read_text()
    include = '#if defined(CONFIG_PROSPECTOR_TOUCH_UI)\n#include <prospector/touch_settings.h>\n#endif\n'
    if include not in text:
        text = include + text
    hook = '#if defined(CONFIG_PROSPECTOR_TOUCH_UI)\n    prospector_touch_settings_attach(screen);\n#endif\n'
    if hook not in text:
        if '    return screen;' not in text:
            sys.exit(f'No return screen hook in {f}')
        text = text.replace('    return screen;', hook + '    return screen;')
    f.write_text(text)
kconfig = mod / 'Kconfig'
s = kconfig.read_text()
if 'config PROSPECTOR_TOUCH_UI' not in s:
    s += '''\nconfig PROSPECTOR_TOUCH_UI
    bool "Enable Prospector touch settings UI"
    default n
    depends on SHIELD_PROSPECTOR_ADAPTER
    help
      Enables on-screen brightness slider with Zephyr LVGL touch input.
'''
    kconfig.write_text(s)
print('Files copied, matrix + module patched. Next: edit firmware config/west.yml')
print('Change prospector-zmk-module remote from 280Zo to YOUR module fork and pin a SHA.')
print('Commit each repository separately, then run GitHub Actions build.')
