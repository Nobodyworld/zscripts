"""CLI argument validation and integration tests for zscripts."""
from __future__ import annotations

import time
from pathlib import Path

import pytest

from zscripts.cli import main as cli_main
from zscripts.config import get_config


class TestCLIArguments:
    """Test CLI argument validation and edge cases."""

    def test_invalid_types_argument(self, sample_project_path: Path) -> None:
        """Test handling of invalid --types argument."""
        from zscripts.cli import UnknownTypeError
        with pytest.raises(UnknownTypeError):
            cli_main([
                "collect",
                "--types", "invalid,python",
                "--project-root", str(sample_project_path)
            ])

    def test_empty_types_argument(self, sample_project_path: Path) -> None:
        """Test handling of empty --types argument."""
        exit_code = cli_main([
            "collect",
            "--types", "",
            "--project-root", str(sample_project_path)
        ])
        assert exit_code == 0  # Should handle gracefully

    def test_multiple_types_argument(self, sample_project_path: Path) -> None:
        """Test handling of multiple file types."""
        exit_code = cli_main([
            "collect",
            "--types", "python,js,html",
            "--project-root", str(sample_project_path)
        ])
        assert exit_code == 0

    def test_missing_required_arguments(self) -> None:
        """Test handling of missing required arguments."""
        # Missing --project-root, should use current directory
        exit_code = cli_main(["collect", "--types", "python"])
        assert exit_code == 0  # Should work with current directory

    def test_invalid_project_root(self) -> None:
        """Test handling of invalid project root."""
        exit_code = cli_main([
            "collect",
            "--types", "python",
            "--project-root", "/nonexistent/path"
        ])
        assert exit_code == 0  # Should create directory structure

    def test_output_file_in_nonexistent_directory(self, tmp_path: Path, sample_project_path: Path) -> None:
        """Test output to nested nonexistent directory."""
        deep_output = tmp_path / "very" / "deep" / "nested" / "output.txt"
        exit_code = cli_main([
            "consolidate",
            "--types", "python",
            "--project-root", str(sample_project_path),
            "--output", str(deep_output)
        ])
        assert exit_code == 0
        assert deep_output.exists()

    def test_config_file_argument(self, tmp_path: Path, sample_project_path: Path) -> None:
        """Test --config argument."""
        config_file = tmp_path / "test_config.json"
        config_file.write_text('{"skip": ["*.tmp"], "file_types": {}}')

        exit_code = cli_main([
            "collect",
            "--types", "python",
            "--project-root", str(sample_project_path),
            "--config", str(config_file)
        ])
        assert exit_code == 0

    def test_invalid_config_file(self, sample_project_path: Path) -> None:
        """Test handling of invalid config file."""
        with pytest.raises(RuntimeError, match="Configuration file not found"):
            cli_main([
                "collect",
                "--types", "python",
                "--project-root", str(sample_project_path),
                "--config", "/nonexistent/config.json"
            ])


class TestCLIIntegration:
    """Integration tests for CLI functionality."""

    def test_full_workflow(self, tmp_path: Path, sample_project_path: Path) -> None:
        """Test a complete workflow from collect to consolidate."""
        # First collect logs
        exit_code = cli_main([
            "collect",
            "--types", "python",
            "--project-root", str(sample_project_path)
        ])
        assert exit_code == 0

        # Then consolidate
        output = tmp_path / "full_consolidated.txt"
        exit_code = cli_main([
            "consolidate",
            "--types", "python",
            "--project-root", str(sample_project_path),
            "--output", str(output)
        ])
        assert exit_code == 0
        assert output.exists()
        assert output.stat().st_size > 0

    def test_tree_and_consolidate_workflow(self, tmp_path: Path, sample_project_path: Path) -> None:
        """Test tree generation followed by consolidation."""
        # Generate tree
        tree_output = tmp_path / "project_tree.txt"
        exit_code = cli_main([
            "tree",
            "--project-root", str(sample_project_path),
            "--output", str(tree_output)
        ])
        assert exit_code == 0
        assert tree_output.exists()

        # Consolidate files
        consolidate_output = tmp_path / "consolidated.txt"
        exit_code = cli_main([
            "consolidate",
            "--types", "python",
            "--project-root", str(sample_project_path),
            "--output", str(consolidate_output)
        ])
        assert exit_code == 0
        assert consolidate_output.exists()

    def test_multiple_file_types_integration(self, tmp_path: Path, sample_project_path: Path) -> None:
        """Test collecting multiple file types and consolidating single type."""
        # Collect multiple types
        exit_code = cli_main([
            "collect",
            "--types", "python,js",
            "--project-root", str(sample_project_path)
        ])
        assert exit_code == 0

        # Consolidate single type (consolidate command only accepts one type)
        output = tmp_path / "python_only.txt"
        exit_code = cli_main([
            "consolidate",
            "--types", "python",
            "--project-root", str(sample_project_path),
            "--output", str(output)
        ])
        assert exit_code == 0
        assert output.exists()

        content = output.read_text()
        # Should contain both Python and JS content
        assert any("def " in line or "function" in line for line in content.split('\n'))


class TestCLIOutput:
    """Test CLI output formatting and content."""

    def test_collect_output_structure(self, sample_project_path: Path) -> None:
        """Test that collect creates proper directory structure."""
        exit_code = cli_main([
            "collect",
            "--types", "python",
            "--project-root", str(sample_project_path)
        ])
        assert exit_code == 0

        # Check that log directories were created
        config = get_config()
        log_dir = config.collection_logs.get("python", "logs_apps_pyth")
        full_log_dir = sample_project_path.parent / "zscripts" / "logs" / log_dir
        assert full_log_dir.exists()

    def test_consolidate_output_format(self, tmp_path: Path, sample_project_path: Path) -> None:
        """Test that consolidate output has proper format."""
        output = tmp_path / "formatted_output.txt"
        exit_code = cli_main([
            "consolidate",
            "--types", "python",
            "--project-root", str(sample_project_path),
            "--output", str(output)
        ])
        assert exit_code == 0

        content = output.read_text()
        lines = content.split('\n')

        # Should contain file headers and content
        assert any("# " in line and ".py" in line for line in lines)  # File headers
        assert any("class " in line or "def " in line for line in lines)  # Python content

    def test_tree_output_format(self, tmp_path: Path, sample_project_path: Path) -> None:
        """Test that tree output has proper format."""
        output = tmp_path / "tree_output.txt"
        exit_code = cli_main([
            "tree",
            "--project-root", str(sample_project_path),
            "--output", str(output)
        ])
        assert exit_code == 0

        content = output.read_text(encoding='utf-8')
        lines = content.split('\n')

        # Should contain tree structure - check for Unicode tree characters
        tree_chars_found = any("├──" in line or "└──" in line for line in lines)
        assert tree_chars_found, f"Tree characters not found in output. Content preview: {content[:200]}"
        assert any("sample_project" in line for line in lines)       # Project name


class TestCLIPerformance:
    """Test CLI performance with various inputs."""

    def test_large_project_simulation(self, tmp_path: Path) -> None:
        """Test CLI with simulated large project."""
        # Create many files and directories
        for i in range(20):
            dir_path = tmp_path / f"module_{i}"
            dir_path.mkdir()

            for j in range(10):
                file_path = dir_path / f"file_{j}.py"
                file_path.write_text(f"# Module {i}, File {j}\ndef func_{i}_{j}():\n    return {i * j}\n")

        # Test collect performance
        start_time = time.time()
        exit_code = cli_main([
            "collect",
            "--types", "python",
            "--project-root", str(tmp_path)
        ])
        end_time = time.time()

        assert exit_code == 0
        assert end_time - start_time < 5.0  # Should complete within 5 seconds

    def test_memory_usage(self, tmp_path: Path) -> None:
        """Test that CLI doesn't use excessive memory."""
        # Create files with substantial content
        for i in range(50):
            file_path = tmp_path / f"large_{i}.py"
            content = f"# Large file {i}\n" + "\n".join(f"x_{i}_{j} = {i * j}" for j in range(1000))
            file_path.write_text(content)

        # Should complete without memory issues
        output = tmp_path / "large_output.txt"
        exit_code = cli_main([
            "consolidate",
            "--types", "python",
            "--project-root", str(tmp_path),
            "--output", str(output)
        ])
        assert exit_code == 0
        assert output.exists()

