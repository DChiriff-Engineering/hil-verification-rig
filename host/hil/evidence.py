from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping


class EvidenceError(RuntimeError):
    pass


@dataclass(slots=True)
class EvidenceBundle:
    root: Path
    evidence_level: str

    @classmethod
    def create(cls, path: Path, *, evidence_level: str) -> "EvidenceBundle":
        path = Path(path)
        if path.exists():
            raise EvidenceError(f"evidence directory already exists: {path}")
        path.mkdir(parents=True)
        (path / "plots").mkdir()
        return cls(path, evidence_level)

    def write_metadata(self, metadata: Mapping[str, object]) -> Path:
        payload = {
            "evidence_level": self.evidence_level,
            "physical_hardware": self.evidence_level == "physical-hil",
            **dict(metadata),
        }
        target = self.root / "metadata.json"
        target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return target

    def write_test_summary(self, rows: Iterable[Mapping[str, object]]) -> Path:
        rows = list(rows)
        target = self.root / "test_summary.csv"
        fieldnames = list(rows[0].keys()) if rows else ["test_id", "result", "requirement_ids"]
        with target.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        return target
