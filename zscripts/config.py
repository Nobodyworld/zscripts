"""Core configuration for the zscripts tooling.

This module exposes the default configuration for the project while also
supporting user overrides stored in ``config.json`` within the same directory.
The optional JSON file may define the following keys to customize behaviour:

``file_groups``
    Mapping of file names to the output group they should be written to.  Any
    entries supplied by the user extend/override :data:`DEFAULT_FILE_TYPES`.
``skip_dirs``
    Iterable of directory names that should be ignored in addition to
    :data:`DEFAULT_SKIP_DIRS`.
``ignore_patterns``
    Extra glob patterns that should be treated as ignored files or folders when
    scanning the project tree.
"""

from __future__ import annotations

from pathlib import Path
import json
from typing import Any, Dict

SCRIPT_DIR = Path(__file__).resolve().parent

CONFIG_FILE = SCRIPT_DIR / "config.json"

DEFAULT_SKIP_DIRS = [
    "__pycache__",
    "assets",
    "asgi",
    "build",
    "dist",
    "env",
    "envs",
    "logs",
    "media",
    "migrations",
    "node_modules",
    "public",
    "static",
    "staticfiles",
    "venv",
    "wsgi",
    "yayay",
    "zbuild",
    "zscripts",
    ".git.txt",
]

DEFAULT_FILE_TYPES = {
    "admin.py": "admin_files",
    #"api_views.py": "api_views_files",
    "apps.py": "apps_files",
    "forms.py": "forms_files",
    #"handlers.py": "handlers_files",
    #"middleware.py": "middleware_files",
    "models.py": "models_files",
    #"permissions.py": "permissions_files",
    #"serializers.py": "serializers_files",
    #"services.py": "services_files",
    "signals.py": "signals_files",
    #"tasks.py": "tasks_files",
    "tests.py": "tests_files",
    "urls.py": "urls_files",
    "views.py": "views_files",
    "utils.py": "utils_files",
    #"constants.py": "constants_files",
    #"context_processors.py": "context_processors_files",
    #"decorators.py": "decorators_files",
    #"exceptions.py": "exceptions_files",
    #"helpers.py": "helpers_files",
    #"mixins.py": "mixins_files",
    #"settings.py": "settings_files",
    #"custom_tags.py": "tag_files",
    #"utilities.py": "utilities_files",
    #"validators.py": "validators_files",
    #"factories.py": "factories_files",
}


def _load_user_config() -> Dict[str, Any]:
    """Load optional user configuration from :data:`CONFIG_FILE`."""

    if not CONFIG_FILE.is_file():
        return {}

    try:
        with CONFIG_FILE.open("r", encoding="utf-8") as config_stream:
            raw_config = json.load(config_stream)
            if isinstance(raw_config, dict):
                return raw_config
    except json.JSONDecodeError:
        # Fallback to defaults when the config file cannot be parsed.
        pass
    return {}


_USER_CONFIG = _load_user_config()


def _merge_file_types(defaults: Dict[str, str], overrides: Dict[str, str] | None) -> Dict[str, str]:
    """Merge file group overrides with the defaults."""

    merged = defaults.copy()
    if overrides:
        merged.update({k: v for k, v in overrides.items() if isinstance(k, str) and isinstance(v, str)})
    return merged


FILE_TYPES = _merge_file_types(DEFAULT_FILE_TYPES, _USER_CONFIG.get("file_groups"))

# Define the directories to skip, combining defaults with any user overrides.
SKIP_DIRS = sorted({
    skip.strip("/")
    for skip in DEFAULT_SKIP_DIRS + [
        entry for entry in _USER_CONFIG.get("skip_dirs", []) if isinstance(entry, str)
    ]
    if skip
})

# Additional ignore patterns supplied via ``config.json``.
USER_IGNORE_PATTERNS = {
    pattern
    for pattern in _USER_CONFIG.get("ignore_patterns", [])
    if isinstance(pattern, str) and pattern
}

# Define directories for logging and output
LOG_DIR = SCRIPT_DIR / 'logs'
BUILD_DIR = LOG_DIR / 'build_files'
ANALYSIS_DIR = LOG_DIR / 'analysis_logs'
CONSOLIDATION_DIR = LOG_DIR / 'consoli_files'
WORK_DIR = LOG_DIR / 'logs_files'

# Define log directories for specific file types
ALL_LOG_DIR = LOG_DIR / 'logs_apps_all'
PYTHON_LOG_DIR = LOG_DIR / 'logs_apps_pyth'
HTML_LOG_DIR = LOG_DIR / 'logs_apps_html'
CSS_LOG_DIR = LOG_DIR / 'logs_apps_css'
JS_LOG_DIR = LOG_DIR / 'logs_apps_js'
BOTH_LOG_DIR = LOG_DIR / 'logs_apps_both'
SINGLE_LOG_DIR = LOG_DIR / 'logs_single_files'

# Define the single file log name
CAPTURE_ALL_PYTHON_LOG = SINGLE_LOG_DIR / 'capture_all_pyth.txt'
CAPTURE_ALL_HTML_LOG = SINGLE_LOG_DIR / 'capture_all_html.txt'
CAPTURE_ALL_CSS_LOG = SINGLE_LOG_DIR / 'capture_all_css.txt'
CAPTURE_ALL_JS_LOG = SINGLE_LOG_DIR / 'capture_all_js.txt'
CAPTURE_ALL_PYTHON_HTML_LOG = SINGLE_LOG_DIR / 'capture_all_python_html.txt'
CAPTURE_ALL_LOG = SINGLE_LOG_DIR / 'capture_all.txt'
