from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PlantConfig:
    source_voltage_mv: int = 12000
    droop_milliohms: int = 50
    ambient_temperature_cc: int = 2500
    heating_divisor_ma: int = 500
    fan_cooling_divisor_percent: int = 20
    passive_cooling_divisor_cc: int = 1000


@dataclass(frozen=True, slots=True)
class PlantState:
    bus_mv: int
    current_ma: int
    temperature_cc: int


def step_plant(
    state: PlantState,
    config: PlantConfig,
    *,
    enable: bool,
    fan_percent: int,
    scripted_load_ma: int,
) -> PlantState:
    if not 0 <= fan_percent <= 100:
        raise ValueError("fan_percent must be 0..100")
    if scripted_load_ma < 0:
        raise ValueError("scripted_load_ma must be non-negative")
    current_ma = scripted_load_ma if enable else 0
    droop_mv = (current_ma * config.droop_milliohms) // 1000
    bus_mv = max(0, config.source_voltage_mv - droop_mv)
    heating_cc = current_ma // config.heating_divisor_ma
    fan_cooling_cc = fan_percent // config.fan_cooling_divisor_percent
    passive_cooling_cc = max(0, state.temperature_cc - config.ambient_temperature_cc) // config.passive_cooling_divisor_cc
    temperature_cc = max(
        config.ambient_temperature_cc,
        state.temperature_cc + heating_cc - fan_cooling_cc - passive_cooling_cc,
    )
    return PlantState(bus_mv=bus_mv, current_ma=current_ma, temperature_cc=temperature_cc)
