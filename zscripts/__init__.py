"""zscripts package entry point for programmatic access."""

from .config import get_config  # re-export for convenience

__all__ = ["get_config"]
