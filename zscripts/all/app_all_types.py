"""Thin wrapper around :mod:`zscripts.cli` for legacy entry points."""

from __future__ import annotations

from zscripts.cli import main as cli_main

# TODO - Introduce a registry of legacy entry points instead of separate modules.


def main() -> int:
    """Delegate to the shared CLI for the ``apps_all`` group."""

    return cli_main(["collect", "--types", "all"])


if __name__ == "__main__":
    raise SystemExit(main())
