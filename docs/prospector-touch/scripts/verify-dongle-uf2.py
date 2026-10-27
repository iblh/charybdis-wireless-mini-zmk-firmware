#!/usr/bin/env python3
"""Validate application UF2 for this board's existing 0.6.0 bootloader."""
import struct
import sys
from pathlib import Path

START = 0x26000
END = 0xAD000  # Adafruit nRF52 bootloader 0.6.0 uf2cfg.h USER_FLASH_END


def verify(path):
    blocks = []
    data = Path(path).read_bytes()
    if not data or len(data) % 512:
        raise ValueError('Incomplete UF2')
    for offset in range(0, len(data), 512):
        block = data[offset:offset + 512]
        m0, m1, flags, addr, size, index, count, family = struct.unpack_from('<8I', block)
        if (m0, m1, struct.unpack_from('<I', block, 508)[0]) != (0x0A324655, 0x9E5D5157, 0x0AB16F30):
            raise ValueError('Invalid UF2 magic')
        if flags != 0x2000 or family != 0xADA52840 or size != 256:
            raise ValueError('Not a supported nRF52840 application UF2')
        if count != len(data) // 512 or index != offset // 512:
            raise ValueError('Invalid UF2 block sequence')
        blocks.append((addr, block[32:32 + size]))
    addresses = [a for a, _ in blocks]
    if addresses != list(range(START, START + 256 * len(blocks), 256)):
        raise ValueError('Unexpected application address range')
    end = addresses[-1] + 256
    if end > END:
        raise ValueError(f'Image ends at 0x{end:X}, beyond bootloader limit 0x{END:X}; DO NOT FLASH')
    sp, reset = struct.unpack_from('<2I', blocks[0][1])
    if not (0x20000000 < sp <= 0x20040000 and reset & 1 and START <= (reset & ~1) < end):
        raise ValueError('Invalid application vectors')
    print(f'UF2 PASS: 0x{START:X}–0x{end:X}; {END - end} bytes below bootloader limit')


if __name__ == '__main__':
    try:
        verify(sys.argv[1])
    except (ValueError, OSError, IndexError) as error:
        sys.exit(str(error))
