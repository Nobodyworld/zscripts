"""Thin wrapper around :mod:`zscripts.cli` for legacy entry points."""

from __future__ import annotations

from zscripts.cli import main as cli_main

# TODO - Provide typed wrapper for python consolidate to improve IDE help.


def main() -> int:
    """Delegate to the shared CLI for the ``single_python`` group."""

    return cli_main(["consolidate", "--types", "python"])


if __name__ == "__main__":
    raise SystemExit(main())
