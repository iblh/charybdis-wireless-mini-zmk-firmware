/* SPDX-License-Identifier: MIT */
#pragma once
#include <stdint.h>
#include <limits.h>

#define MOTION_Q 1048576LL
struct motion_rotation { int64_t remainder_x, remainder_y; };

/* Positive angle rotates clockwise in screen coordinates (Y points down).
 * Preserve fractions across small reports; never feed saturation back as motion. */
static inline int16_t motion_quantize(int64_t value, int64_t *remainder) {
    int64_t integer = value / MOTION_Q;
    *remainder = value - integer * MOTION_Q;
    if (integer > INT16_MAX) return INT16_MAX;
    if (integer < INT16_MIN) return INT16_MIN;
    return (int16_t)integer;
}

static inline void motion_rotate(struct motion_rotation *state, int32_t cosine, int32_t sine,
                                 int16_t x, int16_t y, int16_t *out_x, int16_t *out_y) {
    int64_t nx = (int64_t)x * cosine - (int64_t)y * sine + state->remainder_x;
    int64_t ny = (int64_t)x * sine + (int64_t)y * cosine + state->remainder_y;
    *out_x = motion_quantize(nx, &state->remainder_x);
    *out_y = motion_quantize(ny, &state->remainder_y);
}
