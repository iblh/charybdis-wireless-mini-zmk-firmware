#!/usr/bin/env python3
"""Instrument an isolated copy of the pinned driver; never edit the West checkout."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess

PIN = 'f6e234367b22508b5c0a6bcc82437c64f320089b'
HERE = Path(__file__).resolve().parent


def replace_once(text, before, after):
    if text.count(before) != 1:
        raise ValueError(f'Pinned driver hook no longer unique: {before[:75]!r}')
    return text.replace(before, after, 1)


def prepare(source, output, angle):
    source, output = source.resolve(), output.resolve()
    if source == output or source in output.parents:
        raise ValueError('The staged driver must be outside the source checkout')
    head = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
    status = subprocess.check_output(['git', '-C', str(source), 'status', '--porcelain'], text=True)
    if head != PIN or status:
        raise ValueError(f'Requires clean pinned PMW3610 driver {PIN}; got {head}, dirty={bool(status)}')
    marker = output / '.generated-by-prospector-profile'
    if output.exists():
        if not marker.is_file():
            raise ValueError(f'Refusing to replace unmarked directory: {output}')
        shutil.rmtree(output)
    shutil.copytree(source, output, ignore=shutil.ignore_patterns('.git', '__pycache__'))
    marker.touch()
    text = (source / 'src/pmw3610.c').read_text()
    text = replace_once(text, '#include "pmw3610.h"',
                        '#include "pmw3610.h"\n#include "pmw3610_profile.h"')
    text = replace_once(text, '    data->dev = dev;',
                        '    data->dev = dev;\n    pmw_profile_start(dev);')
    text = replace_once(text, '    pmw3610_set_interrupt(dev, false);\n    k_work_submit',
                        '    pmw_profile_irq();\n    pmw3610_set_interrupt(dev, false);\n    k_work_submit')
    text = replace_once(text, '    pmw3610_report_data(dev);',
                        '    pmw_profile_work_start();\n    pmw3610_report_data(dev);')
    text = replace_once(text, '        drop_motion_bursts--;',
                        '        pmw_profile_wake_drop();\n        drop_motion_bursts--;')
    text = replace_once(text, '        LOG_ERR("SPI burst read failed: %d", err);',
                        '        pmw_profile_spi_error();\n        LOG_ERR("SPI burst read failed: %d", err);')
    text = replace_once(text, '    LOG_DBG("x/y: %d/%d", x, y);',
                        '    pmw_profile_sample(x, y, buf[4],\n'
                        '        ((uint16_t)(buf[PMW3610_SHUTTER_H_POS] & 1) << 8) |\n'
                        '        buf[PMW3610_SHUTTER_L_POS]);')
    text = replace_once(text, '    static int64_t last_smp_time = 0;\n', '')
    text = replace_once(text, '''#if CONFIG_PMW3610_ALT_REPORT_INTERVAL_MIN > 0
    // purge accumulated delta, if last sampled had not been reported on last report tick
    if (now - last_smp_time >= CONFIG_PMW3610_ALT_REPORT_INTERVAL_MIN) {
        dx = 0;
        dy = 0;
    }
    last_smp_time = now;
#endif
''', '    /* Keep unreported movement when the next burst arrives late. */\n')
    # Consume raw accumulators and advance the report clock BEFORE rotation.
    # Otherwise a tiny rotated report that rounds to zero would leave raw dx/dy
    # pending AND retain the same movement in the rotation's fractional carry.
    text = replace_once(text, '        dy = 0;\n        if (have_x) {',
                        '        dy = 0;\n        pmw_profile_rotate(&rx, &ry);\n'
                        '        have_x = rx != 0;\n        have_y = ry != 0;\n'
                        '        if (have_x) {')
    # Count queue failures using the actual API result, without retrying or blocking.
    if text.count('input_report(dev,') != 3:
        raise ValueError('Unexpected input_report call sites')
    text = text.replace('input_report(dev,', 'pmw_profile_input(dev,')
    (output / 'src/pmw3610.c').write_text(text)
    for name in ['pmw3610_profile.h', 'pmw3610_profile.c', 'motion_math.h']:
        shutil.copyfile(HERE / name, output / 'src' / name)
    q = 1048576
    (output / 'src/profile_coeffs.h').write_text(
        f'#define PROFILE_ANGLE ({angle})\n'
        f'#define PROFILE_COS ({round(math.cos(math.radians(angle)) * q)})\n'
        f'#define PROFILE_SIN ({round(math.sin(math.radians(angle)) * q)})\n')
    shutil.copyfile(HERE / 'Kconfig.profile', output / 'Kconfig.profile')
    with (output / 'Kconfig').open('a') as stream:
        stream.write('\nrsource "Kconfig.profile"\n')
    with (output / 'CMakeLists.txt').open('a') as stream:
        stream.write('\nif(CONFIG_PMW3610_ALT_PROFILE)\n'
                     '  zephyr_library_sources(src/pmw3610_profile.c)\nendif()\n')
    # Same module identity: EXTRA_ZEPHYR_MODULES replaces the manifest module.
    module = output / 'zephyr/module.yml'
    module.write_text('name: zmk-pmw3610-driver\n' + module.read_text())
    manifest = {'driver_base_sha': PIN, 'angle_deg_clockwise': angle,
                'source_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                  for p in HERE.iterdir() if p.is_file()}}
    (output / 'profile-source.json').write_text(json.dumps(manifest, indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--angle', type=int, default=15)
    args = parser.parse_args()
    if not -180 <= args.angle <= 180:
        parser.error('angle must be between -180 and 180')
    prepare(args.source, args.output, args.angle)


if __name__ == '__main__':
    main()
