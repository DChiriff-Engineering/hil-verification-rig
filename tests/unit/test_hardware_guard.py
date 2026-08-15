from pathlib import Path


def test_hardware_tests_are_explicitly_marked_and_windows_runner_enables_them():
    root = Path(__file__).resolve().parents[2]
    test_text = (root / "tests/hardware/test_hil_smoke.py").read_text()
    assert "pytest.mark.hil" in test_text
