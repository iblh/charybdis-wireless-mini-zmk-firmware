#!/usr/bin/env python3
"""Stage exact pinned ZMK app with aggregate diagnostics; never patch West checkout."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

PIN = '4dd95d7840eb3d5a3f59bb29fbf1ab054715ef85'


def once(text, before, after):
    if text.count(before) != 1:
        raise ValueError(f'Nonunique pinned hook: {before[:90]}')
    return text.replace(before, after, 1)


def instrument_central(text):
    text = once(text, '        if (&peripheral_input_slots[i].sub == params) {',
                '''        if (&peripheral_input_slots[i].sub == params) {
            if (payload.sync) pipe_cadence(PIPE_CADENCE_RX);''')
    text = once(text, '    uint8_t source;\n    struct zmk_split_transport_peripheral_event event;',
                '    uint8_t source;\n    uint32_t queued_at;\n    struct zmk_split_transport_peripheral_event event;')
    helper = '''
static int profile_enqueue(struct peripheral_event_wrapper *event) {
    bool key = event->event.type == ZMK_SPLIT_TRANSPORT_PERIPHERAL_EVENT_TYPE_KEY_POSITION_EVENT;
    bool point = event->event.type == ZMK_SPLIT_TRANSPORT_PERIPHERAL_EVENT_TYPE_INPUT_EVENT;
    pipe_count(key ? (event->source == 0 ? PIPE_RX_KEY0 : PIPE_RX_KEY1) :
                    (point ? PIPE_RX_POINT : PIPE_RX_OTHER));
    event->queued_at = pipe_now();
    int result = k_msgq_put(&peripheral_event_msgq, event, K_NO_WAIT);
    if (result) pipe_count(key ? PIPE_DROP_KEY : (point ? PIPE_DROP_POINT : PIPE_DROP_OTHER));
    pipe_max(PIPE_QUEUE_HIGH, k_msgq_num_used_get(&peripheral_event_msgq));
    return result;
}
'''
    pattern = r'k_msgq_put\(&peripheral_event_msgq, &(\w+), K_NO_WAIT\)'
    text, count = re.subn(pattern, r'profile_enqueue(&\1)', text)
    if count != 7:
        raise ValueError(f'Expected 7 central enqueue sites, found {count}')
    text = once(text, 'K_WORK_DEFINE(peripheral_event_work, peripheral_event_work_callback);',
                'K_WORK_DEFINE(peripheral_event_work, peripheral_event_work_callback);\n' + helper)
    text = once(text, '        zmk_split_transport_central_peripheral_event_handler(&bt_central, ev.source, ev.event);',
                '''        pipe_max(PIPE_AGE_US, pipe_elapsed(ev.queued_at));
        uint32_t started = pipe_now();
        int result = zmk_split_transport_central_peripheral_event_handler(&bt_central, ev.source, ev.event);
        pipe_max(PIPE_HANDLE_US, pipe_elapsed(started));
        if (result < 0) pipe_count(PIPE_HANDLE_ERR);''')
    text = once(text, 'static bool is_scanning = false;', '''static bool is_scanning = false;
#if defined(CONFIG_PROSPECTOR_SCAN_AB)
static atomic_t profile_scan_blocked;
#endif''')
    text = once(text, 'static int start_scanning(void) {', '''static int start_scanning(void) {
#if defined(CONFIG_PROSPECTOR_SCAN_AB)
    if (atomic_get(&profile_scan_blocked)) return 0;
#endif''')
    text = once(text, '        LOG_ERR("Scanning failed to start (err %d)", err);', '''#if defined(CONFIG_PROSPECTOR_SCAN_AB)
        is_scanning = false;
#endif
        LOG_ERR("Scanning failed to start (err %d)", err);''')
    helper = '''
#if defined(CONFIG_PROSPECTOR_SCAN_AB)
bool pipe_scan_status(unsigned int *links) {
    *links = 0;
    for (unsigned int i = 0; i < CONFIG_ZMK_SPLIT_BLE_CENTRAL_PERIPHERALS; i++)
        *links += peripherals[i].state == PERIPHERAL_SLOT_STATE_CONNECTED;
    return is_scanning;
}
int pipe_scan_apply(bool blocked) {
    unsigned int links;
    pipe_scan_status(&links);
    if (blocked && links != 1) return -EAGAIN;
    atomic_set(&profile_scan_blocked, blocked);
    if (blocked) return is_scanning ? stop_scanning() : 0;
    return start_scanning();
}
#endif
'''
    text = once(text, 'static void split_central_connected(struct bt_conn *conn, uint8_t conn_err) {',
                helper + '\nstatic void split_central_connected(struct bt_conn *conn, uint8_t conn_err) {')
    return text


def instrument_service(text):
    helper = '''
static int profile_notify(bool point, const struct bt_gatt_attr *attr, const void *data, uint16_t len) {
    pipe_count(point ? PIPE_TX_POINT : PIPE_TX_KEY);
    uint32_t started = pipe_now();
#if defined(CONFIG_PROSPECTOR_BLE_TX_TRACE)
    int result = pipe_bt_notify(point && ((const struct zmk_split_input_event_payload *)data)->sync,
                                attr, data, len);
#else
    int result = bt_gatt_notify(NULL, attr, data, len);
#endif
    pipe_max(PIPE_NOTIFY_US, pipe_elapsed(started));
    if (result) pipe_count(point ? PIPE_TX_POINT_ERR : PIPE_TX_KEY_ERR);
    if (!result && point && ((const struct zmk_split_input_event_payload *)data)->sync)
        pipe_cadence(PIPE_CADENCE_TX);
    return result;
}
static int profile_queue(struct k_msgq *queue, const void *data, k_timeout_t timeout, bool point) {
    uint32_t started = pipe_now();
    int result = k_msgq_put(queue, data, timeout);
    pipe_max(PIPE_TX_WAIT_US, pipe_elapsed(started));
    if (result) pipe_count(point ? PIPE_TX_POINT_FULL : PIPE_TX_KEY_FULL);
    return result;
}
'''
    text = once(text, '#define POS_STATE_LEN 16', '#define POS_STATE_LEN 16\n' + helper)
    text = once(text, 'bt_gatt_notify(NULL, &split_svc.attrs[1], &state, sizeof(state))',
                'profile_notify(false, &split_svc.attrs[1], &state, sizeof(state))')
    text = once(text, 'bt_gatt_notify(NULL, &split_svc.attrs[item.attr_index], &item.payload,',
                'profile_notify(true, &split_svc.attrs[item.attr_index], &item.payload,')
    text = once(text, 'k_msgq_put(&position_state_msgq, position_state, K_MSEC(100))',
                'profile_queue(&position_state_msgq, position_state, K_MSEC(100), false)')
    if text.count('k_msgq_put(&input_event_msgq, &item, K_NO_WAIT)') != 2:
        raise ValueError('Expected two input queue sites')
    return text.replace('k_msgq_put(&input_event_msgq, &item, K_NO_WAIT)',
                        'profile_queue(&input_event_msgq, &item, K_NO_WAIT, true)')


def instrument_usb(text):
    text = once(text, '    switch (zmk_usb_get_status()) {',
                '''    pipe_count(report[0] == ZMK_HID_REPORT_ID_KEYBOARD ? PIPE_USB_KEY :
               (report[0] == ZMK_HID_REPORT_ID_MOUSE ? PIPE_USB_MOUSE : PIPE_USB_OTHER));
    switch (zmk_usb_get_status()) {''')
    text = once(text, '        k_sem_take(&hid_sem, K_MSEC(30));',
                '''        ; /* Declaration after switch label (C99). */
        uint32_t started = pipe_now();
        int taken = k_sem_take(&hid_sem, K_MSEC(30));
        pipe_max(PIPE_USB_WAIT_US, pipe_elapsed(started));
        if (taken) pipe_count(PIPE_USB_TIMEOUT);
        /* Measurement only: preserve upstream timeout/write behavior. */
        started = pipe_now();''')
    text = once(text, '        int err = hid_int_ep_write(hid_dev, report, len, NULL);',
                '''        int err = hid_int_ep_write(hid_dev, report, len, NULL);
        pipe_max(PIPE_USB_WRITE_US, pipe_elapsed(started));
        if (err) pipe_count(PIPE_USB_ERR);
        if (!err && report[0] == ZMK_HID_REPORT_ID_MOUSE) pipe_cadence(PIPE_CADENCE_USB);''')
    text = once(text, '        return usb_wakeup_request();',
                '''        { int result = usb_wakeup_request();
          if (result) pipe_count(PIPE_USB_ERR);
          return result; }''')
    return once(text, '        return -ENODEV;', '        pipe_count(PIPE_USB_ERR);\n        return -ENODEV;')


def instrument_mouse(text):
    return once(text, '        zmk_endpoint_send_mouse_report();',
                '''        uint32_t started = pipe_now();
        int sent = zmk_endpoint_send_mouse_report();
        pipe_max(PIPE_MOUSE_SEND_US, pipe_elapsed(started));
        if (sent) pipe_count(PIPE_MOUSE_SEND_ERR);''')


HOOKS = {
    'src/split/bluetooth/central.c': instrument_central,
    'src/split/bluetooth/service.c': instrument_service,
    'src/usb_hid.c': instrument_usb,
    'src/pointing/input_listener.c': instrument_mouse,
}


def prepare(source, output):
    source, output = source.resolve(), output.resolve()
    if source == output or source in output.parents or output in source.parents:
        raise ValueError('Stage must be outside source')
    head = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
    dirty = subprocess.check_output(['git', '-C', str(source), 'status', '--porcelain'], text=True)
    if head != PIN or dirty:
        raise ValueError(f'Requires clean pinned ZMK {PIN}')
    # Validate all hooks before touching the stage.
    patched = {name: '#include <prospector/pipeline_profile.h>\n' + fn((source/'app'/name).read_text())
               for name, fn in HOOKS.items()}
    marker = output / '.generated-by-prospector-pipeline'
    if output.exists():
        if not marker.is_file():
            raise ValueError(f'Refusing to replace unmarked stage {output}')
        shutil.rmtree(output)
    shutil.copytree(source / 'app', output / 'app', ignore=shutil.ignore_patterns('__pycache__'))
    marker.touch()
    for name, text in patched.items():
        (output / 'app' / name).write_text(text)
    manifest = {'zmk_base_sha': PIN, 'patched_sha256': {
        name: hashlib.sha256(text.encode()).hexdigest() for name, text in patched.items()},
        'patch_script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (output / 'pipeline-source.json').write_text(json.dumps(manifest, indent=2)+'\n')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    prepare(args.source, args.output)
