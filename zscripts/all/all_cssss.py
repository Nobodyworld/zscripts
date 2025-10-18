"""Thin wrapper around :mod:`zscripts.cli` for legacy entry points."""

from __future__ import annotations

from zscripts.cli import main as cli_main

# TODO - Decommission CSS wrapper once direct CLI aliases are supported.


def main() -> int:
    """Delegate to the shared CLI for the ``apps_css`` group."""

    return cli_main(["collect", "--types", "css"])


if __name__ == "__main__":
    raise SystemExit(main())
