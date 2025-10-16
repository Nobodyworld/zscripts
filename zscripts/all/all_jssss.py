"""Thin wrapper around :mod:`zscripts.cli` for legacy entry points."""

from __future__ import annotations

from zscripts.cli import main as cli_main


def main() -> int:
    """Delegate to the shared CLI for the ``apps_js`` group."""

    return cli_main(["collect", "--types", "js"])


if __name__ == "__main__":
    raise SystemExit(main())
