import pytest

from hil.scenarios import CORE_SCENARIOS, run_software_scenario


@pytest.mark.parametrize("case", CORE_SCENARIOS, ids=lambda case: case.test_id)
def test_core_software_scenario_passes_under_reference_model(case):
    result = run_software_scenario(case.test_id)
    assert result.passed, result.details
    assert result.test_id == case.test_id
    assert result.requirement_ids == case.requirement_ids
    assert result.evidence
