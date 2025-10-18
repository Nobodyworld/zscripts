"""Shared pytest fixtures for the zscripts test suite."""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

import pytest


def _load_config_helpers():
    """Import configuration helpers with a runtime sys.path adjustment."""

    root = Path(__file__).resolve().parent.parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    module = importlib.import_module("zscripts.config")
    return module.Config, module.get_config, module.load_config

# TODO - Replace sys.path mutation with a dedicated test helper package.


@pytest.fixture(scope="session")
def repository_root() -> Path:
    return Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session")
def sample_project_path(repository_root: Path) -> Path:
    return repository_root / "sample_project"


@pytest.fixture()
def temp_config_path(tmp_path: Path) -> Path:
    _, get_config, _ = _load_config_helpers()
    base = get_config().to_dict()
    log_root = tmp_path / "logs"
    base.setdefault("directories", {})["log_root"] = str(log_root)
    config_path = tmp_path / "zscripts.config.json"
    config_path.write_text(json.dumps(base), encoding="utf-8")
    return config_path


@pytest.fixture()
def temp_config(temp_config_path: Path):
    _, _, load_config = _load_config_helpers()
    return load_config(temp_config_path)
