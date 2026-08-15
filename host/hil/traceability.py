from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping

from .scenarios import ScenarioSpec


def coverage_by_requirement(cases: Iterable[ScenarioSpec]) -> dict[str, tuple[str, ...]]:
    mapping: dict[str, list[str]] = defaultdict(list)
    for case in cases:
        for requirement_id in case.requirement_ids:
            mapping[requirement_id].append(case.test_id)
    return {key: tuple(value) for key, value in mapping.items()}


def validate_traceability(requirements: Mapping[str, str], cases: Iterable[ScenarioSpec]) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    for case in cases:
        if case.test_id in seen:
            errors.append(f"duplicate test ID {case.test_id}")
        seen.add(case.test_id)
        if not case.requirement_ids:
            errors.append(f"{case.test_id} has no requirements")
        for rid in case.requirement_ids:
            if rid not in requirements:
                errors.append(f"{case.test_id} references unknown requirement {rid}")
    return errors
