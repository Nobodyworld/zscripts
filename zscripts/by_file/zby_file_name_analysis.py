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
from utils import load_gitignore_patterns, process_file, write_files, extract_definitions, consolidate_files
from config import SCRIPT_DIR, WORK_DIR, BUILD_DIR, ANALYSIS_DIR, CONSOLIDATION_DIR, SKIP_DIRS, FILE_TYPES

# Ensure necessary directories exist
os.makedirs(WORK_DIR, exist_ok=True)
os.makedirs(BUILD_DIR, exist_ok=True)
os.makedirs(ANALYSIS_DIR, exist_ok=True)
os.makedirs(CONSOLIDATION_DIR, exist_ok=True)

# Dictionary to store content by file type
content_dict = {key: "" for key in FILE_TYPES.values()}

def scan_directories(directory):
    """
    Scans directories and processes files based on specified file types.

    Args:
        directory (Path): The directory to scan for files.
    """
    ignore_patterns = load_gitignore_patterns(directory)

    for subdir, dirs, files in os.walk(directory):
        # Skip specified directories
        if any(skip_dir in os.path.relpath(subdir, directory).split(os.sep) for skip_dir in SKIP_DIRS):
            continue

        for file in files:
            if file in FILE_TYPES:
                file_path = Path(subdir) / file
                process_file(file_path, FILE_TYPES[file], content_dict)

def process_and_convert_files():
    """
    Process and convert text files in the working directory to Python files in the build directory.
    """
    for file_name in os.listdir(WORK_DIR):
        if file_name.endswith('.txt'):
            new_file_name = file_name.replace('_files.txt', '.py')
            old_file_path = WORK_DIR / file_name
            new_file_path = BUILD_DIR / new_file_name

            with open(old_file_path, 'r', encoding='utf-8') as file:
                content = file.read()

            if content.strip():  # Check if the content is not just whitespace
                with open(new_file_path, 'w', encoding='utf-8') as file:
                    file.write(content)
                print(f"Converted and moved {file_name} to {new_file_name}")
            else:
                print(f"Skipped empty file: {file_name}")

def scan_directory_for_analysis(directory):
    """
    Scans a directory for Python files and extracts class and function definitions.
    """
    for filename in os.listdir(directory):
        if filename.endswith('.py'):
            file_path = directory / filename
            extract_definitions(file_path, ANALYSIS_DIR)

def main():
    """
    Main function to process and log files based on their names, convert files, and perform analysis and consolidation.

    Steps:
    1. Determine the project root directory.
    2. Scan directories for specified files.
    3. Write the processed content to log files.
    4. Process and convert files from work directory to build directory.
    5. Extract class and function definitions from build directory.
    6. Consolidate files into single logs.
    """
    try:
        # Determine the project root, which is the parent directory of the script directory
        project_root = SCRIPT_DIR.parent

        # Load ignore patterns from .gitignore or other sources
        ignore_patterns = load_gitignore_patterns(project_root)

        # Scan directories for specified files
        scan_directories(project_root)

        # Write the processed content to log files
        write_files(content_dict, WORK_DIR)

        # Process and convert files from work directory to build directory
        process_and_convert_files()

        # Extract class and function definitions from build directory
        scan_directory_for_analysis(BUILD_DIR)

        # Consolidate files into single logs
        consolidate_files(BUILD_DIR, CONSOLIDATION_DIR / 'consolidated_build.py', {'.py'}, ignore_patterns)
        consolidate_files(ANALYSIS_DIR, CONSOLIDATION_DIR / 'consolidated_analysis.txt', {'.txt'}, ignore_patterns)

        print("All specified files have been processed and analyzed.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
