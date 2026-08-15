#include <Arduino.h>

static const char *FIRMWARE_VERSION = "0.1.0";
static const uint32_t SERIAL_BAUD = 115200;
static const uint8_t ENABLE_OBSERVE_PIN = A0;
static const uint8_t FAULT_OBSERVE_PIN = A1;
static const int HIGH_THRESHOLD_CODE = 400;
static bool streamEnabled = false;
static uint32_t lastStreamMs = 0;

static void identity() {
  Serial.print(F("{\"type\":\"id\",\"ok\":true,\"protocol_version\":1,\"role\":\"witness\",\"firmware_version\":\""));
  Serial.print(FIRMWARE_VERSION);
  Serial.println(F("\",\"board_id\":\"UNO-REV3\"}"));
}

static void sample() {
  const int enableCode = analogRead(ENABLE_OBSERVE_PIN);
  const int faultCode = analogRead(FAULT_OBSERVE_PIN);
  Serial.print(F("{\"type\":\"witness\",\"ok\":true,\"timestamp_ms\":"));
  Serial.print(millis());
  Serial.print(F(",\"enable_code\":")); Serial.print(enableCode);
  Serial.print(F(",\"fault_code\":")); Serial.print(faultCode);
  Serial.print(F(",\"enable\":")); Serial.print(enableCode >= HIGH_THRESHOLD_CODE ? 1 : 0);
  Serial.print(F(",\"fault\":")); Serial.print(faultCode >= HIGH_THRESHOLD_CODE ? 1 : 0);
  Serial.println(F("}"));
}

static void handleCommand(char *line) {
  if (strcmp(line, "ID?") == 0) identity();
  else if (strcmp(line, "PING") == 0) Serial.println(F("{\"type\":\"ack\",\"ok\":true,\"cmd\":\"PING\"}"));
  else if (strcmp(line, "SAMPLE?") == 0) sample();
  else if (strcmp(line, "STREAM ON") == 0) { streamEnabled = true; Serial.println(F("{\"type\":\"ack\",\"ok\":true,\"cmd\":\"STREAM ON\"}")); }
  else if (strcmp(line, "STREAM OFF") == 0) { streamEnabled = false; Serial.println(F("{\"type\":\"ack\",\"ok\":true,\"cmd\":\"STREAM OFF\"}")); }
  else Serial.println(F("{\"type\":\"error\",\"ok\":false,\"code\":\"BAD_COMMAND\",\"message\":\"unsupported command\"}"));
}

void setup() {
  pinMode(ENABLE_OBSERVE_PIN, INPUT);
  pinMode(FAULT_OBSERVE_PIN, INPUT);
  Serial.begin(SERIAL_BAUD);
  Serial.setTimeout(100);
}

void loop() {
  static char line[96];
  static size_t length = 0;
  while (Serial.available() > 0) {
    const char c = static_cast<char>(Serial.read());
    if (c == '\n') { line[length] = '\0'; if (length) handleCommand(line); length = 0; }
    else if (c != '\r' && length + 1 < sizeof(line)) line[length++] = c;
  }
  if (streamEnabled && millis() - lastStreamMs >= 20) { lastStreamMs = millis(); sample(); }
}
