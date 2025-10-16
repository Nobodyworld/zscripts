"""Smoke tests for legacy wrapper entry points."""

from __future__ import annotations

import importlib
import shutil
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_PROJECT = REPO_ROOT / "sample_project"

COLLECT_WRAPPERS = (
    "zscripts.all.all_both",
    "zscripts.all.all_cssss",
    "zscripts.all.all_htmlll",
    "zscripts.all.all_jssss",
    "zscripts.all.all_pyth",
    "zscripts.all.app_all_types",
)

SINGLE_WRAPPERS = (
    "zscripts.all_single.single",
    "zscripts.all_single.single_css",
    "zscripts.all_single.single_html",
    "zscripts.all_single.single_js",
    "zscripts.all_single.single_pyth",
)


def _prepare_sample_project(tmp_path: Path) -> Path:
    """Copy the bundled sample project into a temporary directory."""

    project_root = tmp_path / "project"
    shutil.copytree(SAMPLE_PROJECT, project_root)
    return project_root


@pytest.mark.parametrize("module_name", COLLECT_WRAPPERS)
def test_collect_wrappers_succeed(
    module_name: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project_root = _prepare_sample_project(tmp_path)
    monkeypatch.chdir(project_root)

    module = importlib.import_module(module_name)

    assert module.main() == 0
    assert (project_root / "zscripts_logs").exists()


@pytest.mark.parametrize("module_name", SINGLE_WRAPPERS)
def test_single_wrappers_succeed(
    module_name: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project_root = _prepare_sample_project(tmp_path)
    monkeypatch.chdir(project_root)

    module = importlib.import_module(module_name)

    assert module.main() == 0
