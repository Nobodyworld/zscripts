# zscripts/scripts/readme/readme_build.py

import os

def compile_readme():
    # Define the path to the readme directory and the build order file
    readme_dir = 'zscripts/zreadme'

    # List the build order as a list of filenames
    build_order = [
        '0-Overview.txt',
        '1-Core.txt',
        '2-Common.txt',
        '3-Models.txt',
        '4-Plan.txt',
    ]


    # Initialize the compiled content as an empty string
    compiled_content = ''

    # Process each file in the build order
    for filename in build_order:
        filename = filename.strip()  # Remove any extra whitespace or new lines
        readme_file = os.path.join(readme_dir, filename)
        try:
            with open(readme_file, 'r', encoding='utf-8') as file:
                compiled_content += file.read() + '\n\n'  # Add two newlines for spacing
        except FileNotFoundError:
            print(f"Warning: {readme_file} not found and will be skipped.")
        except UnicodeDecodeError as e:
            print(f"Error reading {readme_file}: {e}")
    
    # Write the compiled content to the main README.md file in the project root
    output_readme_path = 'README.md'
    with open(output_readme_path, 'w', encoding='utf-8') as file:
        file.write(compiled_content)

    print(f"Readme compiled and saved to {output_readme_path} at {os.path.abspath(output_readme_path)}")

if __name__ == '__main__':
    compile_readme()
