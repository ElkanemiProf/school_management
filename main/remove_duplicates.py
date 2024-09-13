import os
from collections import defaultdict

# Directory where your static files are located
STATIC_DIR = r'C:\Users\HP\Desktop\data science\UNITY\school_management\main\static'


# Dictionary to store file hashes and their paths
file_hashes = defaultdict(list)

for root, dirs, files in os.walk(STATIC_DIR):
    for file in files:
        filepath = os.path.join(root, file)
        # Get the file size or content as a simple way to identify duplicates
        file_size = os.path.getsize(filepath)
        file_hashes[file_size].append(filepath)

# List of duplicate files
duplicates = [paths for paths in file_hashes.values() if len(paths) > 1]

# Remove duplicates
for duplicate_group in duplicates:
    # Keep the first file, remove the rest
    for duplicate_file in duplicate_group[1:]:
        os.remove(duplicate_file)
        print(f"Removed {duplicate_file}")
