#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "pico/stdlib.h"
#include "pico/unique_id.h"
#include "hardware/uart.h"

#include "hil_protocol.h"

#define FIRMWARE_VERSION "0.1.0"
#define SENSOR_UART uart0
#define SENSOR_UART_BAUD 115200u
#define SENSOR_UART_TX_PIN 0u
#define SENSOR_UART_RX_PIN 1u
#define DUT_ENABLE_PIN 10u
#define DUT_PWM_PIN 11u
#define DEFAULT_SOURCE_MV 12000
#define DEFAULT_LOAD_MA 2000
#define AMBIENT_TEMP_CC 2500

typedef enum { INJ_NONE, INJ_BUS, INJ_CURRENT, INJ_TEMP, INJ_BAD_CRC, INJ_DROPOUT, INJ_REPEAT_SEQ, INJ_FROZEN } injection_t;

static uint16_t source_mv = DEFAULT_SOURCE_MV;
static uint16_t scripted_load_ma = DEFAULT_LOAD_MA;
static uint16_t plant_bus_mv = DEFAULT_SOURCE_MV;
static uint16_t plant_current_ma = 0;
static int16_t plant_temp_cc = AMBIENT_TEMP_CC;
static uint16_t sequence = 0;
static injection_t injection = INJ_NONE;
static int32_t injection_value = 0;
static hil_sensor_frame_t frozen_frame;
static bool have_frozen_frame = false;
static char usb_line[160];
static size_t usb_line_len = 0;
static uint32_t last_step_ms = 0;
static uint32_t last_telemetry_ms = 0;
static volatile uint32_t pwm_rise_us = 0, pwm_period_us = 0, pwm_high_us = 0;

static void pwm_edge_callback(uint gpio, uint32_t events) {
    (void)gpio; (void)events; uint32_t now = time_us_32();
    if (gpio_get(DUT_PWM_PIN)) { if (pwm_rise_us != 0) pwm_period_us = now - pwm_rise_us; pwm_rise_us = now; }
    else if (pwm_rise_us != 0) pwm_high_us = now - pwm_rise_us;
}
static uint8_t measured_pwm_percent(void) {
    uint32_t period = pwm_period_us, high = pwm_high_us; if (period == 0) return 0;
    uint32_t pct = (high * 100u + period / 2u) / period; return (uint8_t)(pct > 100u ? 100u : pct);
}
static const char *injection_name(void) {
    switch (injection) { case INJ_NONE:return "NONE"; case INJ_BUS:return "BUS"; case INJ_CURRENT:return "CURRENT"; case INJ_TEMP:return "TEMP"; case INJ_BAD_CRC:return "BAD_CRC"; case INJ_DROPOUT:return "DROPOUT"; case INJ_REPEAT_SEQ:return "REPEAT_SEQ"; case INJ_FROZEN:return "FROZEN"; }
    return "UNKNOWN";
}
static void plant_step(void) {
    bool enable = gpio_get(DUT_ENABLE_PIN); uint8_t fan = measured_pwm_percent();
    plant_current_ma = enable ? scripted_load_ma : 0u;
    uint32_t droop = ((uint32_t)plant_current_ma * 50u) / 1000u; plant_bus_mv = source_mv > droop ? (uint16_t)(source_mv - droop) : 0u;
    int32_t heating = plant_current_ma / 500u; int32_t fan_cooling = fan / 20u; int32_t passive = plant_temp_cc > AMBIENT_TEMP_CC ? (plant_temp_cc - AMBIENT_TEMP_CC) / 1000 : 0;
    int32_t next_temp = plant_temp_cc + heating - fan_cooling - passive; if (next_temp < AMBIENT_TEMP_CC) next_temp = AMBIENT_TEMP_CC; if (next_temp > 32767) next_temp = 32767; plant_temp_cc = (int16_t)next_temp;
}
static void send_sensor_frame(void) {
    if (injection == INJ_DROPOUT) return;
    hil_sensor_frame_t f = {.sequence=sequence,.bus_mv=plant_bus_mv,.current_ma=plant_current_ma,.temperature_cc=plant_temp_cc,.flags=0};
    if (injection == INJ_BUS) f.bus_mv = (uint16_t)injection_value;
    else if (injection == INJ_CURRENT) f.current_ma = (uint16_t)injection_value;
    else if (injection == INJ_TEMP) f.temperature_cc = (int16_t)injection_value;
    else if (injection == INJ_FROZEN && have_frozen_frame) f = frozen_frame;
    uint8_t raw[HIL_FRAME_SIZE]; hil_encode_sensor_frame(&f, raw); if (injection == INJ_BAD_CRC) raw[13] ^= 0x01u;
    uart_write_blocking(SENSOR_UART, raw, HIL_FRAME_SIZE);
    if (injection != INJ_REPEAT_SEQ && injection != INJ_FROZEN) sequence++;
    if (!have_frozen_frame) { frozen_frame = f; have_frozen_frame = true; }
}
static void reset_hil(void) {
    source_mv=DEFAULT_SOURCE_MV; scripted_load_ma=DEFAULT_LOAD_MA; plant_bus_mv=DEFAULT_SOURCE_MV; plant_current_ma=0; plant_temp_cc=AMBIENT_TEMP_CC; sequence=0; injection=INJ_NONE; injection_value=0; have_frozen_frame=false;
}
static void print_identity(void) {
    char id[2 * PICO_UNIQUE_BOARD_ID_SIZE_BYTES + 1]; pico_get_unique_board_id_string(id, sizeof(id));
    printf("{\"type\":\"id\",\"ok\":true,\"protocol_version\":%d,\"role\":\"hil\",\"firmware_version\":\"%s\",\"board_id\":\"%s\"}\n", HIL_PROTOCOL_VERSION,FIRMWARE_VERSION,id);
}
static void print_status(void) {
    printf("{\"type\":\"status\",\"ok\":true,\"bus_mv\":%u,\"current_ma\":%u,\"temperature_cc\":%d,\"enable_observed\":%s,\"fan_percent_observed\":%u,\"sequence\":%u,\"fault_injection\":\"%s\"}\n",
           plant_bus_mv,plant_current_ma,plant_temp_cc,gpio_get(DUT_ENABLE_PIN)?"true":"false",measured_pwm_percent(),sequence,injection_name());
}
static bool set_fault_command(const char *kind, int32_t value) {
    if (strcmp(kind,"OVERVOLTAGE")==0 || strcmp(kind,"UNDERVOLTAGE")==0 || strcmp(kind,"BUS")==0) injection=INJ_BUS;
    else if (strcmp(kind,"OVERCURRENT")==0 || strcmp(kind,"CURRENT")==0) injection=INJ_CURRENT;
    else if (strcmp(kind,"OVERTEMPERATURE")==0 || strcmp(kind,"TEMP")==0) injection=INJ_TEMP;
    else if (strcmp(kind,"BAD_CRC")==0 || strcmp(kind,"CRC")==0) injection=INJ_BAD_CRC;
    else if (strcmp(kind,"DROPOUT")==0) injection=INJ_DROPOUT;
    else if (strcmp(kind,"REPEAT_SEQ")==0) injection=INJ_REPEAT_SEQ;
    else if (strcmp(kind,"FROZEN")==0) { injection=INJ_FROZEN; frozen_frame=(hil_sensor_frame_t){sequence,plant_bus_mv,plant_current_ma,plant_temp_cc,0}; have_frozen_frame=true; }
    else return false;
    injection_value=value; return true;
}
static void handle_usb_command(char *line) {
    if (strcmp(line,"ID?")==0) { print_identity(); return; }
    if (strcmp(line,"PING")==0) { printf("{\"type\":\"ack\",\"ok\":true,\"cmd\":\"PING\"}\n"); return; }
    if (strcmp(line,"STATUS?")==0) { print_status(); return; }
    if (strcmp(line,"RESET")==0) { reset_hil(); printf("{\"type\":\"ack\",\"ok\":true,\"cmd\":\"RESET\"}\n"); return; }
    if (strcmp(line,"FAULT CLEAR")==0) { injection=INJ_NONE; injection_value=0; printf("{\"type\":\"ack\",\"ok\":true,\"cmd\":\"FAULT CLEAR\"}\n"); return; }
    char kind[32]; long value;
    if (sscanf(line,"FAULT SET %31s %ld",kind,&value)==2) {
        if (set_fault_command(kind,(int32_t)value)) printf("{\"type\":\"ack\",\"ok\":true,\"cmd\":\"FAULT SET\",\"fault\":\"%s\"}\n",kind);
        else printf("{\"type\":\"error\",\"ok\":false,\"code\":\"BAD_ARGUMENT\",\"message\":\"unknown fault\"}\n"); return;
    }
    unsigned long load;
    if (sscanf(line,"LOAD %lu",&load)==1 && load <= 65535u) { scripted_load_ma=(uint16_t)load; printf("{\"type\":\"ack\",\"ok\":true,\"cmd\":\"LOAD\",\"milliamps\":%u}\n",scripted_load_ma); return; }
    unsigned long source;
    if (sscanf(line,"SOURCE %lu",&source)==1 && source <= 65535u) { source_mv=(uint16_t)source; printf("{\"type\":\"ack\",\"ok\":true,\"cmd\":\"SOURCE\",\"millivolts\":%u}\n",source_mv); return; }
    printf("{\"type\":\"error\",\"ok\":false,\"code\":\"BAD_COMMAND\",\"message\":\"unsupported command\"}\n");
}
static void poll_usb_commands(void) {
    int c; while ((c=getchar_timeout_us(0)) != PICO_ERROR_TIMEOUT) {
        if (c=='\n') { usb_line[usb_line_len]='\0'; if (usb_line_len) handle_usb_command(usb_line); usb_line_len=0; stdio_flush(); }
        else if (c!='\r' && usb_line_len+1<sizeof(usb_line)) usb_line[usb_line_len++]=(char)c;
    }
}
int main(void) {
    stdio_init_all(); uart_init(SENSOR_UART,SENSOR_UART_BAUD); gpio_set_function(SENSOR_UART_TX_PIN,GPIO_FUNC_UART); gpio_set_function(SENSOR_UART_RX_PIN,GPIO_FUNC_UART); uart_set_format(SENSOR_UART,8,1,UART_PARITY_NONE);
    gpio_init(DUT_ENABLE_PIN); gpio_set_dir(DUT_ENABLE_PIN,GPIO_IN); gpio_pull_down(DUT_ENABLE_PIN);
    gpio_init(DUT_PWM_PIN); gpio_set_dir(DUT_PWM_PIN,GPIO_IN); gpio_pull_down(DUT_PWM_PIN); gpio_set_irq_enabled_with_callback(DUT_PWM_PIN,GPIO_IRQ_EDGE_RISE|GPIO_IRQ_EDGE_FALL,true,&pwm_edge_callback);
    reset_hil(); sleep_ms(500);
    while (true) {
        uint32_t now=to_ms_since_boot(get_absolute_time()); poll_usb_commands();
        if ((uint32_t)(now-last_step_ms)>=HIL_SENSOR_PERIOD_MS) { last_step_ms=now; plant_step(); send_sensor_frame(); }
        if ((uint32_t)(now-last_telemetry_ms)>=200u) { last_telemetry_ms=now; print_status(); stdio_flush(); }
        tight_loop_contents();
    }
}
