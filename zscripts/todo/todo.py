
"""
We need to define a function that looks for this kind of logic ```python .... ``` and seperates it from the log as as seperate file with sectional logs and no newlines.
Plan for other ``` logic as well. ```plaintext    
additional_content.txt

We also need to create a count.log that keeps track of uniqe words and their counts.

example:
### System Overview
This pseudocode outlines a system with several components:
- **Markdown Parser:** Parses the markdown file into manageable chunks or lines.
- **Log Line Processor:** Processes each line for further action.
- **Log Line Manager:** Manages the processed lines based on their content and context.
- **Log Content Manager:** Executes actions based on processed lines, like updating todos or managing projects.
- **Tools:** Additional tools for statistics, keyword extraction, and project management.


Some of these are names that are not specific to any one thing, but are for the particular user they might be relevant. 
We should try to determine the relevance of these names to the user and their project. 
We can do this by looking at the context in which they are used and the content of the surrounding text. 
For example, if the user is talking about a project management tool, then the names "Log Line Manager" and "Log Content Manager" are likely to be relevant. 
If the user is talking about a markdown parser, then the name "Markdown Parser" is likely to be relevant. 
We can also look at the content of the surrounding text to see if there are any other clues that might help us determine the relevance of these names to the user and their project.

We always need to stay within the bounds of markdown walking when handling this logic. 
We can handle the linecontent(log.txt at end of line), and the additional_content.txt specifically.

"""
import os
import re

def parse_and_log_markdown(file_path, log_path):
    """ Parses the markdown file and logs the sections with sub-items as specified. """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = iter(file.readlines())
    except FileNotFoundError:
        print(f"Error: The file {file_path} does not exist.")
        return

    try:
        with open(log_path, 'w', encoding='utf-8') as log_file:
            current_section = None
            for line in lines:
                line = line.strip()
                section_match = re.match(r'###\s+(.*)', line)
                if section_match:
                    current_section = section_match.group(1).strip().replace(' ', '_').lower()
                elif current_section:
                    subheading_match = re.match(r'\*\*(.*):\*\*', line)
                    if subheading_match:
                        current_subheading = subheading_match.group(1).strip().lower()
                        line = next(lines, '').strip()
                        while line and not line.startswith('**') and not line.startswith('###'):
                            if line.startswith('-'):
                                log_file.write(f"{current_section}|**{current_subheading}:**|{line}\n")
                            line = next(lines, '').strip()
    except IOError as e:
        print(f"Failed to write to {log_path}: {e}")

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    markdown_path = os.path.join(script_dir, 'todo.md')
    log_path = os.path.join(script_dir, 'log.txt')  # Path to save the log file

    parse_and_log_markdown(markdown_path, log_path)
    print("Markdown content has been processed and logged.")

if __name__ == '__main__':
    main()
