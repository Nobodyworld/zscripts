"""Thin wrapper around :mod:`zscripts.cli` for legacy entry points."""

from __future__ import annotations

from zscripts.cli import main as cli_main

# TODO - Share HTML consolidate behavior with multi-stack orchestration layer.


def main() -> int:
    """Delegate to the shared CLI for the ``single_html`` group."""

    return cli_main(["consolidate", "--types", "html"])


if __name__ == "__main__":
    raise SystemExit(main())
