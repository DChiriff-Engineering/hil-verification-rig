#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "pico/stdlib.h"
#include "pico/unique_id.h"
#include "hardware/pwm.h"
#include "hardware/uart.h"

#include "hil_protocol.h"

#define FIRMWARE_VERSION "0.1.0"
#define SENSOR_UART uart0
#define SENSOR_UART_BAUD 115200u
#define SENSOR_UART_TX_PIN 0u
#define SENSOR_UART_RX_PIN 1u
#define ENABLE_PIN 10u
#define FAN_PWM_PIN 11u
#define FAULT_STATUS_PIN 12u
#define FAN_PWM_WRAP 999u
#define FAN_PWM_CLKDIV 6.25f

typedef enum { STATE_STARTUP, STATE_NORMAL, STATE_DERATE, STATE_FAULT, STATE_RECOVERY } dut_state_t;
typedef enum {
    FAULT_NONE, FAULT_OVERVOLTAGE, FAULT_OVERCURRENT, FAULT_OVERTEMPERATURE,
    FAULT_SENSOR_TIMEOUT, FAULT_DATA_INTEGRITY, FAULT_STALE_SEQUENCE, FAULT_IMPLAUSIBLE_SLEW
} fault_reason_t;

typedef struct {
    uint32_t bad_frames, stale_sequences, timeouts, overvoltage, overcurrent, overtemperature, implausible_slew, recoveries, resets;
} counters_t;

static dut_state_t state = STATE_STARTUP;
static fault_reason_t fault_reason = FAULT_NONE;
static counters_t counters;
static bool enable_cmd = false;
static uint8_t fan_percent = 0;
static uint32_t last_valid_ms = 0;
static bool have_valid_frame = false;
static uint16_t last_sequence = 0;
static bool have_sequence = false;
static hil_sensor_frame_t last_frame;
static bool have_last_frame = false;
static uint8_t invalid_count = 0;
static uint8_t severe_oc_count = 0;
static uint32_t recovery_start_ms = 0;
static bool recovery_timer_active = false;
static uint8_t rx_frame[HIL_FRAME_SIZE];
static size_t rx_index = 0;
static char usb_line[160];
static size_t usb_line_len = 0;
static uint32_t last_telemetry_ms = 0;

static const char *state_name(dut_state_t s) {
    switch (s) { case STATE_STARTUP:return "STARTUP"; case STATE_NORMAL:return "NORMAL"; case STATE_DERATE:return "DERATE"; case STATE_FAULT:return "FAULT"; case STATE_RECOVERY:return "RECOVERY"; }
    return "UNKNOWN";
}
static const char *fault_name(fault_reason_t f) {
    switch (f) {
        case FAULT_NONE:return "NONE"; case FAULT_OVERVOLTAGE:return "OVERVOLTAGE"; case FAULT_OVERCURRENT:return "OVERCURRENT";
        case FAULT_OVERTEMPERATURE:return "OVERTEMPERATURE"; case FAULT_SENSOR_TIMEOUT:return "SENSOR_TIMEOUT";
        case FAULT_DATA_INTEGRITY:return "DATA_INTEGRITY"; case FAULT_STALE_SEQUENCE:return "STALE_SEQUENCE";
        case FAULT_IMPLAUSIBLE_SLEW:return "IMPLAUSIBLE_SLEW";
    }
    return "UNKNOWN";
}

static void apply_outputs(void) {
    gpio_put(ENABLE_PIN, enable_cmd);
    gpio_put(FAULT_STATUS_PIN, state == STATE_FAULT || state == STATE_RECOVERY);
    uint slice = pwm_gpio_to_slice_num(FAN_PWM_PIN);
    uint16_t level = (uint16_t)(((uint32_t)(FAN_PWM_WRAP + 1u) * fan_percent) / 100u);
    if (level > FAN_PWM_WRAP) level = FAN_PWM_WRAP;
    pwm_set_gpio_level(FAN_PWM_PIN, level);
}

static void set_fault(fault_reason_t reason) {
    if (state != STATE_FAULT || fault_reason != reason) {
        if (reason == FAULT_OVERVOLTAGE) counters.overvoltage++;
        else if (reason == FAULT_OVERCURRENT) counters.overcurrent++;
        else if (reason == FAULT_OVERTEMPERATURE) counters.overtemperature++;
        else if (reason == FAULT_IMPLAUSIBLE_SLEW) counters.implausible_slew++;
    }
    state = STATE_FAULT; fault_reason = reason; enable_cmd = false; fan_percent = 100; recovery_timer_active = false;
    apply_outputs();
}

static bool recovery_healthy(const hil_sensor_frame_t *f) {
    return f->bus_mv >= HIL_RECOVERY_MIN_MV && f->bus_mv < HIL_OV_MV && f->current_ma < HIL_OC_WARN_MA && f->temperature_cc < HIL_TEMP_DERATE_CC;
}

static bool implausible_slew(const hil_sensor_frame_t *f) {
    if (!have_last_frame) return false;
    int32_t dv = (int32_t)f->bus_mv - (int32_t)last_frame.bus_mv; if (dv < 0) dv = -dv;
    int32_t di = (int32_t)f->current_ma - (int32_t)last_frame.current_ma; if (di < 0) di = -di;
    int32_t dt = (int32_t)f->temperature_cc - (int32_t)last_frame.temperature_cc; if (dt < 0) dt = -dt;
    bool bus_bad = f->bus_mv < HIL_OV_MV && dv > HIL_MAX_BUS_SLEW_MV;
    bool current_bad = f->current_ma < HIL_OC_SEVERE_MA && di > HIL_MAX_CURRENT_SLEW_MA;
    bool temp_bad = f->temperature_cc < HIL_TEMP_SEVERE_CC && dt > HIL_MAX_TEMP_SLEW_CC;
    return bus_bad || current_bad || temp_bad;
}

static void evaluate_valid_frame(const hil_sensor_frame_t *f, uint32_t now_ms) {
    if (f->bus_mv >= HIL_OV_MV) { set_fault(FAULT_OVERVOLTAGE); return; }
    if (f->temperature_cc >= HIL_TEMP_SEVERE_CC) { set_fault(FAULT_OVERTEMPERATURE); return; }
    severe_oc_count = f->current_ma >= HIL_OC_SEVERE_MA ? (uint8_t)(severe_oc_count + 1u) : 0u;
    if (severe_oc_count >= HIL_OC_SEVERE_SAMPLES) { set_fault(FAULT_OVERCURRENT); return; }
    if (implausible_slew(f)) { set_fault(FAULT_IMPLAUSIBLE_SLEW); return; }

    if (state == STATE_FAULT || state == STATE_RECOVERY) {
        if (!recovery_healthy(f)) {
            state = STATE_FAULT; enable_cmd = false; fan_percent = 100; recovery_timer_active = false; apply_outputs(); return;
        }
        if (state == STATE_FAULT) { state = STATE_RECOVERY; recovery_start_ms = now_ms; recovery_timer_active = true; }
        else if (recovery_timer_active && (uint32_t)(now_ms - recovery_start_ms) >= HIL_RECOVERY_DWELL_MS) {
            state = STATE_NORMAL; fault_reason = FAULT_NONE; enable_cmd = true; fan_percent = 25; recovery_timer_active = false; counters.recoveries++;
        }
        apply_outputs(); return;
    }

    bool derate = f->bus_mv < HIL_UV_MV || f->current_ma >= HIL_OC_WARN_MA || f->temperature_cc >= HIL_TEMP_DERATE_CC;
    state = derate ? STATE_DERATE : STATE_NORMAL; fault_reason = FAULT_NONE; enable_cmd = true;
    if (f->temperature_cc >= HIL_TEMP_DERATE_CC) {
        int32_t delta = (int32_t)f->temperature_cc - HIL_TEMP_DERATE_CC;
        int32_t span = HIL_TEMP_SEVERE_CC - HIL_TEMP_DERATE_CC;
        int32_t percent = 40 + (delta * 60) / span; if (percent > 100) percent = 100; fan_percent = (uint8_t)percent;
    } else if (f->current_ma >= HIL_OC_WARN_MA || f->bus_mv < HIL_UV_MV) fan_percent = 70;
    else fan_percent = 25;
    apply_outputs();
}

static void process_complete_frame(const uint8_t raw[HIL_FRAME_SIZE], uint32_t now_ms) {
    hil_sensor_frame_t f;
    if (!hil_decode_sensor_frame(raw, &f)) {
        counters.bad_frames++; invalid_count++; if (invalid_count >= HIL_INVALID_LIMIT) set_fault(FAULT_DATA_INTEGRITY); return;
    }
    if (have_sequence) {
        uint16_t delta = (uint16_t)(f.sequence - last_sequence);
        if (delta == 0u || delta > 0x7fffu) {
            counters.stale_sequences++; invalid_count++; if (invalid_count >= HIL_INVALID_LIMIT) set_fault(FAULT_STALE_SEQUENCE); return;
        }
    }
    invalid_count = 0; last_sequence = f.sequence; have_sequence = true; last_valid_ms = now_ms; have_valid_frame = true;
    evaluate_valid_frame(&f, now_ms);
    last_frame = f; have_last_frame = true;
}

static void poll_sensor_uart(uint32_t now_ms) {
    while (uart_is_readable(SENSOR_UART)) {
        uint8_t byte = uart_getc(SENSOR_UART);
        if (rx_index == 0) { if (byte == 0x5au) rx_frame[rx_index++] = byte; continue; }
        if (rx_index == 1) {
            if (byte == 0xa5u) rx_frame[rx_index++] = byte;
            else rx_index = byte == 0x5au ? 1u : 0u;
            continue;
        }
        rx_frame[rx_index++] = byte;
        if (rx_index == HIL_FRAME_SIZE) { process_complete_frame(rx_frame, now_ms); rx_index = 0; }
    }
}

static void controller_reset(void) {
    memset(&counters, 0, sizeof(counters)); counters.resets = 1;
    state = STATE_STARTUP; fault_reason = FAULT_NONE; enable_cmd = false; fan_percent = 0;
    have_valid_frame = false; have_sequence = false; have_last_frame = false; invalid_count = 0; severe_oc_count = 0; recovery_timer_active = false; rx_index = 0;
    apply_outputs();
}

static void print_identity(void) {
    char id[2 * PICO_UNIQUE_BOARD_ID_SIZE_BYTES + 1]; pico_get_unique_board_id_string(id, sizeof(id));
    printf("{\"type\":\"id\",\"ok\":true,\"protocol_version\":%d,\"role\":\"dut\",\"firmware_version\":\"%s\",\"board_id\":\"%s\"}\n", HIL_PROTOCOL_VERSION, FIRMWARE_VERSION, id);
}
static void print_status(const char *type) {
    printf("{\"type\":\"%s\",\"ok\":true,\"state\":\"%s\",\"fault\":\"%s\",\"enable\":%s,\"fan_percent\":%u,\"bad_frames\":%lu,\"stale_sequences\":%lu,\"timeouts\":%lu}\n",
           type, state_name(state), fault_name(fault_reason), enable_cmd ? "true" : "false", fan_percent,
           (unsigned long)counters.bad_frames, (unsigned long)counters.stale_sequences, (unsigned long)counters.timeouts);
}
static void handle_usb_command(char *line) {
    if (strcmp(line, "ID?") == 0) print_identity();
    else if (strcmp(line, "PING") == 0) printf("{\"type\":\"ack\",\"ok\":true,\"cmd\":\"PING\"}\n");
    else if (strcmp(line, "STATUS?") == 0) print_status("status");
    else if (strcmp(line, "RESET") == 0) { controller_reset(); printf("{\"type\":\"ack\",\"ok\":true,\"cmd\":\"RESET\"}\n"); }
    else printf("{\"type\":\"error\",\"ok\":false,\"code\":\"BAD_COMMAND\",\"message\":\"unsupported command\"}\n");
    stdio_flush();
}
static void poll_usb_commands(void) {
    int c;
    while ((c = getchar_timeout_us(0)) != PICO_ERROR_TIMEOUT) {
        if (c == '\n') { usb_line[usb_line_len] = '\0'; if (usb_line_len) handle_usb_command(usb_line); usb_line_len = 0; }
        else if (c != '\r' && usb_line_len + 1 < sizeof(usb_line)) usb_line[usb_line_len++] = (char)c;
    }
}

int main(void) {
    stdio_init_all();
    uart_init(SENSOR_UART, SENSOR_UART_BAUD); gpio_set_function(SENSOR_UART_TX_PIN, GPIO_FUNC_UART); gpio_set_function(SENSOR_UART_RX_PIN, GPIO_FUNC_UART); uart_set_format(SENSOR_UART, 8, 1, UART_PARITY_NONE); uart_set_fifo_enabled(SENSOR_UART, true);
    gpio_init(ENABLE_PIN); gpio_set_dir(ENABLE_PIN, GPIO_OUT); gpio_init(FAULT_STATUS_PIN); gpio_set_dir(FAULT_STATUS_PIN, GPIO_OUT);
    gpio_set_function(FAN_PWM_PIN, GPIO_FUNC_PWM); uint slice = pwm_gpio_to_slice_num(FAN_PWM_PIN); pwm_config cfg = pwm_get_default_config(); pwm_config_set_clkdiv(&cfg, FAN_PWM_CLKDIV); pwm_config_set_wrap(&cfg, FAN_PWM_WRAP); pwm_init(slice, &cfg, true);
    controller_reset(); sleep_ms(500);
    while (true) {
        uint32_t now_ms = to_ms_since_boot(get_absolute_time());
        poll_sensor_uart(now_ms); poll_usb_commands();
        if (have_valid_frame && (uint32_t)(now_ms - last_valid_ms) > HIL_SENSOR_TIMEOUT_MS && !(state == STATE_FAULT && fault_reason == FAULT_SENSOR_TIMEOUT)) { counters.timeouts++; set_fault(FAULT_SENSOR_TIMEOUT); }
        if ((uint32_t)(now_ms - last_telemetry_ms) >= 200u) { last_telemetry_ms = now_ms; print_status("telemetry"); stdio_flush(); }
        tight_loop_contents();
    }
}
