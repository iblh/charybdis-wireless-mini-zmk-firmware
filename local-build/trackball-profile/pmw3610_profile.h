/* SPDX-License-Identifier: MIT */
#pragma once
#include <zephyr/device.h>
#include <zephyr/input/input.h>
#include <stdint.h>
void pmw_profile_start(const struct device *dev);
void pmw_profile_irq(void);
void pmw_profile_work_start(void);
void pmw_profile_sample(int16_t x, int16_t y, uint8_t quality, uint16_t shutter);
void pmw_profile_spi_error(void);
void pmw_profile_wake_drop(void);
void pmw_profile_rotate(int16_t *x, int16_t *y);
int pmw_profile_input(const struct device *dev, uint8_t type, uint16_t code,
                      int32_t value, bool sync, k_timeout_t timeout);
