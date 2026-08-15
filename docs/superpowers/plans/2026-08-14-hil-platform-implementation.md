# HIL Verification Rig Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement the approved Windows-first HIL verification baseline for two Raspberry Pi Picos plus a read-only Arduino UNO witness, with deterministic host simulation, requirements-driven pytest automation, append-only evidence, firmware compiler gates, and no fabricated physical results.

**Task order:** protocol/data model → deterministic plant → virtual DUT/system scenarios → scenario/traceability catalog → transports/discovery/clients → evidence/reporting → DUT Pico firmware → HIL Pico firmware → UNO witness → hardware pytest/CLI → CI builds → Windows PowerShell workflow → documentation/traceability → README/roadmap → final PR/merge verification.

**Frozen project constants:** frame sync `0xA55A`, protocol v1, CRC-16/CCITT-FALSE, UV `<10500 mV`, healthy recovery `>=10800 mV`, OV `>=14500 mV`, OC warning `>=4500 mA`, severe OC `>=6000 mA` for 3 valid samples, thermal derate `>=7000 centi-C`, severe temperature `>=8500 centi-C`, sensor timeout `250 ms`, healthy recovery dwell `1000 ms`, three consecutive corrupt/stale frames escalate to FAULT.

**Verification gates:** full non-hardware pytest green; deterministic software regression; evidence non-overwrite checks; Python compileall; both Pico firmware targets compile against the same pinned official Pico SDK; UNO firmware compiles for UNO Rev3; branch CI green; docs/constants/links trace correctly; no license file; no unearned physical claims; post-merge `main` CI green.

**Hardware boundary:** board flashing, real UART/GPIO/PWM wiring, physical closed loop, reaction latency, UNO agreement, and measured result bundles remain pending until the user connects the Windows rig.
