#!/usr/bin/env python3
"""Compile actual trace C: callback races, bounded storage and unchanged transport."""
from pathlib import Path
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
module = HERE.parents[2] / 'module'
text = (module / 'src/ble_tx_profile.c').read_text()
text = '\n'.join(line for line in text.splitlines() if not line.startswith('#include'))
source = r'''
#include <assert.h>
#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>
#include <string.h>
#include <stdio.h>
#include <stdarg.h>
#define CONFIG_BT_MAX_CONN 1
#define CONFIG_BT_ATT_TX_COUNT 3
#define CONFIG_BT_EATT 0
#define CONFIG_BT_GATT_NOTIFY_MULTIPLE 0
#define IS_ENABLED(x) (x)
#define BUILD_ASSERT(c,m) _Static_assert(c,m)
#define MIN(a,b) ((a)<(b)?(a):(b))
#define MAX(a,b) ((a)>(b)?(a):(b))
#define ARG_UNUSED(x) (void)(x)
#define LOG_MODULE_REGISTER(a,b)
static void log_inf(const char *format, ...){(void)format;}
#define LOG_INF(...) log_inf(__VA_ARGS__)
typedef void *k_tid_t;
typedef int64_t k_timeout_t;
struct k_spinlock {int unused;};
typedef int k_spinlock_key_t;
static int k_spin_lock(struct k_spinlock *l){(void)l;return 0;}
static void k_spin_unlock(struct k_spinlock *l,int k){(void)l;(void)k;}
static uint64_t clock_us;
static k_tid_t thread=(void*)1;
static k_tid_t k_current_get(void){return thread;}
static uint32_t k_uptime_get_32(void){return (uint32_t)(clock_us/1000);}
static uint32_t pipe_now(void){return (uint32_t)(clock_us*64);}
static uint32_t pipe_elapsed(uint32_t c){return (uint32_t)(pipe_now()-c)/64;}
#define PIPE_CADENCE_DONE 4
static unsigned completed_sync;
static void pipe_cadence(unsigned stage){assert(stage==PIPE_CADENCE_DONE);completed_sync++;}
struct bt_conn {int unused;};struct bt_gatt_attr {int unused;};
struct net_buf {int unused;};struct net_buf_pool {int unused;};
struct bt_gatt_notify_params {
 const struct bt_gatt_attr *attr;const void *data;uint16_t len;
 void (*func)(struct bt_conn*,void*);void *user_data;
};
static int bt_gatt_notify_cb(struct bt_conn*,struct bt_gatt_notify_params*);
'''+text+r'''
enum {NORMAL,EARLY,FAIL_ALLOC,FAIL_SEND,NO_SUBMIT};
static int mode;
static struct bt_gatt_notify_params pending[64];static unsigned pending_count;
static struct net_buf_pool pool;
static struct net_buf buf;
static const struct bt_gatt_attr attr;
static const char payload[]="not logged";
static unsigned real_allocs,real_sends;
struct net_buf *__real_bt_l2cap_create_pdu_timeout(struct net_buf_pool *p,size_t reserve,k_timeout_t timeout){
 assert(p==&pool&&reserve==0&&timeout==-1);real_allocs++;clock_us+=2500;
 return mode==FAIL_ALLOC?NULL:&buf;
}
int __real_bt_att_send(struct bt_conn *conn,struct net_buf *b){
 assert(conn==(void*)99&&b==&buf);real_sends++;clock_us+=50;
 if(mode==EARLY){
  struct bt_gatt_notify_params *p=&pending[pending_count-1];
  if(p->func)p->func(conn,p->user_data);
 }
 return mode==FAIL_SEND?-5:0;
}
static int bt_gatt_notify_cb(struct bt_conn *conn,struct bt_gatt_notify_params *p){
 assert(!conn&&p->attr==&attr&&p->data==payload&&p->len==sizeof(payload));
 if(mode==NO_SUBMIT)return 0;
 if(!__wrap_bt_l2cap_create_pdu_timeout(&pool,0,-1))return -12;
 assert(pending_count<64);pending[pending_count++]=*p;
 return __wrap_bt_att_send((void*)99,&buf);
}
static int notify(bool sync){return pipe_bt_notify(sync,&attr,payload,sizeof(payload));}
static void finish(unsigned i){if(pending[i].func)pending[i].func((void*)99,pending[i].user_data);}
int main(void){
 assert(notify(true)==0&&outstanding==1&&counts.accepted==1);
 assert(durations[DUR_ALLOC].max==2500&&durations[DUR_SEND].max==50);
 assert(durations[DUR_CALL].max==2550);
 // A concurrent thread allocating during the scope must not contaminate it.
 scope_thread=thread;scope=&tokens[0];thread=(void*)2;
 assert(__wrap_bt_l2cap_create_pdu_timeout(&pool,0,-1)==&buf);
 assert(durations[DUR_ALLOC].n==1);thread=(void*)1;scope_thread=NULL;scope=NULL;
 clock_us+=12500;finish(0);
 assert(!outstanding&&counts.done==1&&completed_sync==1);
 assert(durations[DUR_FLIGHT].max==15050&&durations[DUR_TOTAL].max==17550);
 mode=EARLY;unsigned slot=pending_count;
 assert(notify(true)==0&&counts.early==1&&!outstanding&&completed_sync==2);
 // Callback-before-return must not recycle the slot while the API still runs.
 assert(tokens[0].returned&&tokens[0].completed&&!tokens[0].used);
 finish(slot);assert(completed_sync==2); // duplicate cannot decrement live count
 mode=FAIL_ALLOC;assert(notify(false)==-12&&!outstanding&&counts.alloc_fail==1);
 mode=FAIL_SEND;assert(notify(false)==-5&&!outstanding&&counts.send_fail==1);
 mode=NO_SUBMIT;assert(notify(false)==0&&!outstanding&&counts.no_submit==1);
 assert(counts.errors==2);
 // Missing completion (e.g. disconnect flush) retains tokens, never reuses live
 // callback user_data. Exhaustion still forwards payload using the normal API.
 mode=NORMAL;unsigned first=pending_count;
 for(unsigned i=0;i<TRACE_SLOTS;i++)assert(notify(i%2)==0);
 assert(outstanding==TRACE_SLOTS&&counts.peak==TRACE_SLOTS);
 unsigned alloc_before=real_allocs;
 assert(notify(true)==0&&counts.skipped==1&&outstanding==TRACE_SLOTS);
 assert(real_allocs==alloc_before+1&&pending[pending_count-1].func==NULL);
 pipe_bt_report();assert(outstanding==TRACE_SLOTS&&counts.peak==TRACE_SLOTS);
 assert(!counts.attempts&&!durations[DUR_ALLOC].n);
 for(unsigned i=first;i<first+TRACE_SLOTS;i++)finish(i);
 assert(!outstanding&&completed_sync==2+TRACE_SLOTS/2);
 // Long-idle/cycle wrap must not turn a missing callback into a tiny duration.
 memset(durations,0,sizeof(durations));
 clock_us=67108860;assert(notify(true)==0);unsigned last=pending_count-1;
 clock_us+=8000;finish(last);assert(durations[DUR_TOTAL].max==10550);
 assert(notify(false)==0);last=pending_count-1;clock_us+=70000000;finish(last);
 assert(durations[DUR_TOTAL].max>=70000000);
 // Every duration boundary is assigned exactly once.
 memset(durations,0,sizeof(durations));
 uint32_t edges[]={99,100,1000,6000,10000,20000,30000,50000};
 for(unsigned i=0;i<8;i++)duration_add(DUR_ALLOC,edges[i]);
 for(unsigned i=0;i<8;i++)assert(durations[DUR_ALLOC].bins[i]==1);
 assert(real_sends>0);
 puts("PASS actual BT trace C: allocation/submit/completion timing, early callback, errors, no subscriber, thread scope, token exhaustion fallback, live snapshot, duration bins and clock wrap");
}
'''
with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    (root / 'test.c').write_text(source)
    subprocess.run(['cc', '-std=c11', '-Wall', '-Wextra', '-Werror', str(root / 'test.c'),
                    '-o', str(root / 'test')], check=True)
    subprocess.run([str(root / 'test')], check=True)
