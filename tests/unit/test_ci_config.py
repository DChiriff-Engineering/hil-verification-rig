from pathlib import Path
import yaml


def test_ci_workflow_has_host_and_all_firmware_build_gates():
    root = Path(__file__).resolve().parents[2]
    workflow = yaml.safe_load((root / ".github/workflows/verification.yml").read_text())
    assert set(workflow["jobs"]) == {"host-tests", "pico-firmware", "uno-firmware"}
    host = workflow["jobs"]["host-tests"]
    assert host["strategy"]["matrix"]["python-version"] == ["3.11", "3.12", "3.13"]
    pico_text = str(workflow["jobs"]["pico-firmware"])
    assert "2.3.0" in pico_text
    assert "firmware/dut_pico" in pico_text
    assert "firmware/hil_pico" in pico_text
    uno_text = str(workflow["jobs"]["uno-firmware"])
    assert "arduino:avr:uno" in uno_text


def test_ci_never_runs_physical_hardware_tests():
    root = Path(__file__).resolve().parents[2]
    text = (root / ".github/workflows/verification.yml").read_text()
    assert 'pytest -m "not hil"' in text
    assert "HIL_RUN=1" not in text
