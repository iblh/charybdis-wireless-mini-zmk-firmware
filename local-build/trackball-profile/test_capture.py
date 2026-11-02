#!/usr/bin/env python3
"""Exercise the actual serial collector against a pseudo terminal, not hardware."""
from pathlib import Path
import os
import pty
import subprocess
import sys
import tempfile
import time

script = Path(__file__).resolve().parents[2] / 'docs/prospector-touch/scripts/capture-right-profile.py'
with tempfile.TemporaryDirectory(prefix='prospector-capture-') as tmp:
    master, slave = pty.openpty()
    log = Path(tmp) / 'sample.log'
    proc = subprocess.Popen([sys.executable, str(script), '--port', os.ttyname(slave),
                             '--output', str(log), '--seconds', '0.8'],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        assert proc.stdout.readline().startswith('Capturing ')
        os.write(master, b'STATE ready=1\r\nRAW sq=10/20/30\r\n')
        # UTF-8 can split across independent serial reads.
        value = '方向测试'.encode()
        os.write(master, value[:2]); time.sleep(.05); os.write(master, value[2:] + b'\n')
        stdout, stderr = proc.communicate(timeout=5)
        assert proc.returncode == 0, stderr
        captured = log.read_text()
        assert 'STATE ready=1' in captured and '方向测试' in captured and 'RAW sq=10/20/30' in stdout
        assert '# capture_end bytes=' in captured and 'reason=timeout' in captured
        original = log.read_bytes()
    finally:
        if proc.poll() is None: proc.kill(); proc.wait()
        os.close(master); os.close(slave)
    # Existing output evidence must be preserved even if a new port is opened.
    m2, s2 = pty.openpty()
    try:
        result = subprocess.run([sys.executable, str(script), '--port', os.ttyname(s2),
                                 '--output', str(log), '--seconds', '.1'], capture_output=True)
        assert result.returncode != 0 and log.read_bytes() == original
    finally:
        os.close(m2); os.close(s2)
    m3,s3=pty.openpty()
    try:
        empty=Path(tmp)/'empty.log'
        result=subprocess.run([sys.executable,str(script),'--port',os.ttyname(s3),
                               '--output',str(empty),'--seconds','.2'],capture_output=True,text=True)
        assert result.returncode==3 and 'No device output received' in result.stderr
        assert 'capture_end bytes=0' in empty.read_text()
    finally: os.close(m3);os.close(s3)
print('PASS: serial capture, split UTF-8, periodic text, existing log preservation, explicit zero-byte failure')
