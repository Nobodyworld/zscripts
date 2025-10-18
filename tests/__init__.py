"""Ensure the repository root is on ``sys.path`` during tests."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:  # pragma: no cover - environment guard
    sys.path.insert(0, str(ROOT))

# TODO - Replace manual path injection with editable install in test runner.
