#!/usr/bin/env python3
"""Guard pinned private host ABI and prove real host callers use linker probes."""
import argparse
from pathlib import Path
import re
import subprocess

PIN = '10ba6d0cb38bc3d258775d27982f707599320085'


def verify_source(root):
    root = Path(root)
    sha = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip()
    dirty = subprocess.check_output(['git', '-C', str(root), 'status', '--porcelain'], text=True)
    if sha != PIN or dirty:
        raise ValueError('BT trace requires the clean pinned Zephyr checkout')
    print('PASS BT trace pinned host ABI; original Zephyr checkout clean')


def verify_disassembly(text):
    calls = {'__wrap_bt_l2cap_create_pdu_timeout': [], '__wrap_bt_att_send': []}
    caller = ''
    for line in text.splitlines():
        head = re.match(r'^\s*[0-9a-f]+ <([^>]+)>:', line)
        if head:
            caller = head[1]
        for target in calls:
            if re.search(r'\b(?:bl|blx|b\.w)\s+[^<]*<' + target + r'>', line):
                calls[target].append(caller)
    if not any(c.startswith('bt_att_') for c in calls['__wrap_bt_l2cap_create_pdu_timeout']):
        raise ValueError('ATT allocator does not call the wrapped PDU allocator')
    if not any('gatt' in c or 'notify' in c for c in calls['__wrap_bt_att_send']):
        raise ValueError('GATT notify does not call the wrapped ATT submitter')
    for symbol in ['bt_l2cap_create_pdu_timeout', 'bt_att_send']:
        if not re.search(r'<'+symbol+r'>:', text):
            raise ValueError('Missing original host function: '+symbol)
    print('PASS real linked host callers use both wrappers:', calls)


def verify_hci(text):
    for target, caller_pattern in [('hci_acl_handle', r'(acl_handle|hci_driver_send)'),
                                   ('hci_num_cmplt_encode', r'prio_recv_thread')]:
        caller = ''; found = False
        for line in text.splitlines():
            m = re.match(r'^\s*[0-9a-f]+ <([^>]+)>:', line)
            if m: caller = m[1]
            if (re.search(caller_pattern, caller) and
                re.search(r'\b(?:bl|blx|b\.w)\s+[^<]*<__wrap_'+target+r'>', line)):
                found = True
        if not found: raise ValueError('Controller does not use HCI wrapper: '+target)
        if not re.search(r'<'+target+r'>:', text): raise ValueError('Original HCI function missing')
    print('PASS real controller ACL submission and Number Of Completed Packets probes linked')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--zephyr', type=Path)
    p.add_argument('--disassembly', type=Path)
    p.add_argument('--hci', action='store_true')
    a = p.parse_args()
    if a.zephyr:
        verify_source(a.zephyr)
    if a.disassembly:
        verify_disassembly(a.disassembly.read_text())
        if a.hci: verify_hci(a.disassembly.read_text())
    if not (a.zephyr or a.disassembly):
        p.error('supply --zephyr and/or --disassembly')
