"""Create a filtered view of the project tree using shared ignore settings.

The ignore configuration now flows through :func:`utils.load_gitignore_patterns`,
which merges ``.gitignore`` entries with the defaults and user overrides from
``config.json`` (``skip_dirs`` and ``ignore_patterns``).
"""

import os
import sys
from pathlib import Path
import datetime

# Resolve the current script directory
script_dir = Path(__file__).resolve().parent

# Determine the parent directory where 'zscripts' is located
parent_dir = script_dir.parent.parent / 'zscripts'
# Insert the parent directory into the system path to allow importing utils and config modules
sys.path.insert(0, str(parent_dir))

# Import necessary functions and configurations
from utils import load_gitignore_patterns, file_matches_any_pattern
from config import SKIP_DIRS, LOG_DIR

# Get a timestamp for this run
timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

def create_tree(start_path, log_file, ignore_patterns, additional_ignore_dirs=None):
    """
    Create a tree structure of directories and files starting from the given path.

    Args:
        start_path (Path): The root directory to start the tree from.
        log_file (file object): The file object to write the tree structure to.
        ignore_patterns (list): A list of patterns to ignore.
        additional_ignore_dirs (set, optional): A set of additional directories to ignore. Defaults to None.
    """
    if additional_ignore_dirs is None:
        additional_ignore_dirs = set(SKIP_DIRS)
    
    for root, dirs, files in os.walk(start_path, topdown=True):
        dirs[:] = [d for d in dirs if not file_matches_any_pattern(Path(root) / d, ignore_patterns) and d not in additional_ignore_dirs]
        relative_path = Path(root).relative_to(start_path)
        if relative_path.parts:
            print(f"{relative_path}/", file=log_file)
        for file in sorted(files):
            if not file_matches_any_pattern(Path(root) / file, ignore_patterns):
                print(f"    {file}", file=log_file)
        for dir in sorted(dirs):
            print(f"{relative_path / dir}/", file=log_file)

if __name__ == "__main__":
    # Determine the root directory of the project
    project_root = script_dir.parent.parent

    # Define the source path and log file path
    src_path = project_root
    log_file_path = project_root / f"zscripts/logs/logs_tree/create_tree_{timestamp}.txt"

    # Ensure the log directory exists
    log_file_path.parent.mkdir(parents=True, exist_ok=True)

    # Load ignore patterns from .gitignore and configuration overrides
    ignore_patterns = load_gitignore_patterns(project_root)

    # Create the directory tree and write to log file
    with open(log_file_path, 'w', encoding='utf-8') as log_file:
        create_tree(src_path, log_file, ignore_patterns)

    print(f"Directory tree written to {log_file_path}")
