"""Thin wrapper around :mod:`zscripts.cli` for legacy entry points."""

from __future__ import annotations

from zscripts.cli import main as cli_main

# TODO - Unify CSS consolidate wrapper with dynamic extension selection.


def main() -> int:
    """Delegate to the shared CLI for the ``single_css`` group."""

    return cli_main(["consolidate", "--types", "css"])


if __name__ == "__main__":
    raise SystemExit(main())
