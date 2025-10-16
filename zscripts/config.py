"""Configuration loader for zscripts.

This module preserves the existing constant-based interface while sourcing
values from the JSON configuration file stored at the repository root.  The
structure mirrors the keys documented in :code:`zscripts.config.json` so the
rest of the codebase can continue importing the same names.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_CONFIG_PATH = SCRIPT_DIR.parent / "zscripts.config.json"


def _load_raw_config(config_path: Path | None = None) -> Dict[str, Any]:
    """Load the JSON configuration file."""

    path = config_path or DEFAULT_CONFIG_PATH
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError as exc:  # pragma: no cover - defensive guard
        raise RuntimeError(
            "Configuration file not found. Ensure zscripts.config.json exists"
        ) from exc


_RAW_CONFIG = _load_raw_config()

SKIP_DIRS = list(_RAW_CONFIG.get("skip", []))
FILE_TYPES = dict(_RAW_CONFIG.get("file_types", {}))
USER_IGNORE_PATTERNS = set(_RAW_CONFIG.get("user_ignore_patterns", []))

_directories = _RAW_CONFIG.get("directories", {})
LOG_DIR = SCRIPT_DIR / _directories.get("log_root", "logs")
BUILD_DIR = LOG_DIR / _directories.get("build", "build_files")
ANALYSIS_DIR = LOG_DIR / _directories.get("analysis", "analysis_logs")
CONSOLIDATION_DIR = LOG_DIR / _directories.get("consolidation", "consoli_files")
WORK_DIR = LOG_DIR / _directories.get("work", "logs_files")

_collection_logs = _RAW_CONFIG.get("collection_logs", {})
ALL_LOG_DIR = LOG_DIR / _collection_logs.get("all", "logs_apps_all")
PYTHON_LOG_DIR = LOG_DIR / _collection_logs.get("python", "logs_apps_pyth")
HTML_LOG_DIR = LOG_DIR / _collection_logs.get("html", "logs_apps_html")
CSS_LOG_DIR = LOG_DIR / _collection_logs.get("css", "logs_apps_css")
JS_LOG_DIR = LOG_DIR / _collection_logs.get("js", "logs_apps_js")
BOTH_LOG_DIR = LOG_DIR / _collection_logs.get("python_html", "logs_apps_both")
SINGLE_LOG_DIR = LOG_DIR / _collection_logs.get("single", "logs_single_files")

_single_targets = _RAW_CONFIG.get("single_targets", {})
CAPTURE_ALL_PYTHON_LOG = SINGLE_LOG_DIR / _single_targets.get(
    "python", "capture_all_pyth.txt"
)
CAPTURE_ALL_HTML_LOG = SINGLE_LOG_DIR / _single_targets.get(
    "html", "capture_all_html.txt"
)
CAPTURE_ALL_CSS_LOG = SINGLE_LOG_DIR / _single_targets.get(
    "css", "capture_all_css.txt"
)
CAPTURE_ALL_JS_LOG = SINGLE_LOG_DIR / _single_targets.get(
    "js", "capture_all_js.txt"
)
CAPTURE_ALL_PYTHON_HTML_LOG = SINGLE_LOG_DIR / _single_targets.get(
    "python_html", "capture_all_python_html.txt"
)
CAPTURE_ALL_LOG = SINGLE_LOG_DIR / _single_targets.get("any", "capture_all.txt")


def load_config(path: Path | str | None = None) -> Dict[str, Any]:
    """Load configuration data from a custom path."""

    if path is None:
        return dict(_RAW_CONFIG)

    return _load_raw_config(Path(path))


def get_config() -> Dict[str, Any]:
    """Return a shallow copy of the loaded configuration."""

    return dict(_RAW_CONFIG)


__all__ = [
    "DEFAULT_CONFIG_PATH",
    "SKIP_DIRS",
    "FILE_TYPES",
    "USER_IGNORE_PATTERNS",
    "SCRIPT_DIR",
    "LOG_DIR",
    "BUILD_DIR",
    "ANALYSIS_DIR",
    "CONSOLIDATION_DIR",
    "WORK_DIR",
    "ALL_LOG_DIR",
    "PYTHON_LOG_DIR",
    "HTML_LOG_DIR",
    "CSS_LOG_DIR",
    "JS_LOG_DIR",
    "BOTH_LOG_DIR",
    "SINGLE_LOG_DIR",
    "CAPTURE_ALL_PYTHON_LOG",
    "CAPTURE_ALL_HTML_LOG",
    "CAPTURE_ALL_CSS_LOG",
    "CAPTURE_ALL_JS_LOG",
    "CAPTURE_ALL_PYTHON_HTML_LOG",
    "CAPTURE_ALL_LOG",
    "load_config",
    "get_config",
]
