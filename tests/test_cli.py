from __future__ import annotations

from pathlib import Path

from zscripts.cli import main as cli_main
from zscripts.config import get_config


def test_cli_collect(sample_project_path: Path, tmp_path: Path) -> None:
    config = get_config()
    log_dir = config.collection_logs.get("python", "logs_apps_pyth")
    full_log_dir = sample_project_path.parent / "zscripts" / "logs" / log_dir
    exit_code = cli_main(
        [
            "collect",
            "--types",
            "python",
            "--project-root",
            str(sample_project_path),
        ]
    )
    assert exit_code == 0
    assert full_log_dir.exists()


def test_cli_consolidate(sample_project_path: Path, tmp_path: Path) -> None:
    output = tmp_path / "python.txt"
    exit_code = cli_main(
        [
            "consolidate",
            "--types",
            "python",
            "--project-root",
            str(sample_project_path),
            "--output",
            str(output),
        ]
    )
    assert exit_code == 0
    assert output.exists()


def test_cli_tree(sample_project_path: Path, tmp_path: Path) -> None:
    tree_path = tmp_path / "tree.txt"
    exit_code = cli_main(
        [
            "tree",
            "--project-root",
            str(sample_project_path),
            "--output",
            str(tree_path),
        ]
    )
    assert exit_code == 0
    assert tree_path.exists()
