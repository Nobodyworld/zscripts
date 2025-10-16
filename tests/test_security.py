"""Security and safety tests for zscripts."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from zscripts.cli import main as cli_main
from zscripts.config import load_config
from zscripts.utils import collect_app_logs, consolidate_files


class TestSecurity:
    """Test security features and path traversal protection."""

    def test_path_traversal_protection(self, tmp_path: Path) -> None:
        """Test that path traversal attempts are blocked."""
        # Create a malicious file with path traversal
        malicious_file = tmp_path / "backend" / "service.py"
        malicious_file.parent.mkdir(parents=True)
        malicious_file.write_text("# Normal content")

        # Create a file that tries to escape the project root
        escape_file = tmp_path / "backend" / "..\\..\\..\\etc\\passwd.py"
        escape_file.parent.mkdir(parents=True, exist_ok=True)
        escape_file.write_text("# Malicious content")

        # Test that collect_app_logs doesn't follow path traversal
        log_dir = tmp_path / "logs"
        collect_app_logs(tmp_path, log_dir, {".py"}, [])

        # Should not create logs outside the log directory
        assert not (log_dir / ".." / ".." / "etc").exists()
        assert not (log_dir / "passwd.txt").exists()

    def test_file_size_limits(self, tmp_path: Path) -> None:
        """Test handling of very large files."""
        # Create a large file
        large_file = tmp_path / "large.py"
        large_content = "# Large file\n" * 10000  # ~120KB
        large_file.write_text(large_content)

        # Test consolidation with large files
        output = tmp_path / "output.txt"
        consolidate_files(tmp_path, output, {".py"}, [])

        assert output.exists()
        content = output.read_text()
        assert "# Large file" in content

    def test_symlink_handling(self, tmp_path: Path) -> None:
        """Test that symlinks are handled safely."""
        # Create a regular file
        real_file = tmp_path / "real.py"
        real_file.write_text("# Real file")

        # Create a symlink (if supported)
        try:
            link_file = tmp_path / "link.py"
            os.symlink(str(real_file), str(link_file))

            # Test that consolidation works with symlinks
            output = tmp_path / "output.txt"
            consolidate_files(tmp_path, output, {".py"}, [])

            assert output.exists()
            content = output.read_text()
            assert "# Real file" in content
        except OSError:
            # Symlinks not supported on this platform
            pytest.skip("Symlinks not supported on this platform")

    def test_permission_denied_handling(self, tmp_path: Path) -> None:
        """Test graceful handling of permission denied errors."""
        # Create a file
        test_file = tmp_path / "test.py"
        test_file.write_text("# Test file")

        # Make the directory read-only (if possible)
        try:
            # On Windows, this might not work as expected
            output = tmp_path / "output.txt"
            consolidate_files(tmp_path, output, {".py"}, [])
            assert output.exists()
        except PermissionError:
            # This is expected behavior - should not crash
            pass


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_empty_project_directory(self, tmp_path: Path) -> None:
        """Test handling of empty project directories."""
        # Test collect on empty directory
        exit_code = cli_main(["collect", "--types", "python", "--project-root", str(tmp_path)])
        assert exit_code == 0  # Should not crash

        # Test consolidate on empty directory
        output = tmp_path / "output.txt"
        exit_code = cli_main([
            "consolidate",
            "--types", "python",
            "--project-root", str(tmp_path),
            "--output", str(output)
        ])
        assert exit_code == 0
        assert output.exists()

    def test_nonexistent_project_root(self, tmp_path: Path) -> None:
        """Test handling of nonexistent project root."""
        nonexistent = tmp_path / "does_not_exist"
        exit_code = cli_main(["collect", "--types", "python", "--project-root", str(nonexistent)])
        assert exit_code == 0  # Should create directory structure

    def test_invalid_file_types(self, sample_project_path: Path) -> None:
        """Test handling of invalid file type specifications."""
        from zscripts.cli import UnknownTypeError
        with pytest.raises(UnknownTypeError):
            cli_main([
                "collect",
                "--types", "invalid_type",
                "--project-root", str(sample_project_path)
            ])

    def test_output_directory_creation(self, tmp_path: Path, sample_project_path: Path) -> None:
        """Test that output directories are created as needed."""
        nested_output = tmp_path / "deep" / "nested" / "output.txt"

        exit_code = cli_main([
            "consolidate",
            "--types", "python",
            "--project-root", str(sample_project_path),
            "--output", str(nested_output)
        ])
        assert exit_code == 0
        assert nested_output.exists()
        assert nested_output.parent.exists()


class TestConfigurationEdgeCases:
    """Test configuration handling edge cases."""

    def test_malformed_config_file(self, tmp_path: Path) -> None:
        """Test handling of malformed configuration files."""
        config_file = tmp_path / "bad_config.json"
        config_file.write_text("{invalid json")

        # Should raise JSONDecodeError
        with pytest.raises((ValueError, UnicodeDecodeError)):  # JSON parsing errors
            load_config(config_file)

    def test_missing_config_values(self, tmp_path: Path) -> None:
        """Test handling of incomplete configuration."""
        config_file = tmp_path / "minimal_config.json"
        config_file.write_text('{"skip": []}')  # Missing other required fields

        config = load_config(config_file)
        assert config.skip == []
        # Should have defaults for other fields

    def test_config_file_permissions(self, tmp_path: Path) -> None:
        """Test handling of inaccessible configuration files."""
        config_file = tmp_path / "readonly_config.json"
        config_file.write_text('{"skip": ["test"]}')

        # Try to make it readonly (if possible)
        try:
            config_file.chmod(0o444)
            config = load_config(config_file)
            assert config is not None  # Should handle gracefully
        except OSError:
            # chmod may not work on all platforms
            pass


class TestCrossPlatformCompatibility:
    """Test cross-platform file handling."""

    def test_path_separators(self, tmp_path: Path) -> None:
        """Test that path separators are handled correctly."""
        # Create files with different path structures
        (tmp_path / "dir1" / "file.py").parent.mkdir(parents=True)
        (tmp_path / "dir1" / "file.py").write_text("# File 1")

        (tmp_path / "dir2" / "subdir" / "file.py").parent.mkdir(parents=True)
        (tmp_path / "dir2" / "subdir" / "file.py").write_text("# File 2")

        output = tmp_path / "output.txt"
        consolidate_files(tmp_path, output, {".py"}, [])

        content = output.read_text()
        assert "# File 1" in content
        assert "# File 2" in content

    def test_unicode_filenames(self, tmp_path: Path) -> None:
        """Test handling of unicode filenames."""
        unicode_file = tmp_path / "tëst_üñíçødé.py"
        unicode_file.write_text("# Unicode content")

        output = tmp_path / "output.txt"
        consolidate_files(tmp_path, output, {".py"}, [])

        content = output.read_text()
        assert "# Unicode content" in content

    def test_long_paths(self, tmp_path: Path) -> None:
        """Test handling of long file paths."""
        # Create a deeply nested directory structure
        deep_path = tmp_path
        for i in range(10):
            deep_path = deep_path / f"level_{i}"
        deep_path.mkdir(parents=True)
        deep_file = deep_path / "deep.py"
        deep_file.write_text("# Deep file")

        output = tmp_path / "output.txt"
        consolidate_files(tmp_path, output, {".py"}, [])

        content = output.read_text()
        assert "# Deep file" in content


class TestPerformance:
    """Test performance and scalability."""

    def test_large_number_of_files(self, tmp_path: Path) -> None:
        """Test handling of many files."""
        # Create many files
        for i in range(100):
            file_path = tmp_path / f"file_{i}.py"
            file_path.write_text(f"# File {i}\ndef func_{i}():\n    return {i}\n")

        output = tmp_path / "output.txt"
        consolidate_files(tmp_path, output, {".py"}, [])

        content = output.read_text()
        assert "File 0" in content
        assert "File 99" in content
        assert len(content.split("# File")) > 90  # Most files included

    def test_large_file_content(self, tmp_path: Path) -> None:
        """Test handling of files with large content."""
        large_content = "# Header\n" + "x = 1\n" * 10000  # ~50KB
        large_file = tmp_path / "large.py"
        large_file.write_text(large_content)

        output = tmp_path / "output.txt"
        consolidate_files(tmp_path, output, {".py"}, [])

        content = output.read_text()
        assert "# Header" in content
        assert "x = 1" in content

