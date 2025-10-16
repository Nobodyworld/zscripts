from __future__ import annotations

from pathlib import Path

import pytest

from zscripts.utils import IgnoreMatcher, collect_app_logs, consolidate_files, create_filtered_tree


@pytest.fixture()
def sample_project_path(tmp_path: Path) -> Path:
    """Create a minimal sample project for testing."""
    project = tmp_path / "sample"
    project.mkdir()

    # Create backend file
    backend = project / "backend"
    backend.mkdir()
    (backend / "service.py").write_text("# Backend service\n\ndef hello():\n    return 'world'\n")

    # Create frontend file
    frontend = project / "frontend"
    frontend.mkdir()
    (frontend / "App.jsx").write_text("// Frontend app\nconst App = () => <div>Hello</div>;\n")

    return project


def test_ignore_matcher() -> None:
    matcher = IgnoreMatcher(["*.pyc", "__pycache__/"])
    assert matcher.matches(Path("__pycache__/module.pyc"))
    assert not matcher.matches(Path("module.py"))


def test_collect_app_logs(sample_project_path: Path, tmp_path: Path) -> None:
    log_dir = tmp_path / "logs"
    ignore_patterns = ["__pycache__"]
    collect_app_logs(sample_project_path, log_dir, {".py"}, ignore_patterns)

    backend_log = log_dir / "backend.txt"
    assert backend_log.exists()
    content = backend_log.read_text()
    assert "# Backend service" in content


def test_consolidate_files(sample_project_path: Path, tmp_path: Path) -> None:
    output_path = tmp_path / "consolidated.txt"
    ignore_patterns = ["__pycache__"]
    consolidate_files(sample_project_path, output_path, {".py"}, ignore_patterns)

    assert output_path.exists()
    content = output_path.read_text()
    assert "# Backend service" in content


def test_create_filtered_tree(sample_project_path: Path, tmp_path: Path) -> None:
    output_path = tmp_path / "tree.txt"
    ignore_patterns = ["__pycache__"]
    create_filtered_tree(sample_project_path, output_path, ignore_patterns)

    assert output_path.exists()
    content = output_path.read_text()
    assert "backend" in content
    assert "frontend" in content
