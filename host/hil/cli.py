from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import sys

from .evidence import EvidenceBundle, EvidenceError
from .discovery import scan_system_ports
from .protocol import PROTOCOL_VERSION
from .reporting import render_markdown_summary, write_junit_xml
from .scenarios import CORE_SCENARIOS, run_software_scenario


def _software_regression(output: Path) -> int:
    try:
        bundle = EvidenceBundle.create(output, evidence_level="software-simulation")
    except EvidenceError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    results = [run_software_scenario(case.test_id) for case in CORE_SCENARIOS]
    bundle.write_metadata({
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "protocol_version": PROTOCOL_VERSION,
        "scenario_count": len(results),
    })
    bundle.write_test_summary([
        {
            "test_id": result.test_id,
            "result": "PASS" if result.passed else "FAIL",
            "requirement_ids": ";".join(result.requirement_ids),
            "details": result.details,
        }
        for result in results
    ])
    (bundle.root / "summary.md").write_text(
        render_markdown_summary(results, evidence_level="software-simulation"),
        encoding="utf-8",
    )
    write_junit_xml(bundle.root / "junit.xml", results, suite_name="software-reference")
    (bundle.root / "event_log.csv").write_text("test_id,result,evidence\n", encoding="utf-8")
    for result in results:
        with (bundle.root / "event_log.csv").open("a", encoding="utf-8") as handle:
            handle.write(f"{result.test_id},{'PASS' if result.passed else 'FAIL'},\"{'|'.join(result.evidence)}\"\n")
    for name in ("dut_telemetry.csv", "hil_telemetry.csv", "witness_telemetry.csv"):
        (bundle.root / name).write_text("timestamp_ms,source,note\n", encoding="utf-8")
    return 0 if all(result.passed for result in results) else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="hilrig", description="HIL verification rig host executive")
    sub = parser.add_subparsers(dest="command", required=True)
    software = sub.add_parser("software-regression", help="run deterministic hardware-free regression")
    software.add_argument("--output", required=True, type=Path)
    sub.add_parser("discover", help="probe serial ports and identify DUT, HIL, and witness roles")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "software-regression":
        return _software_regression(args.output)
    if args.command == "discover":
        identities, transports = scan_system_ports()
        try:
            for role in ("dut", "hil", "witness"):
                identity = identities.get(role)
                if identity is None:
                    print(f"{role}: MISSING")
                else:
                    print(f"{role}: {identity.port}  firmware={identity.firmware_version}  board_id={identity.board_id}")
            return 0 if set(identities) == {"dut", "hil", "witness"} else 2
        finally:
            for transport in transports.values():
                transport.close()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
