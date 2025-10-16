from __future__ import annotations

from pathlib import Path

from zscripts.config import Config, get_config, get_file_group_resolver, load_config


def test_config_loading() -> None:
    config = get_config()
    assert isinstance(config, Config)
    assert isinstance(config.skip, list)
    assert isinstance(config.file_types, dict)
    assert isinstance(config.user_ignore_patterns, set)
    assert isinstance(config.directories, dict)
    assert isinstance(config.collection_logs, dict)
    assert isinstance(config.single_targets, dict)


def test_load_config_with_path(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    config_path.write_text('{"skip": ["test"], "file_types": {}, "user_ignore_patterns": [], "directories": {}, "collection_logs": {}, "single_targets": {}}')
    config = load_config(config_path)
    assert config.skip == ["test"]


def test_file_group_resolver() -> None:
    resolver = get_file_group_resolver()
    assert isinstance(resolver, dict)
    assert "models.py" in resolver
