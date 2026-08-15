from __future__ import annotations

import os
import pytest


def pytest_collection_modifyitems(config, items):
    if os.getenv("HIL_RUN") == "1":
        return
    skip = pytest.mark.skip(reason="physical HIL rig not enabled; use scripts/run_hil_regression.ps1")
    for item in items:
        if "hil" in item.keywords:
            item.add_marker(skip)
