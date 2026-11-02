/* SPDX-License-Identifier: MIT
 * Temporary single-sensor diagnostics. No SPI reads from the logging worker.
 * All quality samples come from the driver's existing motion burst. */
#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>
#include <zephyr/bluetooth/conn.h>
#include <zephyr/sys/util.h>
#include "pixart.h"
#include "pmw3610_profile.h"
#include "motion_math.h"
#include "profile_coeffs.h"
#if defined(CONFIG_PROSPECTOR_PIPELINE_CADENCE)
#include <prospector/pipeline_profile.h>
#endif

LOG_MODULE_REGISTER(pmw_profile, LOG_LEVEL_INF);
BUILD_ASSERT(DT_NUM_INST_STATUS_OKAY(pixart_pmw3610_alt) == 1,
             "Profile supports exactly one sensor");

struct profile_stats {
    uint32_t samples, moving, quality_sum, quality_zero, spi_errors, input_errors;
    uint32_t input_events, wake_drops, max_gap_ms, max_work_wait_ms;
    int64_t x_sum, y_sum;
    uint32_t abs_x, abs_y;
    uint16_t shutter_min, shutter_max;
    uint8_t quality_min, quality_max;
};
static struct profile_stats stats;
static struct k_spinlock lock;
static const struct device *sensor;
static int64_t last_sample_ms, irq_ms;
static bool have_last_sample, have_irq;
static struct motion_rotation rotation;

void pmw_profile_irq(void) {
    k_spinlock_key_t key = k_spin_lock(&lock);
    irq_ms = k_uptime_get(); have_irq = true;
    k_spin_unlock(&lock, key);
}

void pmw_profile_work_start(void) {
    k_spinlock_key_t key = k_spin_lock(&lock);
    if (have_irq) {
        stats.max_work_wait_ms = MAX(stats.max_work_wait_ms, k_uptime_get() - irq_ms);
        have_irq = false;
    }
    k_spin_unlock(&lock, key);
}

void pmw_profile_sample(int16_t x, int16_t y, uint8_t quality, uint16_t shutter) {
    int64_t now = k_uptime_get();
    k_spinlock_key_t key = k_spin_lock(&lock);
    if (stats.samples == 0) {
        stats.quality_min = quality; stats.shutter_min = shutter;
    }
    stats.samples++;
    stats.moving += x != 0 || y != 0;
    stats.x_sum += x; stats.y_sum += y;
    stats.abs_x += x < 0 ? -(int32_t)x : x;
    stats.abs_y += y < 0 ? -(int32_t)y : y;
    stats.quality_sum += quality; stats.quality_zero += quality == 0;
    stats.quality_min = MIN(stats.quality_min, quality);
    stats.quality_max = MAX(stats.quality_max, quality);
    stats.shutter_min = MIN(stats.shutter_min, shutter);
    stats.shutter_max = MAX(stats.shutter_max, shutter);
    if (have_last_sample) stats.max_gap_ms = MAX(stats.max_gap_ms, now - last_sample_ms);
    last_sample_ms = now; have_last_sample = true;
    k_spin_unlock(&lock, key);
}

void pmw_profile_spi_error(void) {
    k_spinlock_key_t key = k_spin_lock(&lock);
    stats.spi_errors++;
    k_spin_unlock(&lock, key);
}
void pmw_profile_wake_drop(void) {
    k_spinlock_key_t key = k_spin_lock(&lock);
    stats.wake_drops++;
    k_spin_unlock(&lock, key);
}

void pmw_profile_rotate(int16_t *x, int16_t *y) {
    motion_rotate(&rotation, PROFILE_COS, PROFILE_SIN, *x, *y, x, y);
}

int pmw_profile_input(const struct device *dev, uint8_t type, uint16_t code,
                      int32_t value, bool sync, k_timeout_t timeout) {
    int result = input_report(dev, type, code, value, sync, timeout);
#if defined(CONFIG_PROSPECTOR_PIPELINE_CADENCE)
    if (!result && sync) pipe_cadence(PIPE_CADENCE_PMW);
#endif
    k_spinlock_key_t key = k_spin_lock(&lock);
    stats.input_events++; stats.input_errors += result < 0;
    k_spin_unlock(&lock, key);
    return result;
}

static void report_link(struct bt_conn *conn, void *data) {
    struct bt_conn_info info;
    if (!bt_conn_get_info(conn, &info) && info.type == BT_CONN_TYPE_LE &&
        info.state == BT_CONN_STATE_CONNECTED) {
        LOG_INF("LINK interval_us=%u latency=%u", (unsigned)info.le.interval * 1250U,
                info.le.latency);
    }
}

static void report(struct k_work *work);
K_WORK_DELAYABLE_DEFINE(report_work, report);
static void report(struct k_work *work) {
    struct profile_stats snapshot;
    k_spinlock_key_t key = k_spin_lock(&lock);
    snapshot = stats;
    stats = (struct profile_stats){0};
    k_spin_unlock(&lock, key);
    const struct pixart_data *state = sensor->data;
    LOG_INF("STATE ready=%d step=%d err=%d interval_ms=%d angle_deg=%d",
            state->ready, state->async_init_step, state->err,
            CONFIG_PMW3610_ALT_REPORT_INTERVAL_MIN, PROFILE_ANGLE);
    LOG_INF("RAW n=%u moving=%u sum=%lld/%lld abs=%u/%u sq=%u/%u/%u sq0=%u shutter=%u/%u",
            snapshot.samples, snapshot.moving, (long long)snapshot.x_sum,
            (long long)snapshot.y_sum, snapshot.abs_x, snapshot.abs_y,
            snapshot.quality_min,
            snapshot.samples ? snapshot.quality_sum / snapshot.samples : 0,
            snapshot.quality_max, snapshot.quality_zero,
            snapshot.shutter_min, snapshot.shutter_max);
    LOG_INF("PIPE input_events=%u input_err=%u spi_err=%u wake_drop=%u gap_ms=%u work_wait_ms=%u",
            snapshot.input_events, snapshot.input_errors, snapshot.spi_errors,
            snapshot.wake_drops, snapshot.max_gap_ms, snapshot.max_work_wait_ms);
    bt_conn_foreach(BT_CONN_TYPE_LE, report_link, NULL);
    k_work_reschedule(&report_work, K_SECONDS(2));
}

void pmw_profile_start(const struct device *dev) {
    sensor = dev;
    k_work_reschedule(&report_work, K_SECONDS(2));
}
