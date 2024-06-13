import re
import subprocess
import sys

# Define the file path
file_path = r"c:\Users\siddk\source\repos\Quiz\Dicord boy\main.py"


# Read the file content
try:
    with open(file_path, 'r') as file:
        content = file.read()
except Exception as e:
    print(f"Failed to read file: {e}")
    sys.exit(1)

# Regex to find the imports
import_lines = re.findall(r'^\s*(?:import|from)\s+([\w\.]+)', content, re.MULTILINE)

# List to hold unique package names
packages = set(import_lines)

# Process the found import lines to get package names
# for line in import_lines:
#     parts = line.split()
#     if 'import' in parts:
#         packages.add(parts[0].split('.')[0])
#     elif 'from' in parts:
#         packages.add(parts[1].split('.')[0])

# List of package names to exclude (built-in modules)
excluded_packages = {
    'os', 'sys', 'time', 're', 'subprocess', 'collections', 'json', 
    'math', 'datetime', 'itertools', 'functools', 'random', 'string',
    'pathlib', 'typing', 'logging', 'shutil', 'urllib', 'http', 'socket'
}

# Filter out built-in modules
packages = packages.difference(excluded_packages)

# Write packages to requirements.txt
try:
    with open('requirements.txt', 'w') as req_file:
        for package in sorted(packages):
            req_file.write(f"{package}\n")
            print(package)
except Exception as e:
    print(f"Failed to write requirements.txt: {e}")
    sys.exit(1)

# Print the packages to be installed
print("The following packages will be installed:")
for package in sorted(packages):
    print(f"- {package}")

# Install the packages using pip
print("\nStarting installation...")
try:
    result = subprocess.run(['pip', 'install', '-r', 'requirements.txt'], check=True)
    if result.returncode == 0:
        print("Installation completed successfully.")
    else:
        print("Installation completed with errors.")
except subprocess.CalledProcessError as e:
    print(f"Installation failed: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
