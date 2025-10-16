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
from utils import process_file, write_files
from config import SCRIPT_DIR, WORK_DIR, SKIP_DIRS, get_file_group_resolver

resolver = get_file_group_resolver()

def initialize_content_dict():
    """Create an empty content dictionary keyed by configured file groups."""

    return {group: "" for group in resolver.group_names}


def scan_directories(directory, content_dict):
    """Scan directories and process files that match configured file groups."""

    for subdir, dirs, files in os.walk(directory):
        # Skip specified directories
        if any(skip_dir in os.path.relpath(subdir, directory).split(os.sep) for skip_dir in SKIP_DIRS):
            continue

        for file in files:
            file_path = Path(subdir) / file
            matched_groups = resolver.match(file_path, project_root=directory)
            for group in matched_groups:
                process_file(file_path, group, content_dict)

def main():
    """
    Main function to process and log files based on their names.

    Steps:
    1. Determine the project root directory.
    2. Scan directories for specified files.
    3. Write the processed content to log files.
    """
    try:
        # Determine the project root, which is the parent directory of the script directory
        project_root = SCRIPT_DIR.parent

        # Ensure the destination directory exists
        WORK_DIR.mkdir(parents=True, exist_ok=True)

        content_dict = initialize_content_dict()

        # Scan directories for specified files
        scan_directories(project_root, content_dict)

        # Write the processed content to log files
        write_files(content_dict, WORK_DIR)

        print("All specified files have been processed.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
