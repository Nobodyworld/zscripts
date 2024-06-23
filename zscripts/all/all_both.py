import sys
from pathlib import Path

# Resolve the current script directory
script_dir = Path(__file__).resolve().parent

# Determine the parent directory where 'zscripts' is located
parent_dir = script_dir.parent.parent / 'zscripts'
# Insert the parent directory into the system path to allow importing utils and config modules
sys.path.insert(0, str(parent_dir))

# Import necessary functions and configurations
from utils import load_gitignore_patterns, create_app_logs
from config import SCRIPT_DIR, BOTH_LOG_DIR

def main():
    """
    Main function to create logs for all Python and HTML files in the project.

    Steps:
    1. Determine the project root directory.
    2. Define and create the logs directory.
    3. Load ignore patterns from .gitignore.
    4. Create logs for all Python and HTML files, ignoring specified patterns.
    5. Print the location of the generated logs.
    """
    try:
        # Determine the project root, which is the parent directory of the script directory
        project_root = SCRIPT_DIR.parent

        # Define the directory where logs will be stored
        logs_dir = BOTH_LOG_DIR
        logs_dir.mkdir(parents=True, exist_ok=True)  # Create the directory if it doesn't exist

        # Load ignore patterns from .gitignore or other sources
        ignore_patterns = load_gitignore_patterns(project_root)

        # Create logs for all Python and HTML files, ignoring specified patterns
        create_app_logs(project_root, logs_dir, {'.py', '.html'}, ignore_patterns)

        # Print the location of the generated logs
        print(f"Logs for all Python and HTML files in {project_root} have been created in {logs_dir}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
