from hil.scenarios import CORE_SCENARIOS, scenario_by_id


def test_core_catalog_contains_every_approved_test_id_once():
    expected = {"TC-001","TC-010","TC-020","TC-021","TC-030","TC-040","TC-041","TC-050","TC-051","TC-052","TC-060","TC-070","TC-080","TC-090"}
    ids = [case.test_id for case in CORE_SCENARIOS]
    assert set(ids) == expected
    assert len(ids) == len(set(ids))


def test_every_core_scenario_traces_to_at_least_one_requirement():
    assert all(case.requirement_ids for case in CORE_SCENARIOS)
    assert "SYS-001" in scenario_by_id("TC-001").requirement_ids
    assert "FLT-002" in scenario_by_id("TC-050").requirement_ids
