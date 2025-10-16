"""Utilities for loading and interpreting ``zscripts`` configuration."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import TypeAlias, TypedDict, cast

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_CONFIG_PATH = SCRIPT_DIR.parent / "zscripts.config.json"

JSONPrimitive: TypeAlias = str | int | float | bool | None
JSONValue: TypeAlias = JSONPrimitive | list["JSONValue"] | dict[str, "JSONValue"]
JSONMapping: TypeAlias = Mapping[str, JSONValue]


class SerializableConfig(TypedDict):
    skip: list[str]
    file_types: dict[str, str]
    user_ignore_patterns: list[str]
    directories: dict[str, str]
    collection_logs: dict[str, str]
    single_targets: dict[str, str]


@dataclass(frozen=True)
class Config:
    """Immutable snapshot of configuration values loaded from JSON."""

    skip: tuple[str, ...]
    file_types: dict[str, str]
    user_ignore_patterns: frozenset[str]
    directories: dict[str, str]
    collection_logs: dict[str, str]
    single_targets: dict[str, str]

    def to_dict(self) -> SerializableConfig:
        return {
            "skip": list(self.skip),
            "file_types": dict(self.file_types),
            "user_ignore_patterns": sorted(self.user_ignore_patterns),
            "directories": dict(self.directories),
            "collection_logs": dict(self.collection_logs),
            "single_targets": dict(self.single_targets),
        }


@dataclass(frozen=True)
class ResolvedPaths:
    """Concrete filesystem locations derived from configuration settings."""

    log_dir: Path
    build_dir: Path
    analysis_dir: Path
    consolidation_dir: Path
    work_dir: Path
    all_log_dir: Path
    python_log_dir: Path
    html_log_dir: Path
    css_log_dir: Path
    js_log_dir: Path
    python_html_log_dir: Path
    single_log_dir: Path
    capture_all_python_log: Path
    capture_all_html_log: Path
    capture_all_css_log: Path
    capture_all_js_log: Path
    capture_all_python_html_log: Path
    capture_all_log: Path


def _load_raw_config(config_path: Path | None = None) -> dict[str, JSONValue]:
    path = config_path or DEFAULT_CONFIG_PATH
    try:
        with path.open("r", encoding="utf-8") as handle:
            data: object = json.load(handle)
    except FileNotFoundError as exc:  # pragma: no cover - defensive guard
        raise RuntimeError(
            f"Configuration file not found: {path}. Ensure zscripts.config.json exists."
        ) from exc
    except json.JSONDecodeError as exc:  # pragma: no cover - defensive guard
        raise RuntimeError(f"Configuration file {path} is not valid JSON") from exc

    if not isinstance(data, dict):
        raise RuntimeError("Configuration root must be a JSON object")
    return cast(dict[str, JSONValue], data)


def _ensure_iterable_of_strings(value: JSONValue | None, *, name: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str | bytes) or not isinstance(value, Iterable):
        raise RuntimeError(f"Expected '{name}' to be an iterable of strings")

    seen: list[str] = []
    iterable_value = cast(Iterable[object], value)
    for item in iterable_value:
        if not isinstance(item, str):
            raise RuntimeError(f"Configuration entry '{name}' must contain only strings")
        normalised = item.strip()
        if normalised and normalised not in seen:
            seen.append(normalised)
    return tuple(seen)


def _ensure_mapping_of_strings(value: JSONValue | None, *, name: str) -> dict[str, str]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise RuntimeError(f"Expected '{name}' to be a mapping of string keys to string values")

    result: dict[str, str] = {}
    mapping_value = cast(Mapping[object, object], value)
    for key, raw_value in mapping_value.items():
        if not isinstance(key, str) or not isinstance(raw_value, str):
            raise RuntimeError(f"Configuration entry '{name}' must contain only string keys/values")
        key_stripped = key.strip()
        if not key_stripped:
            continue
        result[key_stripped] = raw_value.strip()
    return result


def _normalise_raw_config(raw: JSONMapping) -> Config:
    return Config(
        skip=_ensure_iterable_of_strings(raw.get("skip"), name="skip"),
        file_types=_ensure_mapping_of_strings(raw.get("file_types"), name="file_types"),
        user_ignore_patterns=frozenset(
            _ensure_iterable_of_strings(
                raw.get("user_ignore_patterns"), name="user_ignore_patterns"
            )
        ),
        directories=_ensure_mapping_of_strings(raw.get("directories"), name="directories"),
        collection_logs=_ensure_mapping_of_strings(
            raw.get("collection_logs"), name="collection_logs"
        ),
        single_targets=_ensure_mapping_of_strings(raw.get("single_targets"), name="single_targets"),
    )


def _merge_config_data(defaults: Config, overrides: Config) -> Config:
    combined_skip: list[str] = list(defaults.skip)
    for value in overrides.skip:
        if value not in combined_skip:
            combined_skip.append(value)
    skip = tuple(combined_skip)
    file_types = defaults.file_types | overrides.file_types
    user_ignore_patterns = defaults.user_ignore_patterns | overrides.user_ignore_patterns
    directories = defaults.directories | overrides.directories
    collection_logs = defaults.collection_logs | overrides.collection_logs
    single_targets = defaults.single_targets | overrides.single_targets

    return Config(
        skip=skip,
        file_types=file_types,
        user_ignore_patterns=user_ignore_patterns,
        directories=directories,
        collection_logs=collection_logs,
        single_targets=single_targets,
    )


def resolve_paths(config: Config, *, base_dir: Path | None = None) -> ResolvedPaths:
    root_dir = (base_dir or SCRIPT_DIR).resolve()

    log_dir = root_dir / config.directories.get("log_root", "logs")
    analysis_dir = log_dir / config.directories.get("analysis", "analysis_logs")
    build_dir = log_dir / config.directories.get("build", "build_files")
    consolidation_dir = log_dir / config.directories.get("consolidation", "consoli_files")
    work_dir = log_dir / config.directories.get("work", "logs_files")

    all_log_dir = log_dir / config.collection_logs.get("all", "logs_apps_all")
    python_log_dir = log_dir / config.collection_logs.get("python", "logs_apps_pyth")
    html_log_dir = log_dir / config.collection_logs.get("html", "logs_apps_html")
    css_log_dir = log_dir / config.collection_logs.get("css", "logs_apps_css")
    js_log_dir = log_dir / config.collection_logs.get("js", "logs_apps_js")
    python_html_log_dir = log_dir / config.collection_logs.get("python_html", "logs_apps_both")
    single_log_dir = log_dir / config.collection_logs.get("single", "logs_single_files")

    capture_all_python_log = single_log_dir / config.single_targets.get(
        "python", "capture_all_pyth.txt"
    )
    capture_all_html_log = single_log_dir / config.single_targets.get(
        "html", "capture_all_html.txt"
    )
    capture_all_css_log = single_log_dir / config.single_targets.get("css", "capture_all_css.txt")
    capture_all_js_log = single_log_dir / config.single_targets.get("js", "capture_all_js.txt")
    capture_all_python_html_log = single_log_dir / config.single_targets.get(
        "python_html", "capture_all_python_html.txt"
    )
    capture_all_log = single_log_dir / config.single_targets.get("any", "capture_all.txt")

    return ResolvedPaths(
        log_dir=log_dir,
        build_dir=build_dir,
        analysis_dir=analysis_dir,
        consolidation_dir=consolidation_dir,
        work_dir=work_dir,
        all_log_dir=all_log_dir,
        python_log_dir=python_log_dir,
        html_log_dir=html_log_dir,
        css_log_dir=css_log_dir,
        js_log_dir=js_log_dir,
        python_html_log_dir=python_html_log_dir,
        single_log_dir=single_log_dir,
        capture_all_python_log=capture_all_python_log,
        capture_all_html_log=capture_all_html_log,
        capture_all_css_log=capture_all_css_log,
        capture_all_js_log=capture_all_js_log,
        capture_all_python_html_log=capture_all_python_html_log,
        capture_all_log=capture_all_log,
    )


_DEFAULT_CONFIG = _normalise_raw_config(_load_raw_config())
_PATHS = resolve_paths(_DEFAULT_CONFIG)

SKIP_DIRS = _DEFAULT_CONFIG.skip
FILE_TYPES = dict(_DEFAULT_CONFIG.file_types)
USER_IGNORE_PATTERNS = _DEFAULT_CONFIG.user_ignore_patterns

LOG_DIR = _PATHS.log_dir
BUILD_DIR = _PATHS.build_dir
ANALYSIS_DIR = _PATHS.analysis_dir
CONSOLIDATION_DIR = _PATHS.consolidation_dir
WORK_DIR = _PATHS.work_dir

ALL_LOG_DIR = _PATHS.all_log_dir
PYTHON_LOG_DIR = _PATHS.python_log_dir
HTML_LOG_DIR = _PATHS.html_log_dir
CSS_LOG_DIR = _PATHS.css_log_dir
JS_LOG_DIR = _PATHS.js_log_dir
BOTH_LOG_DIR = _PATHS.python_html_log_dir
SINGLE_LOG_DIR = _PATHS.single_log_dir

CAPTURE_ALL_PYTHON_LOG = _PATHS.capture_all_python_log
CAPTURE_ALL_HTML_LOG = _PATHS.capture_all_html_log
CAPTURE_ALL_CSS_LOG = _PATHS.capture_all_css_log
CAPTURE_ALL_JS_LOG = _PATHS.capture_all_js_log
CAPTURE_ALL_PYTHON_HTML_LOG = _PATHS.capture_all_python_html_log
CAPTURE_ALL_LOG = _PATHS.capture_all_log


def load_config(path: Path | str | None = None) -> Config:
    if path is None:
        return _DEFAULT_CONFIG

    override_path = Path(path)
    overrides = _normalise_raw_config(_load_raw_config(override_path))
    return _merge_config_data(_DEFAULT_CONFIG, overrides)


def get_config() -> Config:
    return _DEFAULT_CONFIG


def get_file_group_resolver() -> dict[str, str]:
    return dict(_DEFAULT_CONFIG.file_types)


__all__ = [
    "Config",
    "DEFAULT_CONFIG_PATH",
    "ResolvedPaths",
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
    "resolve_paths",
    "get_config",
    "get_file_group_resolver",
]
