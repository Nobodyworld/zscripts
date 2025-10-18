"""Thin wrapper around :mod:`zscripts.cli` for legacy entry points."""

from __future__ import annotations

from zscripts.cli import main as cli_main

# TODO - Merge dual-stack entry point with primary CLI command table.


def main() -> int:
    """Delegate to the shared CLI for the ``apps_python_html`` group."""

    return cli_main(["collect", "--types", "python_html"])


if __name__ == "__main__":
    raise SystemExit(main())
