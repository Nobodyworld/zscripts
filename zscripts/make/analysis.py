# zscripts/make/analysis.py
import sys
from pathlib import Path
import os
import re

# Resolve the current script directory
script_dir = Path(__file__).resolve().parent

# Determine the parent directory where 'zscripts' is located
parent_dir = script_dir.parent.parent / 'zscripts'
# Insert the parent directory into the system path to allow importing utils and config modules
sys.path.insert(0, str(parent_dir))

# Import necessary functions and configurations
from utils import load_gitignore_patterns, file_matches_any_pattern
from config import SCRIPT_DIR, ANALYSIS_DIR, BUILD_DIR, SKIP_DIRS

# Ensure the analysis directory exists
ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)

def extract_definitions(file_path):
    """
    Extracts and writes class and function names from a given Python file to a log file.

    Args:
        file_path (Path): The path of the Python file to analyze.
    
    Notes:
        - This function reads the content of the file, uses regular expressions to find class and function definitions,
          and writes the extracted names to a corresponding text file in the analysis directory.
        - The resulting log file is named based on the original Python file name with a .txt extension.
    
    Best Practices:
        - Ensure the regular expressions used for extraction are robust enough to handle various code styles.
        - Regularly clean up or archive old analysis logs to keep the analysis directory manageable.
    """
    base_name = file_path.name
    analysis_file_name = base_name.replace('.py', '.txt')
    analysis_file_path = ANALYSIS_DIR / analysis_file_name

    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    classes = re.findall(r'^class (\w+)', content, re.MULTILINE)
    functions = re.findall(r'^def (\w+)', content, re.MULTILINE)

    with open(analysis_file_path, 'w', encoding='utf-8') as analysis_file:
        if classes:
            analysis_file.write("Classes:\n")
            analysis_file.writelines(f"{cls}\n" for cls in classes)
        if functions:
            analysis_file.write("\nFunctions:\n")
            analysis_file.writelines(f"{func}\n" for func in functions)

    print(f"Analysis for {base_name} written to {analysis_file_name}")

def scan_directory(directory, ignore_patterns):
    """
    Scans a directory for Python files and extracts class and function definitions from each file.

    Args:
        directory (Path): The directory to scan for Python files.
        ignore_patterns (list): A list of patterns to ignore.
    
    Notes:
        - This function iterates over all files in the specified directory, calling extract_definitions for each Python file.
    
    Best Practices:
        - Ensure the directory structure is well-organized to facilitate easy scanning and analysis.
        - Use this function to automate the extraction of code structures for documentation or analysis purposes.
    """
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if not file_matches_any_pattern(Path(root) / d, ignore_patterns)]
        for filename in files:
            if filename.endswith('.py'):
                file_path = Path(root) / filename
                extract_definitions(file_path)

if __name__ == "__main__":
    project_root = SCRIPT_DIR.parent
    ignore_patterns = load_gitignore_patterns(project_root) + SKIP_DIRS
    scan_directory(BUILD_DIR, ignore_patterns)
    print("Extraction complete. Check the analysis logs directory for details.")
