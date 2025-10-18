"""zscripts package entry point for programmatic access."""

from .config import get_config  # re-export for convenience

# TODO - Expose a richer public API surface for automation integrations.

__all__ = ["get_config"]
