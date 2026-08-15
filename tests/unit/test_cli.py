import json
from pathlib import Path

from hil.cli import main


def test_software_regression_command_creates_reproducible_bundle(tmp_path: Path):
    out = tmp_path / "software-run"
    code = main(["software-regression", "--output", str(out)])
    assert code == 0
    metadata = json.loads((out / "metadata.json").read_text())
    assert metadata["evidence_level"] == "software-simulation"
    assert metadata["physical_hardware"] is False
    assert (out / "test_summary.csv").exists()
    assert (out / "summary.md").exists()
    assert (out / "junit.xml").exists()
    assert (out / "event_log.csv").exists()
    assert (out / "dut_telemetry.csv").exists()
    assert (out / "hil_telemetry.csv").exists()
    assert (out / "witness_telemetry.csv").exists()


def test_software_regression_returns_nonzero_if_output_exists(tmp_path: Path):
    out = tmp_path / "software-run"
    out.mkdir()
    assert main(["software-regression", "--output", str(out)]) == 2


def test_discover_command_reports_all_roles(monkeypatch, capsys):
    import hil.cli as cli
    from hil.discovery import DeviceIdentity
    identities = {
        "dut": DeviceIdentity("COM4", "dut", "0.1.0", "D", 1),
        "hil": DeviceIdentity("COM7", "hil", "0.1.0", "H", 1),
        "witness": DeviceIdentity("COM9", "witness", "0.1.0", "W", 1),
    }
    class Dummy:
        def close(self): pass
    monkeypatch.setattr(cli, "scan_system_ports", lambda: (identities, {k: Dummy() for k in identities}))
    assert cli.main(["discover"]) == 0
    output = capsys.readouterr().out
    assert "COM4" in output and "COM7" in output and "COM9" in output
