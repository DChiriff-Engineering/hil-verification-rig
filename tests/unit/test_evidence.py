import json
from pathlib import Path

import pytest

from hil.evidence import EvidenceBundle, EvidenceError


def test_evidence_bundle_refuses_to_overwrite_existing_directory(tmp_path: Path):
    existing = tmp_path / "run"
    existing.mkdir()
    (existing / "keep.txt").write_text("preserve")
    with pytest.raises(EvidenceError, match="exists"):
        EvidenceBundle.create(existing, evidence_level="software-simulation")
    assert (existing / "keep.txt").read_text() == "preserve"


def test_evidence_bundle_writes_labeled_metadata_and_summary(tmp_path: Path):
    bundle = EvidenceBundle.create(tmp_path / "run", evidence_level="software-simulation")
    bundle.write_metadata({"git_commit": "abc123", "protocol_version": 1})
    bundle.write_test_summary([{"test_id": "TC-001", "result": "PASS", "requirement_ids": "SYS-001"}])
    metadata = json.loads((bundle.root / "metadata.json").read_text())
    assert metadata["evidence_level"] == "software-simulation"
    assert metadata["physical_hardware"] is False
    assert (bundle.root / "test_summary.csv").exists()
