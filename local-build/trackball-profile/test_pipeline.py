#!/usr/bin/env python3
"""Exercise actual generated queue/USB hooks with overflow and timeout injection."""
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
FW = HERE.parents[1]
spec = importlib.util.spec_from_file_location('pipeline', HERE / 'prepare_pipeline.py')
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


def function(text, signature):
    start = text.index(signature)
    brace = text.index('{', start)
    depth = 1
    end = brace + 1
    while depth:
        if text[end] == '{': depth += 1
        if text[end] == '}': depth -= 1
        end += 1
    return text[start:end]


with tempfile.TemporaryDirectory() as td:
    out = Path(td)
    stage = out/'zmk'
    p.prepare(FW/'zmk', stage)
    # Regeneration must not touch the real source, and unknown directories are protected.
    p.prepare(FW/'zmk', stage)
    unknown=out/'unknown'; unknown.mkdir(); (unknown/'keep').write_text('user data')
    try: p.prepare(FW/'zmk', unknown)
    except ValueError: pass
    else: raise AssertionError('unmarked directory overwritten')
    assert (unknown/'keep').read_text()=='user data'
    central=(stage/'app/src/split/bluetooth/central.c').read_text()
    service=(stage/'app/src/split/bluetooth/service.c').read_text()
    usb=(stage/'app/src/usb_hid.c').read_text()
    header=(FW.parent/'module/include/prospector/pipeline_profile.h').read_text()
    enum=header[header.index('enum pipe_metric'):header.index('void pipe_count')]
    source=r'''
#include <assert.h>
#include <stdint.h>
#include <stdbool.h>
#include <errno.h>
#include <stddef.h>
#include <stdio.h>
'''+ '#define CONFIG_PROSPECTOR_PIPELINE_CADENCE 1\n'+enum+r'''
static unsigned cadence_calls[PIPE_CADENCE_COUNT];
void pipe_cadence(enum pipe_cadence_stage stage){cadence_calls[stage]++;}
static uint32_t count[PIPE_METRIC_COUNT], maximum[PIPE_METRIC_COUNT], now;
static void pipe_count(enum pipe_metric m){count[m]++;}
static void pipe_max(enum pipe_metric m,uint32_t v){if(v>maximum[m])maximum[m]=v;}
static uint32_t pipe_now(void){return now;}
static uint32_t pipe_elapsed(uint32_t start){return now-start;}
typedef int k_timeout_t;
#define K_NO_WAIT 0
#define K_MSEC(x) (x)
#define ZMK_SPLIT_TRANSPORT_PERIPHERAL_EVENT_TYPE_KEY_POSITION_EVENT 0
#define ZMK_SPLIT_TRANSPORT_PERIPHERAL_EVENT_TYPE_INPUT_EVENT 1
struct k_msgq {int used;};
static struct k_msgq peripheral_event_msgq;
struct peripheral_event_wrapper {uint8_t source;uint32_t queued_at;struct {int type;} event;};
static int k_msgq_put(struct k_msgq*q,const void*e,int timeout){
 (void)e; if(q->used==5){now+=timeout*1000;return -EAGAIN;}q->used++;return 0;}
static uint32_t k_msgq_num_used_get(struct k_msgq*q){return q->used;}
struct bt_gatt_attr {int dummy;};
struct zmk_split_input_event_payload { bool sync; };
static int notify_result;
static int bt_gatt_notify(void*c,const struct bt_gatt_attr*a,const void*d,uint16_t n){
 (void)c;(void)a;(void)d;(void)n;now+=3700;return notify_result;}
'''+function(central,'static int profile_enqueue(')+function(service,'static int profile_notify(')+function(service,'static int profile_queue(')+r'''
#define ZMK_HID_REPORT_ID_KEYBOARD 1
#define ZMK_HID_REPORT_ID_MOUSE 4
enum {USB_DC_SUSPEND,USB_DC_ERROR,USB_DC_RESET,USB_DC_DISCONNECTED,USB_DC_UNKNOWN,USB_DC_CONFIGURED};
static int status=USB_DC_CONFIGURED, sem_result,write_result,writes;
static int hid_sem;static void*hid_dev;
static int zmk_usb_get_status(void){return status;}
static int usb_wakeup_request(void){return -EIO;}
static int k_sem_take(int*s,int timeout){(void)s;now+=sem_result?timeout*1000:200;return sem_result;}
static void k_sem_give(int*s){(void)s;}
static int hid_int_ep_write(void*d,const uint8_t*r,size_t n,void*v){
 (void)d;(void)r;(void)n;(void)v;writes++;now+=17;return write_result;}
'''+function(usb,'static int zmk_usb_hid_send_report(')+r'''
int main(void){
 struct peripheral_event_wrapper e={.source=0,.event={.type=0}};
 for(int i=0;i<5;i++)assert(profile_enqueue(&e)==0);
 e.source=1;assert(profile_enqueue(&e)==-EAGAIN);
 e.event.type=1;assert(profile_enqueue(&e)==-EAGAIN);
 e.event.type=3;assert(profile_enqueue(&e)==-EAGAIN);
 assert(count[PIPE_RX_KEY0]==5&&count[PIPE_RX_KEY1]==1&&count[PIPE_RX_POINT]==1);
 assert(count[PIPE_DROP_KEY]==1&&count[PIPE_DROP_POINT]==1&&count[PIPE_DROP_OTHER]==1);
 assert(maximum[PIPE_QUEUE_HIGH]==5);
 struct k_msgq q={.used=5};
 assert(profile_queue(&q,&e,100,false)==-EAGAIN);
 assert(count[PIPE_TX_KEY_FULL]==1&&maximum[PIPE_TX_WAIT_US]==100000);
 assert(profile_queue(&q,&e,0,true)==-EAGAIN&&count[PIPE_TX_POINT_FULL]==1);
 notify_result=-ENOMEM;
 assert(profile_notify(false,NULL,NULL,16)==-ENOMEM);
 assert(profile_notify(true,NULL,NULL,8)==-ENOMEM);
 assert(count[PIPE_TX_KEY_ERR]==1&&count[PIPE_TX_POINT_ERR]==1&&maximum[PIPE_NOTIFY_US]==3700);
 struct zmk_split_input_event_payload payload={.sync=false};notify_result=0;
 assert(profile_notify(true,NULL,&payload,sizeof(payload))==0);
 assert(cadence_calls[PIPE_CADENCE_TX]==0);
 payload.sync=true;assert(profile_notify(true,NULL,&payload,sizeof(payload))==0);
 assert(cadence_calls[PIPE_CADENCE_TX]==1);
 notify_result=-ENOMEM;assert(profile_notify(true,NULL,&payload,sizeof(payload))==-ENOMEM);
 assert(cadence_calls[PIPE_CADENCE_TX]==1); /* failures do not become accepted frames */
 uint8_t key[]={1},mouse[]={4};
 assert(zmk_usb_hid_send_report(key,1)==0);
 sem_result=-EAGAIN;write_result=-EBUSY;
 assert(zmk_usb_hid_send_report(mouse,1)==-EBUSY);
 assert(count[PIPE_USB_TIMEOUT]==1&&count[PIPE_USB_ERR]==1&&maximum[PIPE_USB_WAIT_US]==30000);
 assert(writes==2); /* Instrumentation preserves the existing timeout/write policy. */
 assert(cadence_calls[PIPE_CADENCE_USB]==0); /* failed mouse write excluded */
 sem_result=write_result=0;
 assert(zmk_usb_hid_send_report(mouse,1)==0&&cadence_calls[PIPE_CADENCE_USB]==1);
 status=USB_DC_DISCONNECTED;assert(zmk_usb_hid_send_report(key,1)==-ENODEV);
 status=USB_DC_SUSPEND;assert(zmk_usb_hid_send_report(key,1)==-EIO);
 assert(count[PIPE_USB_ERR]==3);
 puts("PASS actual generated pipeline hooks: queue overflow, per-source counts, 100ms queue stall, GATT failure and USB semaphore/endpoint errors");
}
'''
    c=out/'test.c';c.write_text(source)
    subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror',str(c),'-o',str(out/'test')],check=True)
    subprocess.run([str(out/'test')],check=True)
    # The staged app lives inside the firmware Git repo. Its device source ID
    # must use the ZMK patch manifest, not accidentally identify the parent repo.
    config=out/'config';config.mkdir();(config/'test.conf').write_text('CONFIG_TEST=y\n')
    auto=out/'autoconf';auto.write_text('CONFIG_TEST=y\n')
    output=out/'build_info.h'
    command=['python3',str(FW.parent/'module/tools/generate_build_info.py'),
             '--module',str(FW.parent/'module'),'--config',str(config),'--autoconfig',str(auto),
             '--zmk',str(stage),'--zephyr',str(FW/'zephyr'),'--output',str(output)]
    subprocess.run(command,check=True)
    first=output.read_text().split('PROSPECTOR_SOURCE_ID ')[1].splitlines()[0]
    manifest_path=stage/'pipeline-source.json'
    manifest=json.loads(manifest_path.read_text());manifest['patch_script_sha256']='different'
    manifest_path.write_text(json.dumps(manifest))
    subprocess.run(command,check=True)
    second=output.read_text().split('PROSPECTOR_SOURCE_ID ')[1].splitlines()[0]
    assert first!=second
    (stage/'app/src/usb_hid.c').write_text('unrecorded modification')
    rejected=subprocess.run(command,capture_output=True,text=True)
    assert rejected.returncode and 'differs from manifest' in rejected.stderr
    print('PASS staged source identity: patch manifest changes ID; unrecorded core edits rejected')
    assert not subprocess.check_output(['git','-C',str(FW/'zmk'),'status','--porcelain'])
