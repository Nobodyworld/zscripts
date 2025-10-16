"""Command line interface for the :mod:`zscripts` toolkit."""

from __future__ import annotations

import argparse
import logging
import sys
from collections.abc import Callable, Iterable, Mapping, Sequence
from pathlib import Path
from typing import cast

from .config import DEFAULT_CONFIG_PATH, Config, load_config, resolve_paths
from .utils import (
    collect_app_logs,
    consolidate_files,
    create_filtered_tree,
    load_gitignore_patterns,
)

SCRIPT_DIR = Path(__file__).resolve().parent
LOGGER = logging.getLogger("zscripts.cli")
ERROR_ID_UNKNOWN_TYPE = "CLI001"
ERROR_ID_PROJECT_ROOT = "CLI002"
ERROR_ID_RUNTIME = "CLI999"


def _normalise_extensions(source: Mapping[str, Iterable[str]]) -> dict[str, frozenset[str]]:
    return {key: frozenset(ext.lower() for ext in value) for key, value in source.items()}


COLLECT_TYPE_EXTENSIONS = _normalise_extensions(
    {
        "python": (".py",),
        "html": (".html",),
        "css": (".css",),
        "js": (".js",),
        "python_html": (".py", ".html"),
        "all": (".py", ".html", ".js", ".css"),
    }
)

SINGLE_TYPE_EXTENSIONS = _normalise_extensions(
    {
        "python": (".py",),
        "html": (".html",),
        "css": (".css",),
        "js": (".js",),
        "python_html": (".py", ".html"),
        "any": (".py", ".html", ".js", ".css"),
    }
)


class UnknownTypeError(ValueError):
    """Raised when an unknown log type is requested."""


def _parse_type_list(raw: str, *, allowed: Mapping[str, frozenset[str]]) -> tuple[str, ...]:
    requested = tuple(value.strip() for value in raw.split(",") if value.strip())
    if not requested:
        return ()
    for value in requested:
        if value not in allowed:
            raise UnknownTypeError(f"Unsupported type '{value}'. Choose from {sorted(allowed)}")
    return requested


def _build_log_paths(config: Config, base_dir: Path | None = None) -> dict[str, Path]:
    resolved = resolve_paths(config)
    root = base_dir or resolved.log_dir
    logs = config.collection_logs
    return {
        "all": root / logs.get("all", "logs_apps_all"),
        "python": root / logs.get("python", "logs_apps_pyth"),
        "html": root / logs.get("html", "logs_apps_html"),
        "css": root / logs.get("css", "logs_apps_css"),
        "js": root / logs.get("js", "logs_apps_js"),
        "python_html": root / logs.get("python_html", "logs_apps_both"),
        "single": root / logs.get("single", "logs_single_files"),
    }


def _build_single_targets(config: Config, base_dir: Path | None = None) -> dict[str, Path]:
    resolved = resolve_paths(config)
    root = base_dir or resolved.single_log_dir.parent
    single_dir = root / config.collection_logs.get("single", "logs_single_files")
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
    return load_gitignore_patterns(
        project_root,
        skip_dirs=config.skip,
        user_ignore_patterns=config.user_ignore_patterns,
    )


def _resolve_project_root(raw_root: str, *, sample: bool) -> Path:
    if sample:
        project_root = SCRIPT_DIR.parent / "sample_project"
    else:
        project_root = Path(raw_root).expanduser()

    resolved = project_root.resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"Project root does not exist: {resolved}")
    return resolved


def collect_command(args: argparse.Namespace) -> None:
    config_arg = cast(Path | str | None, getattr(args, "config", None))
    project_root_arg = cast(str, getattr(args, "project_root", "."))
    types_arg = cast(str, getattr(args, "types", "python"))
    output_dir_arg = cast(str | None, getattr(args, "output_dir", None))
    sample_flag = cast(bool, getattr(args, "sample", False))

    LOGGER.info("event=collect start project_root=%s", project_root_arg)
    config = load_config(config_arg)
    type_names = _parse_type_list(types_arg, allowed=COLLECT_TYPE_EXTENSIONS)
    if not type_names:
        type_names = ("python",)

    project_root = _resolve_project_root(project_root_arg, sample=sample_flag)
    output_base = Path(output_dir_arg).expanduser().resolve() if output_dir_arg else None

    log_paths = _build_log_paths(config, output_base)
    base_output_dir = next(iter(log_paths.values())).parent
    ignore_patterns = _augment_ignore_patterns(project_root, config)

    print(f"Scanning project: {project_root}")
    print(f"Output directory: {base_output_dir}")

    for type_name in type_names:
        log_dir = log_paths[type_name]
        log_dir.mkdir(parents=True, exist_ok=True)
        collect_app_logs(project_root, log_dir, COLLECT_TYPE_EXTENSIONS[type_name], ignore_patterns)
        LOGGER.info("event=collect_completed type=%s output=%s", type_name, log_dir)
        print(f"✓ Created {type_name} logs at {log_dir}")

    print(f"\n📁 View logs at: {base_output_dir}")


def consolidate_command(args: argparse.Namespace) -> None:
    config_arg = cast(Path | str | None, getattr(args, "config", None))
    project_root_arg = cast(str, getattr(args, "project_root", "."))
    types_arg = cast(str, getattr(args, "types", "python"))
    output_dir_arg = cast(str | None, getattr(args, "output_dir", None))
    output_arg = cast(str | None, getattr(args, "output", None))
    sample_flag = cast(bool, getattr(args, "sample", False))

    LOGGER.info("event=consolidate start project_root=%s", project_root_arg)
    config = load_config(config_arg)
    type_names = _parse_type_list(types_arg, allowed=SINGLE_TYPE_EXTENSIONS)
    if len(type_names) != 1:
        raise UnknownTypeError("Consolidate command accepts a single type value")

    type_name = type_names[0] if type_names else "python"
    project_root = _resolve_project_root(project_root_arg, sample=sample_flag)

    output_base = Path(output_dir_arg).expanduser().resolve() if output_dir_arg else None
    targets = _build_single_targets(config, output_base)

    output_path = Path(output_arg).expanduser().resolve() if output_arg else targets[type_name]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    ignore_patterns = _augment_ignore_patterns(project_root, config)
    consolidate_files(project_root, output_path, SINGLE_TYPE_EXTENSIONS[type_name], ignore_patterns)
    LOGGER.info("event=consolidate_completed type=%s output=%s", type_name, output_path)
    print(f"✓ Consolidated {type_name} sources into {output_path}")


def tree_command(args: argparse.Namespace) -> None:
    config_arg = cast(Path | str | None, getattr(args, "config", None))
    project_root_arg = cast(str, getattr(args, "project_root", "."))
    output_dir_arg = cast(str | None, getattr(args, "output_dir", None))
    output_arg = cast(str | None, getattr(args, "output", None))
    include_contents = cast(bool, getattr(args, "include_contents", False))
    sample_flag = cast(bool, getattr(args, "sample", False))

    LOGGER.info("event=tree start project_root=%s", project_root_arg)
    config = load_config(config_arg)
    project_root = _resolve_project_root(project_root_arg, sample=sample_flag)

    if output_dir_arg:
        output_base = Path(output_dir_arg).expanduser().resolve()
        output_path = output_base / "project_tree.txt"
    elif output_arg:
        output_path = Path(output_arg).expanduser().resolve()
    else:
        default_base = next(iter(_build_log_paths(config).values())).parent
        output_path = default_base / "project_tree.txt"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    ignore_patterns = _augment_ignore_patterns(project_root, config)
    create_filtered_tree(
        project_root,
        output_path,
        ignore_patterns,
        include_content=include_contents,
    )
    LOGGER.info("event=tree_completed output=%s", output_path)
    print(f"✓ Wrote project tree to {output_path}")


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
    subparser.add_argument(
        "--output-dir",
        default=None,
        help="Custom output directory for logs (default: configuration log root)",
    )
    subparser.add_argument(
        "--sample",
        action="store_true",
        help="Run against the included sample project",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="CLI front-end for zscripts utilities")
    subparsers = parser.add_subparsers(dest="command", required=True)

    collect_parser = subparsers.add_parser(
        "collect", help="Generate per-app logs for selected stacks"
    )
    _add_shared_arguments(collect_parser)
    collect_parser.add_argument(
        "--types",
        default="python",
        help="Comma separated list of stacks to capture (choices: python, html, css, js, python_html, all)",
    )
    collect_parser.set_defaults(func=collect_command)

    consolidate_parser = subparsers.add_parser(
        "consolidate", help="Create a single consolidated log file"
    )
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

    tree_parser = subparsers.add_parser(
        "tree", help="Snapshot the project tree with filtered sources"
    )
    _add_shared_arguments(tree_parser)
    tree_parser.add_argument(
        "--output",
        help="Optional custom output file for the tree snapshot",
    )
    tree_parser.add_argument(
        "--include-contents",
        action="store_true",
        help="Include file contents in the tree output",
    )
    tree_parser.set_defaults(func=tree_command)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    command = cast(str, getattr(args, "command", ""))
    handler: Callable[[argparse.Namespace], None] | None = getattr(args, "func", None)
    if handler is None:
        parser.error("No command specified")

    try:
        handler(args)
    except UnknownTypeError as exc:
        LOGGER.error(
            "event=cli_error error_id=%s command=%s reason=%s",
            ERROR_ID_UNKNOWN_TYPE,
            command,
            exc,
        )
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except FileNotFoundError as exc:
        LOGGER.error(
            "event=cli_error error_id=%s command=%s reason=%s",
            ERROR_ID_PROJECT_ROOT,
            command,
            exc,
        )
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except ValueError as exc:
        LOGGER.error(
            "event=cli_error error_id=%s command=%s reason=%s",
            ERROR_ID_RUNTIME,
            command,
            exc,
        )
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except RuntimeError as exc:
        LOGGER.error(
            "event=cli_error error_id=%s command=%s reason=%s",
            ERROR_ID_RUNTIME,
            command,
            exc,
        )
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        LOGGER.exception("event=cli_error error_id=%s command=%s", ERROR_ID_RUNTIME, command)
        print(f"os error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
