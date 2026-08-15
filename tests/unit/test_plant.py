from hil.plant import PlantConfig, PlantState, step_plant


def test_disabled_load_draws_zero_current_and_no_droop():
    state = PlantState(bus_mv=12000, current_ma=0, temperature_cc=2500)
    out = step_plant(state, PlantConfig(), enable=False, fan_percent=0, scripted_load_ma=4000)
    assert out.current_ma == 0
    assert out.bus_mv == 12000


def test_enabled_load_creates_droop_and_heating():
    state = PlantState(bus_mv=12000, current_ma=0, temperature_cc=2500)
    out = step_plant(state, PlantConfig(), enable=True, fan_percent=0, scripted_load_ma=4000)
    assert out.current_ma == 4000
    assert out.bus_mv < 12000
    assert out.temperature_cc > 2500


def test_more_fan_reduces_next_temperature_for_same_load():
    state = PlantState(bus_mv=12000, current_ma=0, temperature_cc=7000)
    low_fan = step_plant(state, PlantConfig(), enable=True, fan_percent=0, scripted_load_ma=4000)
    high_fan = step_plant(state, PlantConfig(), enable=True, fan_percent=100, scripted_load_ma=4000)
    assert high_fan.temperature_cc < low_fan.temperature_cc
