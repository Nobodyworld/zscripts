"""Assemble README.md from individual section templates."""

from __future__ import annotations

from pathlib import Path


def compile_readme() -> None:
    readme_dir = Path("zscripts/zreadme")
    build_order = [
        "0-Overview.txt",
        "1-Configuration.txt",
        "2-CLI.txt",
        "3-Sample-Project.txt",
        "4-Migration.txt",
    ]

    compiled_content: list[str] = []
    for filename in build_order:
        path = readme_dir / filename.strip()
        try:
            compiled_content.append(path.read_text(encoding="utf-8").rstrip())
        except FileNotFoundError:
            print(f"Warning: {path} not found and will be skipped.")
        except UnicodeDecodeError as error:
            print(f"Error reading {path}: {error}")

    output_readme_path = Path("README.md")
    output_readme_path.write_text("\n\n".join(compiled_content) + "\n", encoding="utf-8")
    print(f"Readme compiled and saved to {output_readme_path.resolve()}")


if __name__ == "__main__":
    compile_readme()
