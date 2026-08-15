# Interface Control Document

**Protocol family:** HIL Rig Protocol v1  
**Sensor binary sync:** `0xA55A`  
**Integrity:** CRC-16/CCITT-FALSE (`poly=0x1021`, init `0xFFFF`, xorout `0x0000`, no reflection)  
**Pico-to-Pico UART:** 115200 baud, 8 data bits, no parity, 1 stop bit

## 1. Electrical interface

The UNO Rev3 is a 5 V board. It is **read-only** relative to all Pico GPIO in this design and must not drive Pico pins.

| Signal | Source | Destination | Notes |
|---|---|---|---|
| UART TX | HIL GP0 | DUT GP1 | 3.3 V only |
| ENABLE | DUT GP10 | HIL GP10 and UNO A0 | UNO observes only |
| PWM | DUT GP11 | HIL GP11 | HIL edge-timestamp capture |
| FAULT status | DUT GP12 | UNO A1 | UNO observes only |
| GND | common | common | required for direct signal connections |

## 2. Binary sensor frame

All multibyte integers are little-endian. Total length is **14 bytes**.

| Offset | Size | Field | Encoding |
|---:|---:|---|---|
| 0 | 2 | sync | `0xA55A` |
| 2 | 1 | protocol version | `1` |
| 3 | 1 | flags | bit field, baseline `0` |
| 4 | 2 | sequence | unsigned 16-bit |
| 6 | 2 | bus voltage | millivolts, unsigned 16-bit |
| 8 | 2 | load current | milliamps, unsigned 16-bit |
| 10 | 2 | temperature | centi-degrees C, signed 16-bit |
| 12 | 2 | CRC | CRC over bytes 0–11 |

### Sequence rule

The first valid frame establishes the sequence baseline. Thereafter:

- a repeated sequence is stale/invalid;
- a clearly backward/out-of-order sequence is stale/invalid;
- a forward gap is accepted and may be diagnosed, because one or more corrupt frames may have been deliberately rejected;
- 16-bit wraparound is supported.

Three consecutive corrupt/stale frames escalate to FAULT. This rule ensures one intentionally corrupted CRC frame does not permanently poison synchronization.

## 3. DUT USB command interface

Commands are UTF-8 ASCII lines terminated by `\n`. Responses are one JSON object per line.

| Command | Purpose |
|---|---|
| `ID?` | return role, protocol version, firmware version, unique board ID |
| `PING` | heartbeat |
| `STATUS?` | current state/fault/outputs/counters |
| `RESET` | reset controller state/counters to safe STARTUP |

Representative identity:

```json
{"type":"id","ok":true,"protocol_version":1,"role":"dut","firmware_version":"0.1.0","board_id":"..."}
```

## 4. HIL USB command interface

| Command | Purpose |
|---|---|
| `ID?` | identify HIL controller |
| `PING` | heartbeat |
| `STATUS?` | plant state, observed DUT outputs, active injection |
| `RESET` | restore deterministic defaults |
| `LOAD <mA>` | set scripted enabled-load current |
| `SOURCE <mV>` | set plant source voltage |
| `FAULT CLEAR` | disable active injection |
| `FAULT SET OVERVOLTAGE <mV>` | override transmitted V_bus |
| `FAULT SET UNDERVOLTAGE <mV>` | override transmitted V_bus |
| `FAULT SET OVERCURRENT <mA>` | override transmitted I_load |
| `FAULT SET OVERTEMPERATURE <centi-C>` | override transmitted temperature |
| `FAULT SET BAD_CRC <value>` | corrupt each emitted frame CRC while active |
| `FAULT SET DROPOUT <value>` | suppress sensor frames |
| `FAULT SET REPEAT_SEQ <value>` | repeat sequence number |
| `FAULT SET FROZEN <value>` | hold one complete sensor frame |

`value` is syntactically required by protocol v1 even for mode-only injections; mode-only handlers ignore it.

## 5. UNO USB command interface

| Command | Purpose |
|---|---|
| `ID?` | return witness identity |
| `PING` | heartbeat |
| `SAMPLE?` | return A0/A1 raw codes, derived ENABLE/FAULT, timestamp |
| `STREAM ON` | begin 20 ms observation stream |
| `STREAM OFF` | stop stream |

There is intentionally **no command that drives an output pin**.

## 6. Host compatibility rule

The host refuses identities with an unsupported protocol version. COM numbers are not stable identifiers; role discovery probes every candidate port with `ID?` and classifies by response.
