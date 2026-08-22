'''
## List 20 largest folders in .
du -ah . | sort -rh | head -20

Standard Cleanup:
.venv
node_modules
.next
__pycache__
build
'''


import os
import shutil
from pathlib import Path


def find_all_folders(root_dir, folder_name):
    """
    Find all occurrences of a specific folder within a directory tree.
    
    Args:
        root_dir (str): Root directory to start searching from
        folder_name (str): Name of the folder to find
    
    Returns:
        list: List of paths to all matching folders
    """
    found_folders = []
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        if folder_name in dirnames:
            folder_path = os.path.join(dirpath, folder_name)
            found_folders.append(folder_path)
    
    return found_folders


def delete_all_folders(root_dir, folder_name, dry_run=True):
    """
    Delete all occurrences of a specific folder within a directory tree.
    
    Args:
        root_dir (str): Root directory to start searching from
        folder_name (str): Name of the folder to delete
        dry_run (bool): If True, only show what would be deleted without actually deleting
    
    Returns:
        dict: Dictionary with 'found' and 'deleted' lists
    """
    found_folders = find_all_folders(root_dir, folder_name)
    deleted_folders = []
    
    if dry_run:
        print(f"DRY RUN: Found {len(found_folders)} folder(s) named '{folder_name}':")
        for folder in found_folders:
            print(f"  - {folder}")
        print("\nSet dry_run=False to actually delete these folders.")
    else:
        for folder in found_folders:
            try:
                shutil.rmtree(folder)
                deleted_folders.append(folder)
                print(f"Deleted: {folder}")
            except Exception as e:
                print(f"Error deleting {folder}: {e}")
    
    return {
        'found': found_folders,
        'deleted': deleted_folders
    }


if __name__ == "__main__":
    print("=" * 60)
    print("Folder Search and Delete Tool")
    print("=" * 60)
    print("Working directory: .")
    
    # Show menu first
    print("\n" + "=" * 60)
    print("What would you like to do?")
    print("  1. Show 20 largest folders")
    print("  2. Search for folders")
    print("  3. Delete folders")
    print("  4. Quick cleanup (.venv, node_modules, .next, __pycache__, build)")
    print("  0. Exit")
    print("=" * 60)
    
    choice = input("\nEnter your choice (0-4): ").strip()
    
    if choice == "0":
        print("\nExiting.")
        exit(0)
    
    if choice == "1":
        # Show 20 largest folders
        print("\nFinding 20 largest folders...\n")
        import subprocess
        try:
            result = subprocess.run(
                "du -ah . | sort -rh | head -20",
                shell=True,
                capture_output=True,
                text=True
            )
            print(result.stdout)
        except Exception as e:
            print(f"Error running du command: {e}")
        print("\nDone!")
        exit(0)
    
    if choice == "4":
        # Quick cleanup of common folders
        common_folders = [".venv", "node_modules", ".next", "__pycache__", "build"]
        print("\nQuick cleanup will search and delete:")
        for folder in common_folders:
            print(f"  - {folder}")
        
        confirm = input("\nProceed with quick cleanup? (yes/no): ").strip().lower()
        if confirm not in ["yes", "y"]:
            print("\nQuick cleanup cancelled.")
            exit(0)
        
        total_deleted = 0
        for folder_name in common_folders:
            print(f"\nSearching for '{folder_name}'...")
            folders = find_all_folders(".", folder_name)
            if folders:
                print(f"Found {len(folders)} occurrence(s):")
                for folder in folders:
                    print(f"  - {folder}")
                result = delete_all_folders(".", folder_name, dry_run=False)
                total_deleted += len(result['deleted'])
            else:
                print(f"No '{folder_name}' folders found.")
        
        print(f"\n{'=' * 60}")
        print(f"Quick cleanup complete! Deleted {total_deleted} folder(s) total.")
        print(f"{'=' * 60}")
        exit(0)
    
    if choice not in ["2", "3"]:
        print("\nInvalid choice. Exiting.")
        exit(1)
    
    # Get folder name to search for
    target_folder = input("\nEnter folder name to search for: ").strip()
    if not target_folder:
        print("Error: Folder name cannot be empty.")
        exit(1)
    
    # Find all occurrences
    print(f"\nSearching for '{target_folder}' folders in current directory...\n")
    folders = find_all_folders(".", target_folder)
    
    if not folders:
        print(f"No folders named '{target_folder}' found.")
        exit(0)
    
    print(f"Found {len(folders)} folder(s):")
    for i, folder in enumerate(folders, 1):
        print(f"  {i}. {folder}")
    
    # Handle based on initial choice
    if choice == "2":
        print("\nSearch complete.")
    elif choice == "3":
        confirm = input(f"\nAre you sure you want to delete {len(folders)} folder(s)? (yes/no): ").strip().lower()
        if confirm in ["yes", "y"]:
            print("\nDeleting folders...\n")
            result = delete_all_folders(".", target_folder, dry_run=False)
            print(f"\nSuccessfully deleted {len(result['deleted'])} folder(s).")
        else:
            print("\nDeletion cancelled.")
    
    print("\nDone!")
