from __future__ import annotations

from pathlib import Path
from collections.abc import Iterable, Sequence

from .scenarios import ScenarioResult


def render_markdown_summary(results: Iterable[ScenarioResult], *, evidence_level: str) -> str:
    results = list(results)
    passed = sum(result.passed for result in results)
    label = evidence_level.upper().replace("-", "-")
    lines = [
        f"# {label} EVIDENCE SUMMARY",
        "",
        f"**Result:** {passed}/{len(results)} PASS",
        "",
    ]
    if evidence_level != "physical-hil":
        lines.extend([
            "> This is not physical HIL evidence. It verifies software/reference-model behavior only.",
            "",
        ])
    lines.extend(["| Test | Result | Requirements | Details |", "|---|---|---|---|"])
    for result in results:
        lines.append(
            f"| {result.test_id} | {'PASS' if result.passed else 'FAIL'} | "
            f"{', '.join(result.requirement_ids)} | {result.details} |"
        )
    lines.append("")
    return "\n".join(lines)


def write_timeline_plot(path: Path, x: Sequence[float], y: Sequence[float], *, ylabel: str) -> Path:
    if len(x) != len(y) or not x:
        raise ValueError("x and y must be non-empty and equal length")
    import matplotlib.pyplot as plt

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots()
    ax.step(x, y, where="post")
    ax.set_xlabel("Time (ms)")
    ax.set_ylabel(ylabel)
    ax.grid(True)
    fig.tight_layout()
    fig.savefig(target, dpi=160)
    plt.close(fig)
    return target


def write_junit_xml(path: Path, results: Iterable[ScenarioResult], *, suite_name: str) -> Path:
    from xml.etree import ElementTree as ET
    results = list(results)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    suite = ET.Element("testsuite", name=suite_name, tests=str(len(results)), failures=str(sum(not r.passed for r in results)))
    for result in results:
        case = ET.SubElement(suite, "testcase", classname="hil.scenarios", name=result.test_id)
        ET.SubElement(case, "system-out").text = "\n".join((result.details, *result.evidence))
        if not result.passed:
            ET.SubElement(case, "failure", message=result.details).text = "\n".join(result.evidence)
    tree = ET.ElementTree(suite)
    ET.indent(tree, space="  ")
    tree.write(target, encoding="utf-8", xml_declaration=True)
    return target
