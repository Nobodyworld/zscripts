# zscripts/utils.py
"""Utility helpers shared across the zscripts project.

The module makes use of configuration values declared in :mod:`zscripts.config`
which now allow user extensions through ``config.json``.  In particular the
``ignore_patterns`` and ``skip_dirs`` settings augment the logic in
:func:`load_gitignore_patterns` to ensure custom exclusions propagate through
all tools consistently.
"""

import fnmatch
import os
from pathlib import Path

try:  # Prefer package-relative imports but retain compatibility with legacy entry points.
    from .config import SKIP_DIRS, USER_IGNORE_PATTERNS  # type: ignore[attr-defined]
except ImportError:  # pragma: no cover - fallback for direct script execution
    from config import SKIP_DIRS, USER_IGNORE_PATTERNS  # type: ignore[attr-defined]
from collections.abc import Iterable, Set


class IgnoreMatcher:
    """A matcher for file paths against ignore patterns."""

    def __init__(self, patterns: Iterable[str]) -> None:
        self.patterns = list(patterns)

    def matches(self, path: Path) -> bool:
        """Check if the path matches any ignore pattern."""
        path_str = str(path)
        for pattern in self.patterns:
            if fnmatch.fnmatch(path_str, pattern):
                return True
        return False


BASE_IGNORE_PATTERNS = {
    '*.pyc',
    '__pycache__/',
    '.DS_Store',
    '*.sqlite3',
    'db.sqlite3',
    '/staticfiles/',
    '/media/',
    'error.dev.log',
    'error.base.log',
    'error.test.log',
    'error.prod.log',
    'logs',
    'logs/',
    'zscripts',
    'zscripts/',
    'static/',
    'staticfiles/',
    'migrations/',
    'migrations',
    'node_modules/',
    'yarn-error.log',
    'yarn-debug.log',
    'yarn.lock',
    'package-lock.json',
    'package.json',
    'zbuild',
    'zbuild/'
}


def expand_skip_dirs(skip_dirs: Iterable[str]) -> Set[str]:
    """Create glob-style patterns that match the provided skip directories."""

    patterns: Set[str] = set()
    for skip_dir in skip_dirs:
        cleaned = skip_dir.strip('/')
        if not cleaned:
            continue
        patterns.update({
            cleaned,
            f"{cleaned}/",
            f"*/{cleaned}",
            f"*/{cleaned}/",
            f"*/{cleaned}/*",
            f"{cleaned}/*",
        })
    return patterns


def load_gitignore_patterns(root_path: Path) -> list[str]:
    """
    Load ignore patterns from several sources for consistent filtering.

    The resulting set merges patterns from the local ``.gitignore`` file,
    built-in defaults, :data:`config.SKIP_DIRS`, and any
    ``ignore_patterns`` entries defined in ``config.json``.

    Args:
        root_path (Path): The root directory path where the .gitignore file is located.

    Returns:
        list: A list of patterns to ignore.
    """
    gitignore_path = root_path / '.gitignore'
    patterns = set(BASE_IGNORE_PATTERNS)
    patterns.update(USER_IGNORE_PATTERNS)
    patterns.update(expand_skip_dirs(SKIP_DIRS))
    if gitignore_path.is_file():
        with gitignore_path.open('r', encoding='utf-8') as file:
            for line in file:
                stripped_line = line.strip()
                if stripped_line and not stripped_line.startswith('#'):
                    patterns.add(stripped_line)
    return sorted(patterns)


def file_matches_any_pattern(file_path: Path, patterns: Iterable[str]) -> bool:
    """
    Checks if a file path matches any pattern in the provided collection.

    Args:
        file_path (Path): The path of the file to check.
        patterns (Iterable[str]): A collection of patterns to match against.

    Returns:
        bool: True if the file path matches any pattern, False otherwise.
    """
    file_path_str = str(file_path)
    for pattern in patterns:
        if fnmatch.fnmatch(file_path_str, pattern):
            return True
    return False


def collect_app_logs(
    project_root: Path,
    log_dir: Path,
    extensions: Set[str],
    ignore_patterns: list[str],
) -> None:
    """
    Collect and log source files by application directory.

    Args:
        project_root (Path): The root directory of the project.
        log_dir (Path): The directory where logs will be written.
        extensions (Set[str]): File extensions to include.
        ignore_patterns (list[str]): Patterns to ignore.
    """
    matcher = IgnoreMatcher(ignore_patterns)
    app_logs: dict[str, list[str]] = {}

    for root, dirs, files in os.walk(project_root):
        root_path = Path(root)
        relative_root = root_path.relative_to(project_root)

        # Skip ignored directories
        dirs[:] = [d for d in dirs if not matcher.matches(relative_root / d)]

        if matcher.matches(relative_root):
            continue

        app_name = relative_root.parts[0] if relative_root.parts else "root"
        app_logs.setdefault(app_name, [])

        for file in files:
            file_path = root_path / file
            if file_path.suffix in extensions and not matcher.matches(file_path.relative_to(project_root)):
                try:
                    content = file_path.read_text(encoding='utf-8')
                    app_logs[app_name].append(f"# {file_path.relative_to(project_root)}\n{content}\n")
                except (UnicodeDecodeError, OSError):
                    continue  # Skip binary or unreadable files

    for app_name, entries in app_logs.items():
        if entries:
            log_file_path = log_dir / f"{app_name}.txt"
            log_file_path.parent.mkdir(parents=True, exist_ok=True)
            with log_file_path.open('w', encoding='utf-8') as log_file:
                log_file.write(f"# {app_name}\n\n")
                for entry in entries:
                    log_file.write(entry)


def consolidate_files(
    project_root: Path,
    output_path: Path,
    extensions: Set[str],
    ignore_patterns: list[str],
) -> None:
    """
    Consolidate all matching files into a single output file.

    Args:
        project_root (Path): The root directory of the project.
        output_path (Path): The path to the output file.
        extensions (Set[str]): File extensions to include.
        ignore_patterns (list[str]): Patterns to ignore.
    """
    matcher = IgnoreMatcher(ignore_patterns)
    consolidated: list[str] = []

    for root, dirs, files in os.walk(project_root):
        root_path = Path(root)
        relative_root = root_path.relative_to(project_root)

        # Skip ignored directories
        dirs[:] = [d for d in dirs if not matcher.matches(relative_root / d)]

        if matcher.matches(relative_root):
            continue

        for file in files:
            file_path = root_path / file
            if file_path.suffix in extensions and not matcher.matches(file_path.relative_to(project_root)):
                try:
                    content = file_path.read_text(encoding='utf-8')
                    consolidated.append(f"# {file_path.relative_to(project_root)}\n{content}\n")
                except (UnicodeDecodeError, OSError):
                    continue  # Skip binary or unreadable files

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open('w', encoding='utf-8') as output_file:
        for entry in consolidated:
            output_file.write(entry)


def create_filtered_tree(
    project_root: Path,
    output_path: Path,
    ignore_patterns: list[str],
    *,
    include_content: bool = True,
) -> None:
    """
    Create a filtered tree view of the project with optional file contents.

    Args:
        project_root (Path): The root directory of the project.
        output_path (Path): The path to the output file.
        ignore_patterns (list[str]): Patterns to ignore.
        include_content (bool): Whether to include file contents.
    """
    matcher = IgnoreMatcher(ignore_patterns)

    def _walk_tree(path: Path, prefix: str = "") -> list[str]:
        lines: list[str] = []
        try:
            entries = sorted(path.iterdir())
        except OSError:
            return lines

        for i, entry in enumerate(entries):
            is_last = i == len(entries) - 1
            connector = "└── " if is_last else "├── "
            relative_entry = entry.relative_to(project_root)

            if matcher.matches(relative_entry):
                continue

            lines.append(f"{prefix}{connector}{entry.name}")

            if entry.is_dir():
                extension = "    " if is_last else "│   "
                lines.extend(_walk_tree(entry, prefix + extension))
            elif include_content and entry.is_file():
                try:
                    content = entry.read_text(encoding='utf-8')
                    indented_content = "\n".join(f"{prefix}│   {line}" for line in content.splitlines())
                    lines.append(f"{prefix}│   {indented_content}")
                except (UnicodeDecodeError, OSError):
                    pass  # Skip binary or unreadable files

        return lines

    tree_lines = [str(project_root)] + _walk_tree(project_root)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open('w', encoding='utf-8') as output_file:
        for line in tree_lines:
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
