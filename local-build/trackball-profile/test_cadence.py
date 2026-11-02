#!/usr/bin/env python3
"""Actual cadence collector C: burst/gap bins, independent stages, idle/wrap handling."""
from pathlib import Path
import subprocess
import tempfile

FW=Path(__file__).resolve().parents[2]
module=FW.parent/'module'
text=(module/'src/pipeline_profile.c').read_text()
collector=text[text.index('struct cadence_stats {'):text.index('static void report_cadence(')]
header=(module/'include/prospector/pipeline_profile.h').read_text()
enum=header[header.index('enum pipe_cadence_stage'):header.index('#if defined(CONFIG_PROSPECTOR_PIPELINE_CADENCE)')]
source=r'''
#include <stdint.h>
#include <stdbool.h>
#include <string.h>
#include <assert.h>
#include <stdio.h>
#define MIN(a,b) ((a)<(b)?(a):(b))
#define MAX(a,b) ((a)>(b)?(a):(b))
struct k_spinlock { int unused; };static struct k_spinlock lock;
typedef int k_spinlock_key_t;
static int k_spin_lock(struct k_spinlock*p){(void)p;return 0;}
static void k_spin_unlock(struct k_spinlock*p,int k){(void)p;(void)k;}
static uint32_t now_cycles,now_ms;
static uint32_t k_cycle_get_32(void){return now_cycles;}
static uint32_t k_uptime_get_32(void){return now_ms;}
static uint32_t k_cyc_to_us_floor32(uint32_t cycles){return cycles/64;}
'''+enum+collector+r'''
static void advance(uint32_t us){now_cycles+=us*64U;now_ms+=us/1000;}
int main(void){
 pipe_cadence(PIPE_CADENCE_RX);
 uint32_t steps[]={500,1000,6000,10000,14000,20000,30000,50000};
 for(unsigned i=0;i<8;i++){advance(steps[i]);pipe_cadence(PIPE_CADENCE_RX);}
 struct cadence_stats *s=&cadence[PIPE_CADENCE_RX];
 assert(s->frames==9);for(int i=0;i<8;i++)assert(s->bins[i]==1);
 assert(s->max_us==50000&&s->max_under50_us==30000);
 assert(!cadence[PIPE_CADENCE_USB].frames);
 pipe_cadence(PIPE_CADENCE_PMW);advance(8000);pipe_cadence(PIPE_CADENCE_PMW);
 pipe_cadence(PIPE_CADENCE_TX);advance(45000);pipe_cadence(PIPE_CADENCE_TX);
 assert(cadence[PIPE_CADENCE_PMW].bins[2]==1);
 assert(cadence[PIPE_CADENCE_TX].bins[6]==1);
 assert(cadence[PIPE_CADENCE_USB].frames==0);
 // Restore the RX clock before checking its next-window interval.
 now_cycles=cadence_last_cycles[PIPE_CADENCE_RX];now_ms=cadence_last_ms[PIPE_CADENCE_RX];
 // Draining a window preserves the last arrival to measure across windows.
 memset(cadence,0,sizeof(cadence));advance(7500);pipe_cadence(PIPE_CADENCE_RX);
 assert(s->frames==1&&s->bins[2]==1&&s->max_us==7500);
 // A 32-bit CPU cycle wrap during active motion must not inflate an interval.
 now_cycles=UINT32_MAX-127U;now_ms=200;
 pipe_cadence(PIPE_CADENCE_USB);advance(8000);pipe_cadence(PIPE_CADENCE_USB);
 assert(cadence[PIPE_CADENCE_USB].bins[2]==1&&cadence[PIPE_CADENCE_USB].max_us==8000);
 // 70 seconds idle exceeds a 64MHz cycle wrap. Use coarse uptime for that gap.
 advance(70000000);pipe_cadence(PIPE_CADENCE_USB);
 assert(cadence[PIPE_CADENCE_USB].bins[7]==1&&cadence[PIPE_CADENCE_USB].max_us==70000000);
 assert(cadence[PIPE_CADENCE_USB].max_under50_us==8000);
 // Millisecond uptime wrapping after ~49 days still gives a short active gap.
 now_ms=UINT32_MAX-2;pipe_cadence(PIPE_CADENCE_USB);
 advance(8000);pipe_cadence(PIPE_CADENCE_USB);
 assert(cadence[PIPE_CADENCE_USB].bins[2]==2);
 puts("PASS actual cadence C: all interval boundaries, stages, cross-window continuity, active/idle cycle wraps and uptime wrap");
}
'''
with tempfile.TemporaryDirectory() as td:
    p=Path(td);(p/'test.c').write_text(source)
    subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror',str(p/'test.c'),'-o',str(p/'test')],check=True)
    subprocess.run([str(p/'test')],check=True)
