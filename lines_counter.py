import os
import argparse
import fnmatch
import logging


def setup_logging(log_level):
    """Set up logging with the specified level."""
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {log_level}")
    
    logging.basicConfig(
        level=numeric_level,
        format='%(levelname)s: %(message)s',
    )


def count_lines_in_file(file_path):
    """Count the number of lines in a given file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            line_count = len(file.readlines())
            logging.debug(f"File: {file_path} - {line_count} lines")
            return line_count
    except Exception as e:
        logging.error(f"Error reading {file_path}: {e}")
        return 0


def should_exclude(path, exclude_files, exclude_dirs):
    """
    Check if a file or directory should be excluded based on patterns.
    
    Args:
        path (str): Path to check
        exclude_files (list): List of file patterns to exclude
        exclude_dirs (list): List of directory patterns to exclude
        
    Returns:
        bool: True if the path should be excluded, False otherwise
    """
    name = os.path.basename(path)
    
    # Check if it's a directory pattern
    if os.path.isdir(path):
        for pattern in exclude_dirs:
            if fnmatch.fnmatch(name, pattern):
                return True
    # Check if it's a file pattern
    else:
        for pattern in exclude_files:
            if fnmatch.fnmatch(name, pattern):
                return True
    
    return False


def count_lines_in_directory(directory, extensions=None, exclude_files=None, exclude_dirs=None):
    """
    Count lines of code in all files with specified extensions within a directory and its subdirectories.
    
    Args:
        directory (str): Path to the directory to search
        extensions (list): List of file extensions to include (e.g., ['.py', '.html', '.md'])
        exclude_files (list): List of file patterns to exclude
        exclude_dirs (list): List of directory patterns to exclude
    
    Returns:
        dict: Dictionary with extensions as keys and line counts as values
    """
    if extensions is None:
        extensions = ['.py', '.html', '.md']
    
    if exclude_files is None:
        exclude_files = []
    
    if exclude_dirs is None:
        exclude_dirs = []
    
    # Initialize counters for each extension
    extension_counts = {ext: 0 for ext in extensions}
    file_counts = {ext: 0 for ext in extensions}
    file_details = {ext: [] for ext in extensions}
    
    logging.info(f"Scanning directory: {directory}")
    logging.info(f"Extensions to include: {', '.join(extensions)}")
    
    if exclude_files:
        logging.info(f"File patterns to exclude: {', '.join(exclude_files)}")
    if exclude_dirs:
        logging.info(f"Directory patterns to exclude: {', '.join(exclude_dirs)}")
    
    # Walk through the directory and its subdirectories
    for root, dirs, files in os.walk(directory):
        # Modify dirs in-place to exclude directories
        dirs_before = len(dirs)
        dirs[:] = [d for d in dirs if not should_exclude(os.path.join(root, d), [], exclude_dirs)]
        dirs_excluded = dirs_before - len(dirs)
        
        if dirs_excluded > 0:
            logging.debug(f"Excluded {dirs_excluded} directories in {root}")
        
        for file in files:
            file_path = os.path.join(root, file)
            
            # Skip excluded files
            if should_exclude(file_path, exclude_files, []):
                logging.debug(f"Excluding file: {file_path}")
                continue
                
            # Check if the file has one of the target extensions
            file_ext = os.path.splitext(file)[1].lower()
            if file_ext in extensions:
                line_count = count_lines_in_file(file_path)
                
                # Update the counts
                extension_counts[file_ext] += line_count
                file_counts[file_ext] += 1
                
                # Store file details for detailed reporting
                file_details[file_ext].append((file_path, line_count))
    
    return extension_counts, file_counts, file_details


def main():
    parser = argparse.ArgumentParser(description='Count lines of code in specified file types')
    parser.add_argument('directory', type=str, help='Directory to scan')
    parser.add_argument('--extensions', type=str, nargs='+', default=['.py', '.html', '.md'],
                        help='File extensions to count (default: .py .html .md)')
    parser.add_argument('--exclude-files', type=str, nargs='+', default=[],
                        help='File patterns to exclude (e.g., "test_*.py", "setup.py")')
    parser.add_argument('--exclude-dirs', type=str, nargs='+', default=[],
                        help='Directory patterns to exclude (e.g., "venv", ".*_cache")')
    parser.add_argument('--log-level', type=str, default='INFO',
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help='Set the logging level (default: INFO)')
    parser.add_argument('--detailed', action='store_true',
                        help='Show detailed information about each file')
    
    args = parser.parse_args()
    
    # Set up logging
    setup_logging(args.log_level)
    
    # Make sure extensions start with a dot
    extensions = [ext if ext.startswith('.') else f'.{ext}' for ext in args.extensions]
    
    # Count the lines
    extension_counts, file_counts, file_details = count_lines_in_directory(
        args.directory, 
        extensions, 
        args.exclude_files, 
        args.exclude_dirs
    )
    
    # Print the results
    print(f"\nResults for directory: {os.path.abspath(args.directory)}\n")
    print(f"{'Extension':<10} {'Files':<8} {'Lines':<10}")
    print("-" * 30)
    
    total_lines = 0
    total_files = 0
    
    for ext in sorted(extension_counts.keys()):
        lines = extension_counts[ext]
        files = file_counts[ext]
        print(f"{ext:<10} {files:<8} {lines:<10}")
        total_lines += lines
        total_files += files
    
    print("-" * 30)
    print(f"{'Total':<10} {total_files:<8} {total_lines:<10}")
    
    # Print exclusion information if any patterns were specified
    if args.exclude_files or args.exclude_dirs:
        print("\nExclusions applied:")
        if args.exclude_files:
            print(f"  Files: {', '.join(args.exclude_files)}")
        if args.exclude_dirs:
            print(f"  Directories: {', '.join(args.exclude_dirs)}")
            
    # Print detailed file information if requested
    if args.detailed:
        print("\nDetailed File Information:")
        print(f"{'File':<60} {'Lines':<10}")
        print("-" * 70)
        
        for ext in sorted(extension_counts.keys()):
            if file_counts[ext] > 0:
                print(f"\n{ext} files:")
                
                # Sort files by line count in descending order
                sorted_files = sorted(file_details[ext], key=lambda x: x[1], reverse=True)
                
                for file_path, line_count in sorted_files:
                    relative_path = os.path.relpath(file_path, args.directory)
                    print(f"{relative_path:<60} {line_count:<10}")


if __name__ == "__main__":
    main()

'''
# Example usage
# --------------

# Basic usage with INFO level (default)
python count_lines.py /path/to/directory

# Use DEBUG level to see details about each file processed
python count_lines.py /path/to/directory --log-level DEBUG

# Show detailed information about each file with line counts
python count_lines.py /path/to/directory --detailed

# Combine detailed output with specific log level
python count_lines.py /path/to/directory --detailed --log-level WARNING

# Full example with exclusions
python count_lines.py /path/to/directory --extensions py js html --exclude-dirs node_modules --exclude-files "*.min.*" --detailed --log-level INFO
'''
