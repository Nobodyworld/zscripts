import sys
from pathlib import Path
import os

# Resolve the current script directory
script_dir = Path(__file__).resolve().parent

# Determine the parent directory where 'zscripts' is located
parent_dir = script_dir.parent.parent / 'zscripts'
# Insert the parent directory into the system path to allow importing utils and config modules
sys.path.insert(0, str(parent_dir))

# Import necessary functions and configurations
from utils import load_gitignore_patterns, consolidate_files
from config import SCRIPT_DIR, SINGLE_LOG_DIR, CAPTURE_ALL_LOG

# Ensure the single log directory exists
SINGLE_LOG_DIR.mkdir(parents=True, exist_ok=True)

def main():
    """
    Main function to create a consolidated log of all Python, HTML, CSS, and JavaScript files in the project.

    Steps:
    1. Determine the project root directory.
    2. Define and create the logs directory for single files.
    3. Load ignore patterns from .gitignore.
    4. Create a consolidated log for all specified file types, ignoring specified patterns.
    5. Print the location of the generated log.
    """
    try:
        # Determine the project root, which is the parent directory of the script directory
        project_root = SCRIPT_DIR.parent

        # Load ignore patterns from .gitignore or other sources
        ignore_patterns = load_gitignore_patterns(project_root)

        # Create a consolidated log for all specified file types, ignoring specified patterns
        consolidate_files(project_root, CAPTURE_ALL_LOG, {'.py', '.html', '.css', '.js'}, ignore_patterns)

        # Print the location of the generated log
        print(f"Consolidated log for all specified files in {project_root} has been created in {CAPTURE_ALL_LOG}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
