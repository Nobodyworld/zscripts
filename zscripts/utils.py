"""Filesystem utilities used by :mod:`zscripts` commands."""

from __future__ import annotations

import fnmatch
import logging
import os
import re
from collections.abc import Collection, Iterable, Iterator
from pathlib import Path
from typing import Final, TextIO

from .config import SKIP_DIRS, USER_IGNORE_PATTERNS


class IgnoreMatcher:
    """Match relative paths against glob-style ignore patterns."""

    def __init__(self, patterns: Iterable[str]) -> None:
        compiled: list[tuple[str, re.Pattern[str]]] = []
        for pattern in patterns:
            compiled.append((pattern, re.compile(fnmatch.translate(pattern))))
        self._compiled: Final = compiled

    def matches(self, path: Path | str) -> bool:
        """Return ``True`` if *path* matches any configured ignore pattern."""

        if isinstance(path, Path):
            candidate = path.as_posix()
        else:
            candidate = Path(path).as_posix()

        return any(regex.match(candidate) for _, regex in self._compiled)


LOGGER = logging.getLogger("zscripts.utils")


BASE_IGNORE_PATTERNS: Final[set[str]] = {
    "*.pyc",
    "__pycache__/",
    ".DS_Store",
    "*.sqlite3",
    "db.sqlite3",
    "/staticfiles/",
    "/media/",
    "error.dev.log",
    "error.base.log",
    "error.test.log",
    "error.prod.log",
    "logs",
    "logs/",
    "zscripts",
    "zscripts/",
    "static/",
    "staticfiles/",
    "migrations/",
    "migrations",
    "node_modules/",
    "yarn-error.log",
    "yarn-debug.log",
    "yarn.lock",
    "package-lock.json",
    "package.json",
    "zbuild",
    "zbuild/",
}


def expand_skip_dirs(skip_dirs: Iterable[str]) -> set[str]:
    """Create glob-style patterns that match skip directories."""

    patterns: set[str] = set()
    for skip_dir in skip_dirs:
        if not isinstance(skip_dir, str):
            raise TypeError("Skip directory entries must be strings")

        cleaned = skip_dir.strip("/")
        if not cleaned:
            continue
        patterns.update(
            {
                cleaned,
                f"{cleaned}/",
                f"*/{cleaned}",
                f"*/{cleaned}/",
                f"*/{cleaned}/*",
                f"{cleaned}/*",
            }
        )
    return patterns


def _normalise_user_ignore_patterns(patterns: Iterable[str]) -> set[str]:
    """Validate and normalise user-provided ignore patterns."""

    normalised: set[str] = set()
    for pattern in patterns:
        if not isinstance(pattern, str):
            raise TypeError("User ignore patterns must be strings")

        stripped = pattern.strip()
        if not stripped:
            continue
        if any(control in stripped for control in ("\n", "\r")):
            raise ValueError("User ignore patterns cannot contain newline characters")

        normalised.add(stripped)
    return normalised


def load_gitignore_patterns(
    root_path: Path,
    *,
    skip_dirs: Iterable[str] | None = None,
    user_ignore_patterns: Iterable[str] | None = None,
) -> list[str]:
    """Load ignore patterns from ``.gitignore`` and configuration defaults.

    The legacy behaviour – using the globally configured skip directories and
    user ignore patterns – is preserved when optional arguments are omitted.
    Passing explicit values allows callers that load custom configuration files
    to keep the ignore set aligned with their overrides.
    """

    if not root_path.exists():
        raise FileNotFoundError(f"Project root does not exist: {root_path}")
    if not root_path.is_dir():
        raise NotADirectoryError(f"Project root must be a directory: {root_path}")

    gitignore_path = root_path / ".gitignore"
    patterns = set(BASE_IGNORE_PATTERNS)

    expanded_skip_dirs = expand_skip_dirs(skip_dirs or SKIP_DIRS)
    patterns.update(expanded_skip_dirs)

    if user_ignore_patterns is None:
        patterns.update(USER_IGNORE_PATTERNS)
    else:
        patterns.update(_normalise_user_ignore_patterns(user_ignore_patterns))

    if gitignore_path.is_file():
        with gitignore_path.open("r", encoding="utf-8") as file:
            for line in file:
                stripped_line = line.strip()
                if stripped_line and not stripped_line.startswith("#"):
                    patterns.add(stripped_line)
    return sorted(patterns)


def file_matches_any_pattern(file_path: Path, patterns: Iterable[str]) -> bool:
    """Return ``True`` if *file_path* matches one of *patterns*."""

    candidate = file_path.as_posix()
    return any(fnmatch.fnmatch(candidate, pattern) for pattern in patterns)


def safe_relative_path(project_root: Path, candidate: Path) -> Path:
    """Return *candidate* relative to *project_root* ensuring it does not escape."""

    root_resolved = project_root.resolve()
    candidate_resolved = candidate.resolve()
    try:
        return candidate_resolved.relative_to(root_resolved)
    except ValueError as exc:  # pragma: no cover - defensive guard
        raise ValueError(f"Path {candidate} escapes project root {project_root}") from exc


def _normalise_extensions(extensions: Iterable[str]) -> set[str]:
    return {ext.lower() for ext in extensions}


def _iter_source_files(
    project_root: Path,
    extensions: Collection[str],
    matcher: IgnoreMatcher,
) -> Iterator[tuple[Path, Path, Path]]:
    root_resolved = project_root.resolve()
    extension_set = _normalise_extensions(extensions)

    for root, dirs, files in os.walk(root_resolved, followlinks=False):
        root_path = Path(root)
        if root_path.is_symlink():
            continue

        try:
            relative_root = safe_relative_path(root_resolved, root_path)
        except ValueError:
            continue

        if matcher.matches(relative_root):
            dirs[:] = []
            continue

        dirs[:] = [d for d in dirs if not matcher.matches(relative_root / d)]

        for file_name in sorted(files):
            file_path = root_path / file_name
            if file_path.is_symlink():
                continue

            suffix = file_path.suffix.lower()
            if suffix not in extension_set:
                continue

            try:
                relative_file = safe_relative_path(root_resolved, file_path)
            except ValueError:
                continue

            if matcher.matches(relative_file):
                continue

            yield relative_root, file_path, relative_file


def collect_app_logs(
    project_root: Path,
    log_dir: Path,
    extensions: Collection[str],
    ignore_patterns: Collection[str],
) -> None:
    """Collect matching files grouped by app and write per-app log files."""

    matcher = IgnoreMatcher(ignore_patterns)
    log_dir.mkdir(parents=True, exist_ok=True)

    handles: dict[str, TextIO] = {}

    try:
        for relative_root, file_path, relative_file in _iter_source_files(
            project_root, extensions, matcher
        ):
            app_name = relative_root.parts[0] if relative_root.parts else "root"
            handle = handles.get(app_name)
            if handle is None:
                log_file_path = log_dir / f"{app_name}.txt"
                log_file_path.parent.mkdir(parents=True, exist_ok=True)
                handle = log_file_path.open("w", encoding="utf-8")
                handle.write(f"# {app_name}\n\n")
                handles[app_name] = handle

            try:
                content = file_path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError) as exc:
                LOGGER.warning(
                    "event=collect_app_logs_skipped error_id=FS001 file=%s reason=%s",
                    file_path,
                    exc,
                )
                continue

            handle.write(f"# {relative_file.as_posix()}\n{content}\n\n")
    finally:
        for handle in handles.values():
            handle.close()


def consolidate_files(
    project_root: Path,
    output_path: Path,
    extensions: Collection[str],
    ignore_patterns: Collection[str],
) -> None:
    """Write all matching source files into a single consolidated log."""

    matcher = IgnoreMatcher(ignore_patterns)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as output_file:
        for _, file_path, relative_file in _iter_source_files(project_root, extensions, matcher):
            try:
                content = file_path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError) as exc:
                LOGGER.warning(
                    "event=consolidate_skipped error_id=FS002 file=%s reason=%s",
                    file_path,
                    exc,
                )
                continue
            output_file.write(f"# {relative_file.as_posix()}\n{content}\n\n")


def create_filtered_tree(
    project_root: Path,
    output_path: Path,
    ignore_patterns: Collection[str],
    *,
    include_content: bool = True,
    max_bytes: int = 4096,
) -> None:
    """Write a filtered tree view of *project_root* to *output_path*."""

    matcher = IgnoreMatcher(ignore_patterns)
    root_resolved = project_root.resolve()

    def _walk_tree(current: Path, prefix: str = "") -> Iterator[str]:
        try:
            entries = sorted(current.iterdir())
        except OSError as exc:
            LOGGER.warning(
                "event=tree_walk_failed error_id=FS003 path=%s reason=%s",
                current,
                exc,
            )
            return

        for index, entry in enumerate(entries):
            is_last = index == len(entries) - 1
            connector = "└── " if is_last else "├── "

            try:
                relative_entry = safe_relative_path(root_resolved, entry)
            except ValueError:
                continue

            if matcher.matches(relative_entry):
                continue

            yield f"{prefix}{connector}{entry.name}"

            if entry.is_dir():
                extension = "    " if is_last else "│   "
                yield from _walk_tree(entry, prefix + extension)
            elif include_content and entry.is_file():
                try:
                    content = entry.read_text(encoding="utf-8")
                except (UnicodeDecodeError, OSError) as exc:
                    LOGGER.warning(
                        "event=tree_content_skipped error_id=FS004 path=%s reason=%s",
                        entry,
                        exc,
                    )
                    continue
                trimmed = content[:max_bytes]
                if trimmed:
                    for line in trimmed.splitlines():
                        yield f"{prefix}│   {line}"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as output_file:
        output_file.write(f"{root_resolved.as_posix()}\n")
        for line in _walk_tree(root_resolved):
            output_file.write(f"{line}\n")


__all__ = [
    "IgnoreMatcher",
    "load_gitignore_patterns",
    "expand_skip_dirs",
    "file_matches_any_pattern",
    "collect_app_logs",
    "consolidate_files",
    "create_filtered_tree",
]
