"""Enable ``python -m zscripts`` invocations."""

from .cli import main

# TODO - Allow passing argv through environment variable for easier scripting.

if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
