#!/usr/bin/env python3
"""Actual HCI/scan C under fake clock/UART, including pinned central controls."""
from pathlib import Path
import importlib.util,subprocess,tempfile
HERE=Path(__file__).resolve().parent
FW=HERE.parents[1];MODULE=FW.parent/'module'
def function(text,signature):
 a=text.index(signature);b=text.index('{',a);end=b+1;depth=1
 while depth:
  depth+=(text[end]=='{')-(text[end]=='}');end+=1
 return text[a:end]
def body(path):return '\n'.join(l for l in path.read_text().splitlines() if not l.startswith('#include'))
base=r'''
#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <stdarg.h>
#include <errno.h>
#include <assert.h>
#define CONFIG_BT_MAX_CONN 1
#define BUILD_ASSERT(c,m) _Static_assert(c,m)
#define MAX(a,b) ((a)>(b)?(a):(b))
#define MIN(a,b) ((a)<(b)?(a):(b))
#define ARG_UNUSED(x) (void)(x)
#define LOG_MODULE_REGISTER(a,b)
static void logger(const char *format,...){(void)format;}
#define LOG_INF(...) logger(__VA_ARGS__)
#define LOG_DBG(...) logger(__VA_ARGS__)
#define LOG_ERR(...) logger(__VA_ARGS__)
struct k_spinlock{int unused;};typedef int k_spinlock_key_t;
static int k_spin_lock(struct k_spinlock*l){(void)l;return 0;}
static void k_spin_unlock(struct k_spinlock*l,int k){(void)l;(void)k;}
static uint64_t now_us;
static uint32_t pipe_now(void){return (uint32_t)(now_us*64);}
static uint32_t pipe_elapsed(uint32_t a){return (uint32_t)(pipe_now()-a)/64;}
static uint32_t k_uptime_get_32(void){return (uint32_t)(now_us/1000);}
'''
hci=base+r'''
struct bt_conn{int unused;};
struct bt_conn_cb{void(*disconnected)(struct bt_conn*,uint8_t);};
#define BT_CONN_CB_DEFINE(x) struct bt_conn_cb x
struct net_buf{uint8_t*data;size_t len;};
struct bt_hci_acl_hdr{uint16_t handle,len;};
static uint16_t sys_get_le16(const uint8_t*p){return p[0]|((uint16_t)p[1]<<8);}
#define PIPE_CADENCE_HCI_EVT 5
static unsigned cadence_count;
static void pipe_cadence(unsigned s){assert(s==5);cadence_count++;}
'''+body(MODULE/'src/hci_profile.c')+r'''
static int result;static bool early;static unsigned real_tx,real_events;
int __real_hci_acl_handle(struct net_buf*b,struct net_buf**evt){
 (void)evt;real_tx++;
 if(early)__wrap_hci_num_cmplt_encode(b,1,1);
 return result;
}
void __real_hci_num_cmplt_encode(struct net_buf*b,uint16_t handle,uint8_t n){
 (void)b;(void)handle;(void)n;real_events++;
}
int main(void){
 uint8_t data[]={1,0x20,0,0};struct net_buf b={data,sizeof(data)},*evt=NULL;
 now_us=1000;assert(!__wrap_hci_acl_handle(&b,&evt));
 now_us=2000;assert(!__wrap_hci_acl_handle(&b,&evt));
 now_us=9000;__wrap_hci_num_cmplt_encode(&b,1,2);
 assert(!live&&stats.matched==2&&stats.sum_us==15000&&stats.max_us==8000&&stats.batch==2);
 assert(stats.bins[2]==2&&cadence_count==1&&real_events==1);
 __wrap_hci_num_cmplt_encode(&b,1,1);assert(stats.orphan==1);
 result=-12;assert(__wrap_hci_acl_handle(&b,&evt)==-12&&!live&&stats.err==1);result=0;
 early=true;assert(!__wrap_hci_acl_handle(&b,&evt)&&!live);early=false;
 for(unsigned i=0;i<HCI_SLOTS+1;i++)assert(!__wrap_hci_acl_handle(&b,&evt));
 assert(live==16&&stats.overflow==1&&real_tx==21);
 pipe_hci_report();assert(live==16&&!stats.matched&&stats.peak==16);
 __wrap_hci_num_cmplt_encode(&b,1,17);assert(!live&&stats.matched==16&&stats.orphan==1);
 assert(!__wrap_hci_acl_handle(&b,&evt));hci_trace_cb.disconnected(NULL,0);
 assert(!live&&stats.reset==1);
 sequence=UINT32_MAX-1;assert(!__wrap_hci_acl_handle(&b,&evt));
 now_us+=8000;assert(!__wrap_hci_acl_handle(&b,&evt));
 now_us+=8000;__wrap_hci_num_cmplt_encode(&b,1,1);
 assert(live==1);for(unsigned i=0;i<16;i++)if(pending[i].used)assert(pending[i].id==0);
 __wrap_hci_num_cmplt_encode(&b,1,1);assert(!live);
 assert(!__wrap_hci_acl_handle(&b,&evt));now_us+=70000000;
 __wrap_hci_num_cmplt_encode(&b,1,1);assert(stats.max_us==70000000);
 puts("PASS actual HCI C: batched completions/FIFO ages, callback-before-return, failure, overflow without dropping transport, disconnect reset and clocks/sequence wrap");
}
'''
spec=importlib.util.spec_from_file_location('pipeline',HERE/'prepare_pipeline.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
with tempfile.TemporaryDirectory() as td:
 root=Path(td);p.prepare(FW/'zmk',root/'stage')
 text=(root/'stage/app/src/split/bluetooth/central.c').read_text()
 helpers='\n'.join(function(text,f) for f in ['static int start_scanning(void) {','static int stop_scanning(void) {','bool pipe_scan_status(','int pipe_scan_apply('])
 scan=base+r'''
#define CONFIG_PROSPECTOR_SCAN_AB 1
#define CONFIG_ZMK_SPLIT_BLE_CENTRAL_PERIPHERALS 2
#define PERIPHERAL_SLOT_STATE_CONNECTED 2
#define BT_LE_SCAN_PASSIVE NULL
#define split_central_device_found NULL
static struct{void*conn;int state;}peripherals[2]={{(void*)1,2},{NULL,0}};
static bool is_enabled=true,is_scanning=true;
typedef int atomic_t;static atomic_t profile_scan_blocked;
static int atomic_get(atomic_t*p){return *p;}
static void atomic_set(atomic_t*p,int n){*p=n;}
static unsigned starts,stops;static int api_result;
static int bt_le_scan_start(void*p,void*cb){(void)p;(void)cb;starts++;return api_result;}
static int bt_le_scan_stop(void){stops++;return api_result;}
static int start_scanning(void);static int stop_scanning(void);
'''+helpers+r'''
struct device{int unused;};static struct device fake_uart;
#define DEVICE_DT_GET(x) (&fake_uart)
#define DT_CHOSEN(x) 0
static bool device_is_ready(const struct device*d){(void)d;return true;}
static const char*input="";
static int uart_poll_in(const struct device*d,unsigned char*c){(void)d;if(!*input)return -1;*c=*input++;return 0;}
static int64_t k_uptime_get(void){return now_us/1000;}
'''+body(MODULE/'src/scan_ab.c')+r'''
static void feed(const char*s){input=s;pipe_scan_tick();}
static void at(unsigned ms){now_us=(uint64_t)ms*1000;pipe_scan_tick();}
int main(void){
 feed("arbitrary text\n!P8 START 0\n");assert(!active&&is_scanning);
 feed("!P8 START 77\n");assert(active&&phase==1&&is_scanning);
 at(20000);assert(phase==2&&!is_scanning&&stops==1);
 assert(!start_scanning()&&!is_scanning&&starts==0); // callback cannot restart during OFF
 feed("!P8 STOP 78\n");assert(active); // unrelated session cannot stop test
 at(40000);assert(phase==3&&!is_scanning&&stops==1);
 at(60000);assert(phase==4&&is_scanning&&starts==1);
 at(80000);assert(!active&&phase==0&&is_scanning);
 feed("!P8 START 78\n");at(100000);assert(active&&!is_scanning);
 peripherals[0].state=0;peripherals[0].conn=NULL;pipe_scan_tick();
 assert(!active&&is_scanning&&!atomic_get(&profile_scan_blocked));
 feed("!P8 START 99\n");assert(!active); // no connection: reject
 peripherals[0].state=2;peripherals[0].conn=(void*)1;
 feed("!P8 START 80\n");assert(active);feed("!P8 STOP 80\n");assert(!active&&is_scanning);
 feed("!P8 START 81\n");api_result=-5;at(120000);assert(!active&&!atomic_get(&profile_scan_blocked));
 // The native compiler also sees clock helpers; they are used only by HCI here.
 struct k_spinlock dummy; k_spin_unlock(&dummy,k_spin_lock(&dummy));
 assert(pipe_elapsed(pipe_now())==0);
 puts("PASS actual scan C and pinned central helpers: ON/OFF/OFF/ON, start gate, restore on end/STOP/disconnect/API error, session validation and no-connection rejection");
}
'''
 for label,source in [('hci',hci),('scan',scan)]:
  file=root/(label+'.c');file.write_text(source)
  subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror',str(file),'-o',str(root/label)],check=True)
  subprocess.run([str(root/label)],check=True)
