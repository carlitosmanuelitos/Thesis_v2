import json
import subprocess
from datetime import datetime

# Function to get the current list of packages
def get_current_packages():
    packages_list = subprocess.check_output(["conda", "list", "--json"], text=True)
    packages = json.loads(packages_list)
    return {package["name"]: package["version"] for package in packages}

# Function to compare package lists
def compare_packages(old_packages, new_packages):
    added = {k: v for k, v in new_packages.items() if k not in old_packages}
    removed = {k: v for k, v in old_packages.items() if k not in new_packages}
    return added, removed

# Get the current conda environment name and package list
conda_env_name = "tf_metal"  # Assuming the script is run within the desired environment
current_packages = get_current_packages()
current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Define the file path
file_path = f"./conda env/conda_packages_{conda_env_name}.json"

try:
    # Attempt to read the existing data
    with open(file_path, "r") as file:
        existing_data = json.load(file)
except FileNotFoundError:
    # If the file does not exist, prepare to write new data
    existing_data = []

# Determine if there are changes and what they are
if not existing_data or existing_data[-1]["packages"] != current_packages:
    added, removed = compare_packages(existing_data[-1]["packages"], current_packages) if existing_data else (current_packages, {})
    
    # Prepare the new entry
    new_entry = {
        "run_time": current_time,
        "environment_name": conda_env_name,
        "packages": current_packages,
        "added": added,
        "removed": removed
    }
    
    # Append the new entry
    existing_data.append(new_entry)
    
    # Save the updated data back to the JSON file
    with open(file_path, "w") as file:
        json.dump(existing_data, file, indent=4)

    print(f"Package list updated and saved to {file_path}")
else:
    print("No changes detected in the package list; file not updated.")
