#!/usr/bin/env python3
"""Run actual rotation/profile C with deterministic kernel/input/BLE shims."""
from pathlib import Path
import hashlib
import importlib.util
import math
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
FW = HERE.parents[1]
SOURCE = FW / 'zmk-pmw3610-driver'
spec = importlib.util.spec_from_file_location('prepare_profile', HERE / 'prepare_driver.py')
prepare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prepare)

PLATFORM = r'''
#pragma once
#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>
#include <assert.h>
#include <limits.h>
#include <errno.h>
#include <stdio.h>
#include <stdarg.h>
#include <string.h>
#define LOG_LEVEL_INF 3
#define LOG_MODULE_REGISTER(...)
static int log_lines;
static char log_output[4096];
__attribute__((format(printf,1,2)))
static void profile_log(const char *format, ...) {
 size_t offset=strlen(log_output);va_list args;va_start(args,format);
 int n=vsnprintf(log_output+offset,sizeof(log_output)-offset,format,args);va_end(args);
 assert(n>=0&&(size_t)n<sizeof(log_output)-offset);log_lines++;
}
#define LOG_INF(...) profile_log(__VA_ARGS__)
#define CONFIG_PMW3610_ALT_REPORT_INTERVAL_MIN 12
#define CONFIG_PROSPECTOR_PIPELINE_CADENCE 1
enum pipe_cadence_stage { PIPE_CADENCE_PMW=2 };
static int cadence_frames;
static void pipe_cadence(enum pipe_cadence_stage stage) {assert(stage==PIPE_CADENCE_PMW);cadence_frames++;}
#define BUILD_ASSERT(x, ...) _Static_assert(x, "build assert")
#define DT_NUM_INST_STATUS_OKAY(x) 1
#define MAX(a,b) ((a)>(b)?(a):(b))
#define MIN(a,b) ((a)<(b)?(a):(b))
#define CLAMP(x,low,high) MIN(MAX(x,low),high)
struct device {void *data;const void *config;};
struct k_work {int unused;};
struct k_work_delayable {int unused;};
struct k_spinlock {int unused;};
typedef int k_spinlock_key_t;
typedef int k_timeout_t;
static int64_t now_ms;
static int scheduled, api_result;
static int64_t k_uptime_get(void) {return now_ms;}
static int k_spin_lock(struct k_spinlock *l) {(void)l;return 0;}
static void k_spin_unlock(struct k_spinlock *l,int k) {(void)l;(void)k;}
#define K_SECONDS(x) ((x)*1000)
#define K_WORK_DELAYABLE_DEFINE(name, fn) static struct k_work_delayable name
static int k_work_reschedule(struct k_work_delayable *w,int t) {(void)w;assert(t==2000);scheduled++;return 0;}
struct pixart_data {bool ready;int async_init_step,err;};
struct pixart_config {uint8_t evt_type,x_input_code,y_input_code;};
static int64_t reported_x,reported_y;
static int input_report(const struct device *d,uint8_t t,uint16_t c,int32_t v,bool s,int timeout) {
 (void)d;(void)s;(void)timeout;
 if(api_result==0&&t==2) {if(c==0)reported_x+=v;else if(c==1)reported_y+=v;}
 return api_result;
}
#define LOG_WRN(...) profile_log(__VA_ARGS__)
#define LOG_ERR(...) profile_log(__VA_ARGS__)
#define unlikely(x) (x)
#define K_NO_WAIT 0
#define PMW3610_BURST_SIZE 7
#define PMW3610_REG_MOTION_BURST 0x12
#define PMW3610_X_L_POS 1
#define PMW3610_Y_L_POS 2
#define PMW3610_XY_H_POS 3
#define PMW3610_SHUTTER_H_POS 5
#define PMW3610_SHUTTER_L_POS 6
struct bt_conn {int unused;};
struct bt_conn_info {int type,state;struct {uint16_t interval,latency;}le;};
#define BT_CONN_TYPE_LE 1
#define BT_CONN_STATE_CONNECTED 2
static int bt_conn_get_info(const struct bt_conn *c,struct bt_conn_info *i) {
 (void)c;*i=(struct bt_conn_info){.type=1,.state=2,.le={6,30}};return 0;
}
static void bt_conn_foreach(int t,void (*f)(struct bt_conn*,void*),void *d) {
 struct bt_conn c;(void)t;f(&c,d);
}
'''

TEST = r'''
static void check_actual_report(void) {
 struct pixart_data state={.ready=true};
 struct pixart_config config={.evt_type=2,.x_input_code=0,.y_input_code=1};
 struct device dev={.data=&state,.config=&config};
 reported_x=reported_y=0;rotation=(struct motion_rotation){0};api_result=0;dx=dy=0;
 // Actual driver's report timing, raw accumulation and output are exercised.
 for(int i=0;i<1000;i++) {
  now_ms=1000+i*12;assert(pmw3610_report_data(&dev)==0);
  assert(dx==0&&dy==0); // Even if rotation emitted zero pixels on this iteration.
 }
 assert(llabs(reported_x-(1000LL*PROFILE_COS/1048576))<=1);
 assert(llabs(reported_y-(1000LL*PROFILE_SIN/1048576))<=1);
 // Actual 4ms sampling through the 8/12ms gate: no pending counts disappear.
 reported_x=reported_y=0;rotation=(struct motion_rotation){0};dx=dy=0;
 for(int i=0;i<1000;i++){now_ms=20000+i*4;assert(pmw3610_report_data(&dev)==0);}
 fake_x=0;now_ms+=12;assert(pmw3610_report_data(&dev)==0);fake_x=1;
 assert(dx==0&&dy==0);
 assert(llabs(reported_x-(1000LL*PROFILE_COS/1048576))<=1);
 assert(llabs(reported_y-(1000LL*PROFILE_SIN/1048576))<=1);
 // Jitter/long gaps must not purge motion held by the rate limiter.
 reported_x=reported_y=0;rotation=(struct motion_rotation){0};dx=dy=0;
 now_ms=30000;assert(pmw3610_report_data(&dev)==0);
 now_ms=30004;assert(pmw3610_report_data(&dev)==0);
 now_ms=30028;assert(pmw3610_report_data(&dev)==0);
 now_ms=30032;assert(pmw3610_report_data(&dev)==0);
 fake_x=0;now_ms=30056;assert(pmw3610_report_data(&dev)==0);fake_x=1;
 assert(dx==0&&dy==0);
 assert(reported_x==4LL*PROFILE_COS/1048576&&reported_y==4LL*PROFILE_SIN/1048576);
}
static void check_rotation(void) {
 struct motion_rotation s={0};int16_t x,y;
 // Exact cardinal transforms, all sign combinations and zero.
 const int16_t values[]={INT16_MIN,-1000,-1,0,1,1000,INT16_MAX};
 for(unsigned i=0;i<7;i++)for(unsigned j=0;j<7;j++) {
  s=(struct motion_rotation){0};motion_rotate(&s,1048576,0,values[i],values[j],&x,&y);
  assert(x==values[i]&&y==values[j]);
 }
 s=(struct motion_rotation){0};motion_rotate(&s,0,1048576,12,-31,&x,&y);assert(x==31&&y==12);
 s=(struct motion_rotation){0};motion_rotate(&s,0,-1048576,12,-31,&x,&y);assert(x==-31&&y==-12);
 // Inverse-rotated cardinal input must align at either candidate angle.
 int16_t mount_sin=(1000LL*PROFILE_SIN+524288)/1048576;
 int16_t mount_cos=(1000LL*PROFILE_COS+524288)/1048576;
 s=(struct motion_rotation){0};motion_rotate(&s,PROFILE_COS,PROFILE_SIN,-mount_sin,-mount_cos,&x,&y);
 assert(x>=-1&&x<=1&&y>=-1001&&y<=-999);
 s=(struct motion_rotation){0};motion_rotate(&s,PROFILE_COS,PROFILE_SIN,mount_cos,-mount_sin,&x,&y);
 assert(y>=-1&&y<=1&&x>=999&&x<=1001);
 // Small slow steps retain their fractional cross-axis contribution.
 int64_t sum_x=0,sum_y=0;
 s=(struct motion_rotation){0};
 for(int i=0;i<10000;i++){motion_rotate(&s,PROFILE_COS,PROFILE_SIN,0,-1,&x,&y);sum_x+=x;sum_y+=y;}
 assert(llabs(sum_x-(10000LL*PROFILE_SIN/1048576))<=1);
 assert(llabs(sum_y-(-10000LL*PROFILE_COS/1048576))<=1);
 // Reversals cancel without a bias; saturating a large report leaves no backlog.
 for(int i=0;i<10000;i++){motion_rotate(&s,PROFILE_COS,PROFILE_SIN,0,1,&x,&y);sum_x+=x;sum_y+=y;}
 assert(sum_x==0&&sum_y==0);
 s=(struct motion_rotation){0};motion_rotate(&s,PROFILE_COS,PROFILE_SIN,32767,32767,&x,&y);
 assert(y==32767);motion_rotate(&s,PROFILE_COS,PROFILE_SIN,0,0,&x,&y);assert(x==0&&y==0);
}
int main(void) {
 check_rotation();
 struct pixart_data state={.ready=true,.async_init_step=4};struct device dev={.data=&state};
 pmw_profile_start(&dev);assert(scheduled==1);
 now_ms=10;pmw_profile_irq();now_ms=13;pmw_profile_work_start();
 pmw_profile_sample(-3,-10,20,45);now_ms=25;pmw_profile_sample(3,-5,0,80);
 assert(stats.samples==2&&stats.moving==2&&stats.x_sum==0&&stats.y_sum==-15);
 assert(stats.abs_x==6&&stats.abs_y==15&&stats.quality_min==0&&stats.quality_max==20);
 assert(stats.quality_sum==20&&stats.quality_zero==1&&stats.shutter_min==45&&stats.shutter_max==80);
 assert(stats.max_gap_ms==12&&stats.max_work_wait_ms==3);
 pmw_profile_spi_error();pmw_profile_wake_drop();
 cadence_frames=0;
 api_result=-12;assert(pmw_profile_input(&dev,2,0,4,true,0)==-12);assert(cadence_frames==0);
 assert(stats.input_errors==1&&stats.input_events==1&&stats.spi_errors==1&&stats.wake_drops==1);
 api_result=0;assert(pmw_profile_input(&dev,2,1,-4,true,0)==0);assert(stats.input_errors==1);assert(cadence_frames==1);
 report(NULL);assert(stats.samples==0&&stats.input_errors==0&&scheduled==2&&log_lines==4);
 char expected[100];snprintf(expected,sizeof(expected),"STATE ready=1 step=4 err=0 interval_ms=%d angle_deg=%d",CONFIG_PMW3610_ALT_REPORT_INTERVAL_MIN,PROFILE_ANGLE);
 assert(strstr(log_output,expected));
 assert(strstr(log_output,"sq=0/10/20 sq0=1 shutter=45/80"));
 assert(strstr(log_output,"input_events=2 input_err=1 spi_err=1 wake_drop=1"));
 state.ready=false;state.err=-5;report(NULL);assert(scheduled==3&&log_lines==8);
 check_actual_report();
 return 0;
}
'''


def main(angle=15):
    before = hashlib.sha256((SOURCE / 'src/pmw3610.c').read_bytes()).hexdigest()
    with tempfile.TemporaryDirectory(prefix='prospector-profile-') as tmp:
        tmp = Path(tmp)
        stage = tmp / 'driver'
        prepare.prepare(SOURCE, stage, angle)
        generated = (stage / 'src/pmw3610.c').read_text()
        assert 'LOG_DBG("x/y:' not in generated
        assert generated.count('pmw_profile_input(dev,') == 3
        assert 'pmw_profile_sample(x, y, buf[4]' in generated
        # Only this temporary host copy substitutes the driver's private state layout.
        (stage / 'src/pixart.h').write_text('#include "platform.h"\n')
        headers = ['zephyr/kernel.h', 'zephyr/logging/log.h', 'zephyr/device.h',
                   'zephyr/input/input.h', 'zephyr/bluetooth/conn.h', 'zephyr/sys/util.h', 'pixart.h',
                   'prospector/pipeline_profile.h']
        for header in headers:
            p = tmp / header
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text('#include "platform.h"\n')
        (tmp / 'platform.h').write_text(PLATFORM)
        report = generated.split('static int pmw3610_report_data(const struct device *dev) {', 1)[1]
        report = 'static int pmw3610_report_data(const struct device *dev) {' + report.split(
            'static void pmw3610_gpio_callback', 1)[0]
        mocks = r'''
static int64_t dx,dy;
static int drop_motion_bursts;
static int fake_x=1;
static int pmw3610_read(const struct device *dev,uint8_t addr,uint8_t *buf,uint8_t len) {
 (void)dev;assert(addr==0x12&&len==7);memset(buf,0,len);buf[1]=fake_x;buf[4]=20;return 0;
}
'''
        (tmp / 'test.c').write_text('#include <stdlib.h>\n'
                                  f'#include "{stage}/src/pmw3610_profile.c"\n' + mocks + report + TEST)
        for interval in [12,8]:
            (tmp / 'platform.h').write_text(PLATFORM.replace(
                'CONFIG_PMW3610_ALT_REPORT_INTERVAL_MIN 12',
                f'CONFIG_PMW3610_ALT_REPORT_INTERVAL_MIN {interval}'))
            subprocess.run(['cc', '-std=c11', '-Wall', '-Wextra', '-Wno-unused-parameter',
                            '-Wno-unused-variable', '-I', str(tmp), str(tmp / 'test.c'),
                            '-o', str(tmp / 'test')], check=True)
            subprocess.run([str(tmp / 'test')], check=True)
        unsafe = tmp / 'unmarked'
        unsafe.mkdir()
        try:
            prepare.prepare(SOURCE, unsafe, angle)
        except ValueError:
            pass
        else:
            raise AssertionError('Unmarked directory was overwritten')
    assert hashlib.sha256((SOURCE / 'src/pmw3610.c').read_bytes()).hexdigest() == before
    print(f'PASS ({angle} degrees): actual profile/rotation C; calibration, fractional motion, queue errors, '
          'quality windows, periodic state, safe staging, original driver preserved')


if __name__ == '__main__':
    main(15)
    main(40)
