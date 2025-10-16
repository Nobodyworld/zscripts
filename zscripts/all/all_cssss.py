"""Thin wrapper around :mod:`zscripts.cli` for legacy entry points."""

from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    """Delegate to the shared CLI for the ``apps_css`` group."""

    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    from zscripts.cli import main as cli_main

    return cli_main(['collect', '--types', 'css'])


if __name__ == '__main__':
    raise SystemExit(main())
