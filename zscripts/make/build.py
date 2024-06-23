# zscripts/make/build.py
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
from config import BUILD_DIR, WORK_DIR
from utils import load_gitignore_patterns, file_matches_any_pattern

# Ensure the build directory exists
BUILD_DIR.mkdir(parents=True, exist_ok=True)

def process_and_convert_files():
    """
    Process and convert text files in the work directory to Python files in the build directory.

    This function reads all text files in the work directory, converts their content to Python files
    with appropriate naming, and moves them to the build directory. Empty files are skipped.
    """
    if not WORK_DIR.exists() or not any(WORK_DIR.iterdir()):
        print(f"No files to process in {WORK_DIR}. Ensure the directory exists and contains the necessary files.")
        return

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

if __name__ == "__main__":
    process_and_convert_files()
    print(f"All files have been processed and are located in '{BUILD_DIR}'.")
