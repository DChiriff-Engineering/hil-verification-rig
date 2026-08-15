from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]


def test_windows_operator_scripts_exist_and_use_project_cli():
    expected = [
        "scripts/setup_windows.ps1",
        "scripts/build_firmware.ps1",
        "scripts/run_software_regression.ps1",
        "scripts/run_hil_regression.ps1",
        "scripts/discover_rig.ps1",
    ]
    for path in expected:
        assert (ROOT / path).exists(), path
    assert "hilrig discover" in (ROOT / "scripts/discover_rig.ps1").read_text()
    assert "software-regression" in (ROOT / "scripts/run_software_regression.ps1").read_text()


def test_documentation_preserves_uno_read_only_safety_rule():
    combined = "\n".join((ROOT / p).read_text() for p in ["README.md", "docs/architecture.md", "docs/interface-control-document.md", "docs/safety-and-usage.md"])
    assert "read-only" in combined.lower()
    assert "5 V" in combined
    assert "must not drive" in combined.lower() or "never drive" in combined.lower()


def test_no_license_or_copying_file_is_present():
    forbidden = [p for p in ROOT.rglob("*") if p.is_file() and p.name.lower().startswith(("license", "copying"))]
    assert forbidden == []


def test_relative_markdown_links_resolve():
    broken = []
    link_re = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
    for md in ROOT.rglob("*.md"):
        if any(part in {".pytest_cache", "results"} for part in md.parts):
            continue
        for target in link_re.findall(md.read_text(encoding="utf-8")):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            clean = target.split("#", 1)[0]
            if clean and not (md.parent / clean).resolve().exists():
                broken.append((str(md.relative_to(ROOT)), target))
    assert broken == []
