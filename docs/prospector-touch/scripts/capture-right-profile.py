#!/usr/bin/env python3
"""Read one explicitly selected serial port; no third-party Python packages needed."""
import argparse
import codecs
import datetime
import errno
import fcntl
import os
from pathlib import Path
import select
import struct
import sys
import termios
import time
import tty


def scan_command(fd, action, run):
    data = f'!P8 {action} {run}\n'.encode('ascii')
    if os.write(fd, data) != len(data):
        raise OSError('Incomplete diagnostic control command')


def capture(port, output, duration, scan_ab_run=None):
    fd = os.open(port, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if hasattr(termios, 'TIOCEXCL'):
            fcntl.ioctl(fd, termios.TIOCEXCL)
        tty.setraw(fd, termios.TCSANOW)
        attrs = termios.tcgetattr(fd)
        attrs[4] = attrs[5] = termios.B115200
        attrs[2] |= termios.CLOCAL | termios.CREAD
        attrs[2] &= ~getattr(termios, 'CRTSCTS', 0)
        termios.tcsetattr(fd, termios.TCSANOW, attrs)
        # CDC may use DTR to decide whether a terminal is attached.
        line_status = 'unavailable'
        if hasattr(termios, 'TIOCMBIS') and hasattr(termios, 'TIOCM_DTR'):
            try:
                bits = termios.TIOCM_DTR | getattr(termios, 'TIOCM_RTS', 0)
                fcntl.ioctl(fd, termios.TIOCMBIS, struct.pack('I', bits))
                line_status = 'DTR/RTS requested'
                if hasattr(termios, 'TIOCMGET'):
                    state = bytearray(4)
                    fcntl.ioctl(fd, termios.TIOCMGET, state, True)
                    value = struct.unpack('I', state)[0]
                    line_status = (f'DTR={bool(value & termios.TIOCM_DTR)} '
                                   f'RTS={bool(value & getattr(termios, "TIOCM_RTS", 0))}')
            except OSError as error:
                if error.errno not in (errno.ENOTTY, errno.EINVAL):
                    raise
        output.parent.mkdir(parents=True, exist_ok=True)
        # Exclusive creation avoids overwriting prior bench evidence.
        with output.open('x', encoding='utf-8') as stream:
            stamp = datetime.datetime.now().astimezone().isoformat()
            stream.write(f'# port={port} started={stamp} duration_s={duration} lines={line_status}\n')
            stream.flush()
            print(f'Capturing {port} -> {output}; Ctrl+C stops.', flush=True)
            decoder = codecs.getincrementaldecoder('utf-8')(errors='replace')
            started = time.monotonic()
            deadline = started + duration
            received = 0
            reason = 'timeout'
            warned = False
            commanded = False
            try:
                while time.monotonic() < deadline:
                    if scan_ab_run and not commanded and time.monotonic() - started >= 5:
                        scan_command(fd, 'START', scan_ab_run)
                        commanded = True
                    ready, _, _ = select.select([fd], [], [], min(.5, max(0, deadline-time.monotonic())))
                    if not ready:
                        if not received and not warned and time.monotonic() - started >= 15:
                            print('No serial bytes after 15 seconds. Verify the diagnostic image '
                                  'and the port; the file header is not device output.',
                                  file=sys.stderr, flush=True)
                            warned = True
                        continue
                    try:
                        data = os.read(fd, 8192)
                    except OSError as error:
                        if error.errno == errno.EAGAIN:
                            continue
                        if error.errno in (errno.EIO, errno.ENXIO):
                            reason = 'device-disconnected'
                            break
                        raise
                    if not data:
                        reason = 'end-of-stream'
                        break
                    received += len(data)
                    chunk = decoder.decode(data)
                    stream.write(chunk); stream.flush()
                    sys.stdout.write(chunk); sys.stdout.flush()
            except KeyboardInterrupt:
                reason = 'interrupted'
            finally:
                if commanded:
                    try: scan_command(fd, 'STOP', scan_ab_run)
                    except OSError: pass  # Firmware also restores after its bounded 80s test.
            tail = decoder.decode(b'', final=True)
            stream.write(tail)
            sys.stdout.write(tail)
            summary = (f'# capture_end bytes={received} elapsed_s={time.monotonic()-started:.1f} '
                       f'reason={reason}\n')
            stream.write('\n' + summary)
            print(summary.strip(), flush=True)
            if not received:
                print('No device output received. This does not mean the firmware is error-free. '
                      'Keep the board powered for at least 15 seconds; verify which board/UF2 '
                      'is connected, then retry with a new output filename.', file=sys.stderr)
                return 3
            return 0
    finally:
        os.close(fd)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', required=True, help='Actual right-keyboard /dev/cu.usbmodem... port')
    parser.add_argument('--output', type=Path, required=True, help='A new log file (will not overwrite)')
    parser.add_argument('--seconds', type=float, default=90)
    parser.add_argument('--scan-ab-run', type=int, help='T5-08 Dongle only: start bounded diagnostic after 5s')
    args = parser.parse_args()
    if not 0 < args.seconds <= 3600:
        parser.error('seconds must be in (0,3600]')
    if args.scan_ab_run is not None and not 0 < args.scan_ab_run <= 0xffffffff:
        parser.error('scan-ab-run must be a positive uint32')
    try:
        return capture(args.port, args.output, args.seconds, args.scan_ab_run)
    except (OSError, ValueError) as error:
        parser.exit(1, f'Capture failed: {error}. Close screen/other serial readers and check the port.\n')


if __name__ == '__main__':
    raise SystemExit(main())
