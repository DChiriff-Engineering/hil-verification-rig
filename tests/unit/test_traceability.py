from hil.requirements import REQUIREMENTS
from hil.scenarios import CORE_SCENARIOS
from hil.traceability import coverage_by_requirement, validate_traceability


def test_traceability_catalog_has_no_unknown_requirement_ids():
    errors = validate_traceability(REQUIREMENTS, CORE_SCENARIOS)
    assert errors == []


def test_every_safety_control_requirement_has_automated_coverage():
    coverage = coverage_by_requirement(CORE_SCENARIOS)
    required_prefixes = ("SYS-", "COM-", "MON-", "CTRL-", "FLT-", "REC-", "DIAG-")
    uncovered = [rid for rid in REQUIREMENTS if rid.startswith(required_prefixes) and not coverage.get(rid)]
    assert uncovered == []
