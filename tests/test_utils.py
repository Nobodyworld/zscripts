from __future__ import annotations

import random
import string
from pathlib import Path

import pytest

from zscripts.utils import (
    IgnoreMatcher,
    collect_app_logs,
    consolidate_files,
    create_filtered_tree,
    expand_skip_dirs,
    load_gitignore_patterns,
)


@pytest.fixture()
def sample_project_path(tmp_path: Path) -> Path:
    project = tmp_path / "sample"
    project.mkdir()

    backend = project / "backend"
    backend.mkdir()
    (backend / "service.py").write_text("# Backend service\n\ndef hello():\n    return 'world'\n")

    frontend = project / "frontend"
    frontend.mkdir()
    (frontend / "App.jsx").write_text("// Frontend app\nconst App = () => <div>Hello</div>;\n")

    return project


def test_ignore_matcher_matches_glob_patterns() -> None:
    matcher = IgnoreMatcher(["*.pyc", "__pycache__/"])
    assert matcher.matches(Path("__pycache__/module.pyc"))
    assert not matcher.matches(Path("module.py"))


def test_collect_app_logs_ignores_symlinks(sample_project_path: Path, tmp_path: Path) -> None:
    outside_file = tmp_path / "outside.py"
    outside_file.write_text("print('outside')\n", encoding="utf-8")
    (sample_project_path / "backend" / "escape.py").symlink_to(outside_file)

    log_dir = tmp_path / "logs"
    collect_app_logs(sample_project_path, log_dir, {".py"}, [])

    backend_log = log_dir / "backend.txt"
    content = backend_log.read_text(encoding="utf-8")
    assert "escape.py" not in content
    assert "service.py" in content


def test_consolidate_files_handles_uppercase_extensions(
    sample_project_path: Path, tmp_path: Path
) -> None:
    uppercase_file = sample_project_path / "backend" / "UPPER.PY"
    uppercase_file.write_text("print('upper')\n", encoding="utf-8")

    output_path = tmp_path / "consolidated.txt"
    consolidate_files(sample_project_path, output_path, {".py"}, [])

    content = output_path.read_text(encoding="utf-8")
    assert "service.py" in content
    assert "UPPER.PY" in content


def test_create_filtered_tree_without_contents(sample_project_path: Path, tmp_path: Path) -> None:
    output_path = tmp_path / "tree.txt"
    create_filtered_tree(sample_project_path, output_path, [], include_content=False)

    content = output_path.read_text(encoding="utf-8")
    assert "backend" in content
    assert "frontend" in content
    assert "Backend service" not in content


def test_load_gitignore_patterns_includes_skip_dirs(sample_project_path: Path) -> None:
    gitignore = sample_project_path / ".gitignore"
    gitignore.write_text("node_modules\n", encoding="utf-8")

    patterns = load_gitignore_patterns(sample_project_path)
    assert "node_modules" in patterns


def test_expand_skip_dirs_generates_variants_fuzz() -> None:
    rng = random.Random(2)
    alphabet = string.ascii_lowercase
    for _ in range(50):
        skip_dirs: list[str] = []
        for _ in range(rng.randint(0, 5)):
            length = rng.randint(1, 4)
            token = "".join(rng.choice(alphabet) for _ in range(length))
            if rng.random() < 0.5:
                token = f"/{token}/"
            skip_dirs.append(token)
        patterns = expand_skip_dirs(skip_dirs)

        for skip_dir in skip_dirs:
            cleaned = skip_dir.strip("/")
            if not cleaned:
                continue
            assert cleaned in patterns
            assert f"{cleaned}/" in patterns
            assert f"*/{cleaned}" in patterns
