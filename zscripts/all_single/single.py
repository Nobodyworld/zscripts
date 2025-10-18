"""Thin wrapper around :mod:`zscripts.cli` for legacy entry points."""

from __future__ import annotations

from zscripts.cli import main as cli_main

# TODO - Support parameter injection to avoid hard-coded CLI arguments.


def main() -> int:
    """Delegate to the shared CLI for the ``single_all`` group."""

    return cli_main(["consolidate", "--types", "any"])


if __name__ == "__main__":
    raise SystemExit(main())
