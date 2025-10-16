# zscripts/config.py
from __future__ import annotations

import fnmatch
import warnings
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

try:  # pragma: no cover - optional dependency is validated at runtime
    import yaml  # type: ignore
except ImportError:  # pragma: no cover - handled gracefully when PyYAML is unavailable
    yaml = None

# Define the directories to skip
SKIP_DIRS = ['zscripts', 'zbuild', 'migrations', 'static', 'yayay',
              'asgi', 'wsgi', 'migrations', 'staticfiles', 'logs',
              'media', '__pycache__', 'build', 'dist', 'zscripts',
              'venv', 'env', 'envs', 'node_modules', 'public', 'assets',
              '.git.txt']


CONFIG_FILE_NAME = "zscripts.config.yaml"

# Define the default file groups that map to file patterns
DEFAULT_FILE_GROUPS: Mapping[str, Sequence[str]] = {
    "admin_files": ["admin.py"],
    #"api_views_files": ["api_views.py"],
    "apps_files": ["apps.py"],
    "forms_files": ["forms.py"],
    #"handlers_files": ["handlers.py"],
    #"middleware_files": ["middleware.py"],
    "models_files": ["models.py"],
    #"permissions_files": ["permissions.py"],
    #"serializers_files": ["serializers.py"],
    #"services_files": ["services.py"],
    "signals_files": ["signals.py"],
    #"tasks_files": ["tasks.py"],
    "tests_files": ["tests.py"],
    "urls_files": ["urls.py"],
    "views_files": ["views.py"],
    "utils_files": ["utils.py"],
    #"constants_files": ["constants.py"],
    #"context_processors_files": ["context_processors.py"],
    #"decorators_files": ["decorators.py"],
    #"exceptions_files": ["exceptions.py"],
    #"helpers_files": ["helpers.py"],
    #"mixins_files": ["mixins.py"],
    #"settings_files": ["settings.py"],
    #"tag_files": ["custom_tags.py"],
    #"utilities_files": ["utilities.py"],
    #"validators_files": ["validators.py"],
    #"factories_files": ["factories.py"],
}


def _normalize_patterns(patterns: Iterable[object]) -> List[str]:
    """Normalize configured pattern values into a list of strings."""

    normalized: List[str] = []
    for pattern in patterns:
        if pattern is None:
            continue
        text = str(pattern).strip()
        if text:
            normalized.append(text)
    return normalized


def _load_user_file_groups(config_path: Path) -> Dict[str, List[str]]:
    """Load user-defined file groups from a YAML configuration file."""

    if not config_path.is_file():
        return {}

    if yaml is None:
        warnings.warn(
            "PyYAML is not installed; ignoring user configuration at %s" % config_path,
            RuntimeWarning,
        )
        return {}

    with open(config_path, 'r', encoding='utf-8') as config_file:
        data = yaml.safe_load(config_file) or {}

    file_groups = data.get('file_groups') if isinstance(data, Mapping) else None
    if not isinstance(file_groups, Mapping):
        return {}

    normalized_groups: Dict[str, List[str]] = {}
    for group_name, patterns in file_groups.items():
        if isinstance(patterns, (str, bytes)):
            iterable: Iterable[object] = [patterns]
        elif isinstance(patterns, Iterable):
            iterable = patterns
        else:
            continue

        normalized_groups[str(group_name)] = _normalize_patterns(iterable)

    return normalized_groups


def _merge_file_groups(defaults: Mapping[str, Sequence[str]], overrides: Mapping[str, Sequence[str]]) -> Dict[str, List[str]]:
    """Merge default file groups with user overrides."""

    merged: Dict[str, List[str]] = {name: list(patterns) for name, patterns in defaults.items()}
    for group_name, patterns in overrides.items():
        merged[group_name] = list(patterns)
    return merged


def load_configured_file_groups(project_root: Optional[Path] = None) -> Dict[str, List[str]]:
    """Load the configured file groups, applying user overrides if present."""

    root = project_root or SCRIPT_DIR.parent
    config_path = root / CONFIG_FILE_NAME
    user_groups = _load_user_file_groups(config_path)
    return _merge_file_groups(DEFAULT_FILE_GROUPS, user_groups)


@dataclass
class FileGroupResolver:
    """Resolve file group configuration into matchable patterns."""

    file_groups: Mapping[str, Sequence[str]]

    def __post_init__(self) -> None:
        self._file_groups = {name: tuple(patterns) for name, patterns in self.file_groups.items()}
        self._group_names: Tuple[str, ...] = tuple(self._file_groups.keys())
        self._suffix_map: Dict[str, List[str]] = {}
        self._exact_name_map: Dict[str, List[str]] = {}
        self._glob_patterns: List[Tuple[str, str]] = []

        for group_name, patterns in self._file_groups.items():
            for raw_pattern in patterns:
                pattern = raw_pattern.strip()
                if not pattern:
                    continue
                if pattern.startswith('.') and len(pattern) > 1 and not any(ch in pattern for ch in '*?['):
                    self._suffix_map.setdefault(pattern, []).append(group_name)
                elif any(ch in pattern for ch in '*?[') or '/' in pattern or '\\' in pattern:
                    self._glob_patterns.append((pattern, group_name))
                else:
                    self._exact_name_map.setdefault(pattern, []).append(group_name)

    @property
    def group_names(self) -> Tuple[str, ...]:
        return self._group_names

    def match(self, file_path: Path, project_root: Optional[Path] = None) -> List[str]:
        """Return the ordered list of group names that match the provided file path."""

        matches: List[str] = []
        seen = set()

        def add(group: str) -> None:
            if group not in seen:
                seen.add(group)
                matches.append(group)

        suffix = file_path.suffix
        if suffix and suffix in self._suffix_map:
            for group in self._suffix_map[suffix]:
                add(group)

        name = file_path.name
        if name in self._exact_name_map:
            for group in self._exact_name_map[name]:
                add(group)

        relative_path = None
        if project_root is not None:
            try:
                relative_path = file_path.relative_to(project_root)
            except ValueError:
                relative_path = None

        relative_str = relative_path.as_posix() if isinstance(relative_path, Path) else name
        absolute_str = file_path.as_posix()

        for pattern, group in self._glob_patterns:
            if fnmatch.fnmatch(name, pattern) or fnmatch.fnmatch(relative_str, pattern) or fnmatch.fnmatch(absolute_str, pattern):
                add(group)

        return matches


def _build_file_group_resolver() -> FileGroupResolver:
    configured_groups = load_configured_file_groups()
    return FileGroupResolver(configured_groups)


@lru_cache(maxsize=1)
def get_file_group_resolver() -> FileGroupResolver:
    """Return a cached resolver for the configured file groups."""

    return _build_file_group_resolver()

# Define directories for logging and output
SCRIPT_DIR = Path(__file__).resolve().parent
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
