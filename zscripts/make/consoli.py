# zscripts/make/consoli.py
import sys
from pathlib import Path
import os

# Resolve the current script directory
script_dir = Path(__file__).resolve().parent

# Determine the parent directory where 'zscripts' is located
parent_dir = script_dir.parent.parent / 'zscripts'
# Insert the parent directory into the system path to allow importing utils and config modules
sys.path.insert(0, str(parent_dir))

# Import necessary configurations
from config import BUILD_DIR, ANALYSIS_DIR, CONSOLIDATION_DIR

# Ensure the consolidation directory exists
CONSOLIDATION_DIR.mkdir(parents=True, exist_ok=True)

def consolidate_files(source_dir, file_extension, output_file_name):
    """
    Consolidates all files in the specified directory with the given file extension into a single file.

    Args:
        source_dir (Path): The directory containing files to consolidate.
        file_extension (str): The file extension to look for.
        output_file_name (str): The name of the output consolidated file.

    Note:
        This function reads all files with the specified extension from the source directory,
        concatenates their content, and writes it to a single output file.
    
    Best Practices:
        - Ensure that the source directory contains the files to be consolidated.
        - Use meaningful file names for the output to reflect its content.
    """
    output_path = CONSOLIDATION_DIR / output_file_name
    with open(output_path, 'w', encoding='utf-8') as output_file:
        # Walk through the directory, and concatenate files into the output file
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                if file.endswith(file_extension):
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        output_file.write(f"# Start of {file}\n")
                        output_file.write(content)
                        output_file.write(f"\n# End of {file}\n\n")
                    print(f"Included {file} in {output_file_name}")

if __name__ == "__main__":
    # Consolidate Python build files into one .py file
    consolidate_files(BUILD_DIR, '.py', 'consolidated_build.py')

    # Consolidate analysis log files into one .txt file
    consolidate_files(ANALYSIS_DIR, '.txt', 'consolidated_analysis.txt')

    print("Consolidation complete. Check the consoli_files directory for consolidated files.")
