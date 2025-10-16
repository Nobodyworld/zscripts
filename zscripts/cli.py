"""Lightweight command line interface for zscripts."""

from __future__ import annotations

import argparse
from collections.abc import Iterable, Sequence
from pathlib import Path

from .config import (
    DEFAULT_CONFIG_PATH,
    SCRIPT_DIR,
    Config,
    load_config,
)
from .utils import (
    collect_app_logs,
    consolidate_files,
    create_filtered_tree,
    load_gitignore_patterns,
)

COLLECT_TYPE_EXTENSIONS = {
    "python": {".py"},
    "html": {".html"},
    "css": {".css"},
    "js": {".js"},
    "python_html": {".py", ".html"},
    "all": {".py", ".html", ".js", ".css"},
}

SINGLE_TYPE_EXTENSIONS = {
    "python": {".py"},
    "html": {".html"},
    "css": {".css"},
    "js": {".js"},
    "python_html": {".py", ".html"},
    "any": {".py", ".html", ".js", ".css"},
}


class UnknownTypeError(ValueError):
    """Raised when an unknown log type is requested."""


def _parse_type_list(raw: str, *, allowed: Iterable[str]) -> Sequence[str]:
    requested = [value.strip() for value in raw.split(",") if value.strip()]
    if not requested:
        return ()
    for value in requested:
        if value not in allowed:
            raise UnknownTypeError(f"Unsupported type '{value}'. Choose from {sorted(allowed)}")
    return requested


def _build_log_paths(config: Config) -> dict[str, Path]:
    directories = config.directories
    collection_logs = config.collection_logs
    log_root = SCRIPT_DIR / directories.get("log_root", "logs")
    return {
        "all": log_root / collection_logs.get("all", "logs_apps_all"),
        "python": log_root / collection_logs.get("python", "logs_apps_pyth"),
        "html": log_root / collection_logs.get("html", "logs_apps_html"),
        "css": log_root / collection_logs.get("css", "logs_apps_css"),
        "js": log_root / collection_logs.get("js", "logs_apps_js"),
        "python_html": log_root / collection_logs.get("python_html", "logs_apps_both"),
        "single": log_root / collection_logs.get("single", "logs_single_files"),
    }


def _build_single_targets(config: Config) -> dict[str, Path]:
    log_paths = _build_log_paths(config)
    single_dir = log_paths["single"]
    targets = config.single_targets
    return {
        "python": single_dir / targets.get("python", "capture_all_pyth.txt"),
        "html": single_dir / targets.get("html", "capture_all_html.txt"),
        "css": single_dir / targets.get("css", "capture_all_css.txt"),
        "js": single_dir / targets.get("js", "capture_all_js.txt"),
        "python_html": single_dir / targets.get("python_html", "capture_all_python_html.txt"),
        "any": single_dir / targets.get("any", "capture_all.txt"),
    }


def _augment_ignore_patterns(project_root: Path, config: Config) -> list[str]:
    ignore_patterns = list(load_gitignore_patterns(project_root))
    skip_values = config.skip
    for skip in skip_values:
        ignore_patterns.append(skip)
        ignore_patterns.append(f"{skip}/")
    return ignore_patterns


def collect_command(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    type_names = _parse_type_list(args.types, allowed=COLLECT_TYPE_EXTENSIONS.keys())
    if not type_names:
        type_names = ("python",)

    project_root = Path(args.project_root).resolve()
    log_paths = _build_log_paths(config)
    ignore_patterns = _augment_ignore_patterns(project_root, config)

    for type_name in type_names:
        log_dir = log_paths[type_name]
        log_dir.mkdir(parents=True, exist_ok=True)
        collect_app_logs(project_root, log_dir, COLLECT_TYPE_EXTENSIONS[type_name], ignore_patterns)
        print(f"Created {type_name} logs at {log_dir}")


def consolidate_command(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    type_names = _parse_type_list(args.types, allowed=SINGLE_TYPE_EXTENSIONS.keys())
    if len(type_names) != 1:
        raise UnknownTypeError("Consolidate command accepts a single type value")

    type_name = type_names[0] if type_names else "python"
    project_root = Path(args.project_root).resolve()
    targets = _build_single_targets(config)
    output_path = Path(args.output) if args.output else targets[type_name]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    ignore_patterns = _augment_ignore_patterns(project_root, config)
    consolidate_files(project_root, output_path, SINGLE_TYPE_EXTENSIONS[type_name], ignore_patterns)
    print(f"Consolidated {type_name} sources into {output_path}")


def tree_command(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    project_root = Path(args.project_root).resolve()
    output_path = Path(args.output) if args.output else (_build_log_paths(config)["single"] / "tree.txt")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    ignore_patterns = _augment_ignore_patterns(project_root, config)
    create_filtered_tree(project_root, output_path, ignore_patterns=ignore_patterns)
    print(f"Wrote project tree to {output_path}")


def _add_shared_arguments(subparser: argparse.ArgumentParser) -> None:
    subparser.add_argument(
        "--config",
        default=None,
        help=f"Path to a zscripts configuration file (default: {DEFAULT_CONFIG_PATH})",
    )
    subparser.add_argument(
        "--project-root",
        default=".",
        help="Root directory to scan (default: current directory)",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="CLI front-end for zscripts utilities")
    subparsers = parser.add_subparsers(dest="command", required=True)

    collect_parser = subparsers.add_parser("collect", help="Generate per-app logs for selected stacks")
    _add_shared_arguments(collect_parser)
    collect_parser.add_argument(
        "--types",
        default="python",
        help="Comma separated list of stacks to capture (choices: python, html, css, js, python_html, all)",
    )
    collect_parser.set_defaults(func=collect_command)

    consolidate_parser = subparsers.add_parser("consolidate", help="Create a single consolidated log file")
    _add_shared_arguments(consolidate_parser)
    consolidate_parser.add_argument(
        "--types",
        default="python",
        help="Select the source stack to consolidate (choices: python, html, css, js, python_html, any)",
    )
    consolidate_parser.add_argument(
        "--output",
        help="Optional custom output path for the consolidated log",
    )
    consolidate_parser.set_defaults(func=consolidate_command)

    tree_parser = subparsers.add_parser("tree", help="Snapshot the project tree with filtered sources")
    _add_shared_arguments(tree_parser)
    tree_parser.add_argument(
        "--output",
        help="Optional custom output file for the tree snapshot",
    )
    tree_parser.set_defaults(func=tree_command)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
