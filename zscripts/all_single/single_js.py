"""Thin wrapper around :mod:`zscripts.cli` for legacy entry points."""

from __future__ import annotations

from zscripts.cli import main as cli_main

# TODO - Remove bespoke JS launcher when consolidate command gains presets.


def main() -> int:
    """Delegate to the shared CLI for the ``single_js`` group."""

    return cli_main(["consolidate", "--types", "js"])


if __name__ == "__main__":
    raise SystemExit(main())
