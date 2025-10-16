"""Command line interface for generating zscripts logs."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Iterable, List, Sequence

from .config import (
    LOG_GROUPS,
    SCRIPT_DIR,
    SKIP_DIRS,
)
from .utils import (
    consolidate_files,
    create_app_logs,
    create_filtered_tree,
    load_gitignore_patterns,
)

logger = logging.getLogger(__name__)


def _configure_logging(verbose: bool) -> None:
    """Configure logging for the CLI."""

    level = logging.DEBUG if verbose else logging.INFO
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=level, format="%(levelname)s: %(message)s")
    else:
        logging.getLogger().setLevel(level)


def _resolve_project_root(root_argument: Path | None) -> Path:
    """Resolve the project root to an absolute path."""

    if root_argument is not None:
        return root_argument.expanduser().resolve()
    return SCRIPT_DIR.parent


def _list_groups() -> None:
    """Print the available groups."""

    for key, group in LOG_GROUPS.items():
        print(f"{key:16} {group.description} -> {group.output}")


def _run_app_logs(group, project_root: Path, ignore_patterns: Iterable[str]) -> Path:
    log_dir = group.output
    log_dir.mkdir(parents=True, exist_ok=True)
    create_app_logs(project_root, log_dir, group.file_types or set(), list(ignore_patterns))
    return log_dir


def _run_consolidate(group, project_root: Path, ignore_patterns: Iterable[str]) -> Path:
    log_file_path = group.output
    log_file_path.parent.mkdir(parents=True, exist_ok=True)
    consolidate_files(project_root, log_file_path, group.file_types or set(), list(ignore_patterns))
    return log_file_path


def _run_filtered_tree(group, project_root: Path, ignore_patterns: Iterable[str]) -> Path:
    log_file_path = group.output
    log_file_path.parent.mkdir(parents=True, exist_ok=True)
    patterns: List[str] = list(ignore_patterns)
    if group.include_skip_dirs:
        patterns.extend(SKIP_DIRS)
    create_filtered_tree(project_root, log_file_path, group.file_types, patterns)
    return log_file_path


HANDLERS = {
    'app_logs': _run_app_logs,
    'consolidate': _run_consolidate,
    'filtered_tree': _run_filtered_tree,
}


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point for the CLI."""

    parser = argparse.ArgumentParser(
        description=(
            "Generate per-application logs, consolidated file snapshots, and filtered "
            "directory trees for a project."
        )
    )
    parser.add_argument(
        '--root',
        type=Path,
        help='Optional project root. Defaults to the parent of the zscripts directory.',
    )
    parser.add_argument(
        '-g',
        '--group',
        dest='groups',
        action='append',
        choices=list(LOG_GROUPS.keys()),
        help='Specific group to run. Provide multiple times to run more than one group.',
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List available groups and exit.',
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging output.',
    )

    args = parser.parse_args(argv)

    _configure_logging(args.verbose)

    if args.list:
        _list_groups()
        return 0

    project_root = _resolve_project_root(args.root)
    if not project_root.exists():
        logger.error("The provided project root does not exist: %s", project_root)
        return 2

    base_ignore_patterns = load_gitignore_patterns(project_root)
    group_keys = args.groups or list(LOG_GROUPS.keys())

    logger.info("Project root: %s", project_root)
    logger.info("Groups to process: %s", ', '.join(group_keys))

    exit_code = 0
    for key in group_keys:
        group = LOG_GROUPS[key]
        handler = HANDLERS[group.handler]
        logger.info("Processing group '%s' - %s", group.key, group.description)
        try:
            output_path = handler(group, project_root, base_ignore_patterns)
        except Exception:
            logger.exception("Failed to process group '%s'", group.key)
            exit_code = 1
            continue

        if output_path.is_dir():
            logger.info("Completed '%s'. Outputs written to directory: %s", group.key, output_path)
        else:
            logger.info("Completed '%s'. Output file written to: %s", group.key, output_path)

    return exit_code


__all__ = ['main']
