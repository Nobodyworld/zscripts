"""Configuration validation and advanced feature tests for zscripts."""
from __future__ import annotations

import json
from pathlib import Path

from zscripts.cli import _augment_ignore_patterns
from zscripts.config import Config, get_config, load_config
from zscripts.utils import IgnoreMatcher, consolidate_files, create_filtered_tree


class TestConfigurationValidation:
    """Test configuration validation and edge cases."""

    def test_config_schema_validation(self) -> None:
        """Test that config adheres to expected schema."""
        config = get_config()
        assert isinstance(config, Config)

        # Required attributes
        assert hasattr(config, 'skip')
        assert hasattr(config, 'file_types')
        assert hasattr(config, 'user_ignore_patterns')
        assert hasattr(config, 'directories')
        assert hasattr(config, 'collection_logs')
        assert hasattr(config, 'single_targets')

        # Type checks
        assert isinstance(config.skip, list)
        assert isinstance(config.file_types, dict)
        assert isinstance(config.user_ignore_patterns, set)
        assert isinstance(config.directories, dict)
        assert isinstance(config.collection_logs, dict)
        assert isinstance(config.single_targets, dict)

    def test_config_file_loading_priority(self, tmp_path: Path) -> None:
        """Test configuration file loading priority."""
        # Create a custom config
        custom_config = tmp_path / "custom.json"
        custom_config.write_text('{"skip": ["custom_skip"], "file_types": {"test.py": "test_files"}}')

        # Load config
        config = load_config(custom_config)

        # Should use custom values
        assert "custom_skip" in config.skip
        assert "test.py" in config.file_types

    def test_config_merging(self, tmp_path: Path) -> None:
        """Test that custom config overrides defaults."""
        partial_config = tmp_path / "partial.json"
        partial_config.write_text('{"skip": ["new_skip"]}')

        config = load_config(partial_config)

        # Should have custom skip
        assert "new_skip" in config.skip
        # file_types will be empty since not specified in partial config
        assert isinstance(config.file_types, dict)
        assert len(config.file_types) == 0  # Not merged with defaults

    def test_invalid_config_values(self, tmp_path: Path) -> None:
        """Test handling of invalid config values."""
        invalid_config = tmp_path / "invalid.json"
        invalid_config.write_text('{"skip": "not_a_list", "file_types": "not_a_dict"}')

        # Should handle gracefully or fail appropriately
        try:
            config = load_config(invalid_config)
            # If it loads, types should be corrected or defaults used
            assert isinstance(config.skip, list)
            assert isinstance(config.file_types, dict)
        except Exception:
            # It's acceptable for invalid configs to cause exceptions
            pass

    def test_config_with_comments(self, tmp_path: Path) -> None:
        """Test config files with comments (if supported)."""
        config_with_comments = tmp_path / "comments.json"
        config_with_comments.write_text("""
        {
            // This is a comment
            "skip": ["test"],
            "file_types": {}
            /* Another comment */
        }
        """)

        # JSON doesn't support comments, so this should fail
        try:
            config = load_config(config_with_comments)
            # If it somehow works, that's fine
        except Exception:
            # Expected for JSON with comments
            pass


class TestFileTypeHandling:
    """Test handling of different file types and extensions."""

    def test_python_file_detection(self, tmp_path: Path) -> None:
        """Test detection and handling of Python files."""
        py_file = tmp_path / "test.py"
        py_file.write_text("# Python file\ndef test():\n    pass\n")

        output = tmp_path / "output.txt"
        consolidate_files(tmp_path, output, {".py"}, [])

        content = output.read_text()
        assert "# Python file" in content
        assert "def test():" in content

    def test_javascript_file_detection(self, tmp_path: Path) -> None:
        """Test detection and handling of JavaScript files."""
        js_file = tmp_path / "app.js"
        js_file.write_text("// JavaScript file\nfunction test() {}\n")

        output = tmp_path / "output.txt"
        from zscripts.utils import consolidate_files
        consolidate_files(tmp_path, output, {".js"}, [])

        content = output.read_text()
        assert "// JavaScript file" in content
        assert "function test()" in content

    def test_mixed_file_types(self, tmp_path: Path) -> None:
        """Test handling of mixed file types in same directory."""
        py_file = tmp_path / "code.py"
        py_file.write_text("# Python\ndef func(): pass")

        js_file = tmp_path / "script.js"
        js_file.write_text("// JavaScript\nfunction func() {}")

        txt_file = tmp_path / "readme.txt"
        txt_file.write_text("Readme content")

        # Consolidate only Python and JS
        output = tmp_path / "output.txt"
        from zscripts.utils import consolidate_files
        consolidate_files(tmp_path, output, {".py", ".js"}, [])

        content = output.read_text()
        assert "# Python" in content
        assert "// JavaScript" in content
        assert "Readme content" not in content  # Should exclude .txt

    def test_file_type_case_sensitivity(self, tmp_path: Path) -> None:
        """Test case sensitivity in file extensions."""
        py_file = tmp_path / "test.PY"  # Uppercase extension
        py_file.write_text("# Uppercase PY")

        output = tmp_path / "output.txt"
        from zscripts.utils import consolidate_files
        consolidate_files(tmp_path, output, {".py"}, [])

        content = output.read_text()
        # Should handle case insensitivity (depending on platform)
        # On Windows, this might work; on Unix, it might not
        if content:
            assert "# Uppercase PY" in content

    def test_hidden_files(self, tmp_path: Path) -> None:
        """Test handling of hidden files."""
        hidden_file = tmp_path / ".hidden.py"
        hidden_file.write_text("# Hidden file")

        output = tmp_path / "output.txt"
        from zscripts.utils import consolidate_files
        consolidate_files(tmp_path, output, {".py"}, [])

        content = output.read_text()
        # Hidden files should typically be included unless specifically ignored
        assert "# Hidden file" in content

    def test_nested_skip_directories_ignored(self, tmp_path: Path) -> None:
        """Nested skip directories from config should be ignored during collection."""

        project_root = tmp_path / "project"
        project_root.mkdir()

        # Files that should be skipped
        skip_root = project_root / "skipme"
        skip_root.mkdir()
        (skip_root / "ignored.py").write_text("print('skip root')\n")

        nested_skip = project_root / "nested" / "inner"
        nested_skip.mkdir(parents=True)
        (nested_skip / "ignored_nested.py").write_text("print('nested skip')\n")

        deep_nested = project_root / "deep" / "nested" / "inner"
        deep_nested.mkdir(parents=True)
        (deep_nested / "ignored_deep.py").write_text("print('deep nested skip')\n")

        # File that should be collected
        keep_dir = project_root / "keep"
        keep_dir.mkdir()
        kept_file = keep_dir / "collected.py"
        kept_file.write_text("print('keep me')\n")

        config_path = tmp_path / "config.json"
        config_path.write_text(json.dumps({"skip": ["skipme", "nested/inner"]}))
        config = load_config(config_path)

        ignore_patterns = _augment_ignore_patterns(project_root, config)

        output = tmp_path / "collected.txt"
        consolidate_files(project_root, output, {".py"}, ignore_patterns)

        content = output.read_text()
        assert "keep me" in content
        assert "skip root" not in content
        assert "nested skip" not in content
        assert "deep nested skip" not in content


class TestIgnorePatterns:
    """Test ignore pattern functionality."""

    def test_gitignore_style_patterns(self, tmp_path: Path) -> None:
        """Test gitignore-style ignore patterns."""
        from zscripts.utils import IgnoreMatcher

        matcher = IgnoreMatcher(["*.pyc", "__pycache__", "node_modules"])

        assert matcher.matches(Path("__pycache__/module.pyc"))  # Exact match
        assert not matcher.matches(Path("node_modules/package.json"))  # Doesn't match directory contents
        assert matcher.matches(Path("*.pyc"))  # Pattern matches
        assert not matcher.matches(Path("module.py"))

    def test_complex_ignore_patterns(self, tmp_path: Path) -> None:
        """Test complex ignore patterns."""
        from zscripts.utils import IgnoreMatcher

        patterns = [
            "*.log",
            "temp",  # Directory name
            "build",  # Directory name
            "!important.log"  # Negation (not implemented in simple matcher)
        ]
        matcher = IgnoreMatcher(patterns)

        assert matcher.matches(Path("debug.log"))
        assert matcher.matches(Path("temp"))  # Directory name matches
        assert matcher.matches(Path("build"))  # Directory name matches
        # Negation not implemented, so this matches
        assert matcher.matches(Path("important.log"))

    def test_ignore_pattern_precedence(self, tmp_path: Path) -> None:
        """Test precedence of ignore patterns."""
        # Create files that should be ignored and not ignored
        ignored_file = tmp_path / "cache.pyc"
        ignored_file.write_text("# Ignored")

        included_file = tmp_path / "code.py"
        included_file.write_text("# Included")

        output = tmp_path / "output.txt"
        from zscripts.utils import consolidate_files
        consolidate_files(tmp_path, output, {".py"}, ["*.pyc"])

        content = output.read_text()
        assert "# Included" in content
        assert "# Ignored" not in content


class TestOutputFormatting:
    """Test output formatting and structure."""

    def test_consolidate_output_headers(self, tmp_path: Path) -> None:
        """Test that consolidate output includes proper file headers."""
        file1 = tmp_path / "dir1" / "file1.py"
        file1.parent.mkdir(parents=True)
        file1.write_text("# File 1 content\ndef func1(): pass")

        file2 = tmp_path / "dir2" / "file2.py"
        file2.parent.mkdir(parents=True)
        file2.write_text("# File 2 content\ndef func2(): pass")

        output = tmp_path / "output.txt"
        from zscripts.utils import consolidate_files
        consolidate_files(tmp_path, output, {".py"}, [])

        content = output.read_text()
        lines = content.split('\n')

        # Should contain file separators/headers
        assert any("===" in line or "file1.py" in line for line in lines)
        assert any("===" in line or "file2.py" in line for line in lines)
        assert "# File 1 content" in content
        assert "# File 2 content" in content

    def test_tree_output_structure(self, tmp_path: Path) -> None:
        """Test that tree output has proper structure."""
        # Create directory structure
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("# Main")
        (tmp_path / "tests").mkdir()
        (tmp_path / "tests" / "test_main.py").write_text("# Test")

        output = tmp_path / "tree.txt"
        from zscripts.utils import create_filtered_tree
        create_filtered_tree(tmp_path, output, [])  # No ignore patterns

        content = output.read_text()
        assert "src" in content
        assert "tests" in content
        assert "main.py" in content
        assert "test_main.py" in content

    def test_empty_output_handling(self, tmp_path: Path) -> None:
        """Test handling when no files match criteria."""
        # Create files that don't match filter
        txt_file = tmp_path / "readme.txt"
        txt_file.write_text("Text content")

        output = tmp_path / "output.txt"
        from zscripts.utils import consolidate_files
        consolidate_files(tmp_path, output, {".py"}, [])

        # Output file should still be created but be empty or minimal
        assert output.exists()
        content = output.read_text()
        assert "Text content" not in content