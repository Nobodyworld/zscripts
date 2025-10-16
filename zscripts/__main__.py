"""Enable ``python -m zscripts`` invocations."""

from .cli import main

if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
