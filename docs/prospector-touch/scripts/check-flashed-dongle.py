#!/usr/bin/env python3
"""Compare a UF2 bootloader's CURRENT.UF2 with the known dongle images.

This reads the device volume without writing it or saving a full flash dump.
Only application payload bytes covered by each candidate are compared. It
prints counts and never prints firmware, settings, or BLE bonding bytes.
"""

from __future__ import annotations

import struct
import sys
from pathlib import Path

HANDOFF = Path(__file__).resolve().parents[1]
FIRMWARE = next(parent for parent in HANDOFF.parents if (parent / "config/west.yml").is_file())
ROOT = FIRMWARE.parent
IMAGES = {
    "GitHub Actions #39911723815": HANDOFF
    / "artifacts/ci-39911723815-qwerty/"
    "charybdis_dongle prospector_adapter-qwerty.uf2",
    "local candidate": ROOT / "firmware/build/prospector-touch-candidate-qwerty.uf2",
    "LIGHT button candidate": ROOT / "firmware/build/prospector-touch-light-button-qwerty.uf2",
    "styled LIGHT candidate": ROOT / "firmware/build/prospector-touch-styled-light-qwerty.uf2",
    "touch mapping candidate": ROOT / "firmware/build/prospector-touch-touchmap-qwerty.uf2",
    "UI polish candidate": ROOT / "firmware/build/prospector-touch-ui-polish-qwerty.uf2",
    "four-layout candidate": ROOT / "firmware/build/prospector-touch-four-layouts-qwerty.uf2",
    "lazy-layout diagnostic": ROOT / "firmware/build/prospector-touch-layout-lazy-qwerty.uf2",
    "compact four-layout candidate": ROOT / "firmware/build/prospector-touch-four-layouts-compact-qwerty.uf2",
    "three-layout candidate": ROOT / "firmware/build/prospector-touch-three-layouts-qwerty.uf2",
    "input-modes candidate": ROOT / "firmware/build/prospector-touch-input-modes.uf2",
    "device-page candidate": ROOT / "firmware/build/prospector-touch-device-page-qwerty.uf2",
}
MAGIC_START = (0x0A324655, 0x9E5D5157)
MAGIC_END = 0x0AB16F30


def read_uf2(path: Path) -> dict[int, bytes]:
    blocks: dict[int, bytes] = {}
    with path.open("rb") as source:
        while block := source.read(512):
            if len(block) != 512:
                raise ValueError(f"Incomplete UF2 block in {path}")
            magic0, magic1, _flags, address, size, _index, _count, _family = (
                struct.unpack_from("<8I", block)
            )
            if (magic0, magic1) != MAGIC_START or struct.unpack_from("<I", block, 508)[0] != MAGIC_END:
                raise ValueError(f"Invalid UF2 block in {path}")
            if not 0 < size <= 476:
                raise ValueError(f"Invalid UF2 payload length in {path}")
            payload = block[32 : 32 + size]
            previous = blocks.get(address)
            if previous is not None and previous != payload:
                raise ValueError(f"Conflicting UF2 blocks at 0x{address:x} in {path}")
            blocks[address] = payload
    if not blocks:
        raise ValueError(f"No UF2 blocks in {path}")
    return blocks


def main() -> int:
    current_path = Path(sys.argv[1] if len(sys.argv) > 1 else "/Volumes/NICENANO/CURRENT.UF2")
    if not current_path.is_file():
        print(f"Cannot read {current_path}; check that NICENANO is mounted and CURRENT.UF2 exists.")
        return 2
    try:
        current = read_uf2(current_path)
        print(f"Device readback range: 0x{min(current):X}–0x{max(a + len(b) for a, b in current.items()):X}")
        for label, path in IMAGES.items():
            if not path.is_file():
                continue  # Historical candidates may have been cleaned up.
            image = read_uf2(path)
            present = 0
            matching = 0
            total = sum(map(len, image.values()))
            for address, expected in image.items():
                actual = current.get(address)
                if actual is not None:
                    present += min(len(actual), len(expected))
                    matching += sum(a == b for a, b in zip(actual, expected))
            print(f"{label}: {matching}/{total} matching application bytes; {present}/{total} readable")
            if present == total and matching == total:
                print(f"  EXACT MATCH: {label}")
    except (OSError, ValueError) as error:
        print(f"Could not compare UF2 images: {error}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
