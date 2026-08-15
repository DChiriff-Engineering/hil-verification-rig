from pathlib import Path

from hil.reporting import render_markdown_summary, write_timeline_plot
from hil.scenarios import run_software_scenario


def test_markdown_summary_distinguishes_software_from_physical_evidence():
    results = [run_software_scenario("TC-001"), run_software_scenario("TC-021")]
    text = render_markdown_summary(results, evidence_level="software-simulation")
    assert "SOFTWARE-SIMULATION EVIDENCE" in text
    assert "not physical HIL evidence" in text
    assert "TC-001" in text and "TC-021" in text
    assert "2/2 PASS" in text


def test_timeline_plot_writes_nonempty_png(tmp_path: Path):
    path = write_timeline_plot(tmp_path / "timeline.png", [0, 50, 100], [0, 1, 1], ylabel="ENABLE")
    assert path.exists()
    assert path.stat().st_size > 100


def test_junit_writer_records_test_counts_and_failures(tmp_path: Path):
    from xml.etree import ElementTree as ET
    from hil.reporting import write_junit_xml
    results = [run_software_scenario("TC-001"), run_software_scenario("TC-021")]
    path = write_junit_xml(tmp_path / "junit.xml", results, suite_name="software-reference")
    root = ET.parse(path).getroot()
    assert root.attrib["tests"] == "2"
    assert root.attrib["failures"] == "0"
    assert [case.attrib["name"] for case in root.findall("testcase")] == ["TC-001", "TC-021"]
