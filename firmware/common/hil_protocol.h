#ifndef HIL_PROTOCOL_H
#define HIL_PROTOCOL_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#define HIL_SYNC_WORD 0xA55Au
#define HIL_PROTOCOL_VERSION 1
#define HIL_FRAME_SIZE 14u
#define HIL_SENSOR_PERIOD_MS 50

#define HIL_UV_MV 10500
#define HIL_RECOVERY_MIN_MV 10800
#define HIL_OV_MV 14500
#define HIL_OC_WARN_MA 4500
#define HIL_OC_SEVERE_MA 6000
#define HIL_OC_SEVERE_SAMPLES 3
#define HIL_TEMP_DERATE_CC 7000
#define HIL_TEMP_SEVERE_CC 8500
#define HIL_SENSOR_TIMEOUT_MS 250
#define HIL_RECOVERY_DWELL_MS 1000
#define HIL_INVALID_LIMIT 3

#define HIL_MAX_BUS_SLEW_MV 3000
#define HIL_MAX_CURRENT_SLEW_MA 4000
#define HIL_MAX_TEMP_SLEW_CC 1500

#define HIL_FLAG_NONE 0u

typedef struct {
    uint16_t sequence;
    uint16_t bus_mv;
    uint16_t current_ma;
    int16_t temperature_cc;
    uint8_t flags;
} hil_sensor_frame_t;

static inline uint16_t hil_get_u16_le(const uint8_t *p) {
    return (uint16_t)p[0] | ((uint16_t)p[1] << 8);
}

static inline void hil_put_u16_le(uint8_t *p, uint16_t value) {
    p[0] = (uint8_t)(value & 0xffu);
    p[1] = (uint8_t)(value >> 8);
}

static inline uint16_t hil_crc16_ccitt_false(const uint8_t *data, size_t length) {
    uint16_t crc = 0xffffu;
    for (size_t i = 0; i < length; ++i) {
        crc ^= (uint16_t)data[i] << 8;
        for (unsigned bit = 0; bit < 8; ++bit) {
            crc = (crc & 0x8000u) ? (uint16_t)((crc << 1) ^ 0x1021u) : (uint16_t)(crc << 1);
        }
    }
    return crc;
}

static inline void hil_encode_sensor_frame(const hil_sensor_frame_t *frame, uint8_t out[HIL_FRAME_SIZE]) {
    hil_put_u16_le(&out[0], HIL_SYNC_WORD);
    out[2] = HIL_PROTOCOL_VERSION;
    out[3] = frame->flags;
    hil_put_u16_le(&out[4], frame->sequence);
    hil_put_u16_le(&out[6], frame->bus_mv);
    hil_put_u16_le(&out[8], frame->current_ma);
    hil_put_u16_le(&out[10], (uint16_t)frame->temperature_cc);
    hil_put_u16_le(&out[12], hil_crc16_ccitt_false(out, 12u));
}

static inline bool hil_decode_sensor_frame(const uint8_t in[HIL_FRAME_SIZE], hil_sensor_frame_t *frame) {
    if (hil_get_u16_le(&in[0]) != HIL_SYNC_WORD || in[2] != HIL_PROTOCOL_VERSION) return false;
    if (hil_get_u16_le(&in[12]) != hil_crc16_ccitt_false(in, 12u)) return false;
    frame->flags = in[3];
    frame->sequence = hil_get_u16_le(&in[4]);
    frame->bus_mv = hil_get_u16_le(&in[6]);
    frame->current_ma = hil_get_u16_le(&in[8]);
    frame->temperature_cc = (int16_t)hil_get_u16_le(&in[10]);
    return true;
}

#endif
