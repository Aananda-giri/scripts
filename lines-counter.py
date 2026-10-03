import os
import subprocess
import argparse
import fnmatch
import io
import logging
import tokenize


DEFAULT_EXTENSIONS = ['.py', '.html', '.md', '.js', '.ts', '.tsx', '.dart']
IGNORE_DIRS = ['node_modules', '.archive', 'common', '.venv', 'venv', '.vscode', 'logs', '__pycache__', 'notebooks', 'google_chat_api', 'raw']

def setup_logging(log_level):
    """Set up logging with the specified level."""
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {log_level}")
    
    logging.basicConfig(
        level=numeric_level,
        format='%(levelname)s: %(message)s',
    )


C_STYLE_EXTENSIONS = {'.js', '.ts', '.tsx', '.jsx', '.dart', '.css', '.java', '.c', '.cpp', '.go'}
MARKUP_EXTENSIONS = {'.html', '.htm', '.md', '.xml'}


def python_code_lines(source):
    """Line numbers holding Python code: no blanks, # comments, or docstrings."""
    skip = {tokenize.COMMENT, tokenize.NL, tokenize.NEWLINE, tokenize.INDENT,
            tokenize.DEDENT, tokenize.ENCODING, tokenize.ENDMARKER}
    tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
    code_lines = set()
    for i, tok in enumerate(tokens):
        if tok.type in skip:
            continue
        if tok.type == tokenize.STRING:
            # A string that is a whole statement on its own is a docstring
            prev_type = tokens[i - 1].type if i > 0 else tokenize.NEWLINE
            next_type = tokens[i + 1].type if i + 1 < len(tokens) else tokenize.NEWLINE
            if prev_type in (tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT, tokenize.NL, tokenize.ENCODING) \
                    and next_type in (tokenize.NEWLINE, tokenize.ENDMARKER):
                continue
        code_lines.update(range(tok.start[0], tok.end[0] + 1))
    return len(code_lines)


def c_style_code_lines(source):
    """Count lines with code, ignoring blanks, // and /* */ comments (string-aware)."""
    count = 0
    in_block = False
    string_quote = None  # open ` template literal carries across lines
    for line in source.splitlines():
        has_code = False
        i = 0
        while i < len(line):
            ch, nxt = line[i], line[i + 1:i + 2]
            if in_block:
                if ch == '*' and nxt == '/':
                    in_block = False
                    i += 2
                    continue
            elif string_quote:
                has_code = True
                if ch == '\\':
                    i += 2
                    continue
                if ch == string_quote:
                    string_quote = None
            elif ch == '/' and nxt == '/':
                break
            elif ch == '/' and nxt == '*':
                in_block = True
                i += 2
                continue
            elif ch in '"\'`':
                string_quote = ch
                has_code = True
            elif not ch.isspace():
                has_code = True
            i += 1
        if string_quote in ('"', "'"):
            string_quote = None  # plain quotes cannot span lines
        if has_code:
            count += 1
    return count


def markup_code_lines(source):
    """Count non-blank lines, ignoring <!-- --> comments."""
    count = 0
    in_comment = False
    for line in source.splitlines():
        rest = line
        has_content = False
        while rest:
            if in_comment:
                end = rest.find('-->')
                if end == -1:
                    break
                in_comment = False
                rest = rest[end + 3:]
            else:
                start = rest.find('<!--')
                if rest[:start if start != -1 else None].strip():
                    has_content = True
                if start == -1:
                    break
                in_comment = True
                rest = rest[start + 4:]
        if has_content:
            count += 1
    return count


def count_lines_in_file(file_path):
    """Count lines of code in a file, skipping blank and comment lines."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            source = file.read()
        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.py':
            try:
                line_count = python_code_lines(source)
            except (tokenize.TokenError, SyntaxError):
                # Unparseable file: fall back to skipping blanks and # lines
                line_count = sum(1 for l in source.splitlines()
                                 if l.strip() and not l.strip().startswith('#'))
        elif ext in C_STYLE_EXTENSIONS:
            line_count = c_style_code_lines(source)
        elif ext in MARKUP_EXTENSIONS:
            line_count = markup_code_lines(source)
        else:
            line_count = sum(1 for l in source.splitlines() if l.strip())
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


def git_tracked_files(directory):
    """Return paths of git-tracked files under directory, or None if it isn't a git repo."""
    try:
        result = subprocess.run(['git', 'ls-files', '-z'], cwd=directory,
                                capture_output=True, text=True, check=True)
    except (OSError, subprocess.CalledProcessError):
        return None
    return [os.path.join(directory, f) for f in result.stdout.split('\0') if f]


def count_lines_in_directory(directory, extensions=None, exclude_files=None, exclude_dirs=None, all_files=False):
    """
    Count lines of code in all files with specified extensions within a directory and its subdirectories.
    
    Args:
        directory (str): Path to the directory to search
        extensions (list): List of file extensions to include (e.g., ['.py', '.html', '.md'])
        exclude_files (list): List of file patterns to exclude
        exclude_dirs (list): List of directory patterns to exclude
        all_files (bool): Walk every file on disk instead of only git-tracked files
    
    Returns:
        dict: Dictionary with extensions as keys and line counts as values
    """
    if extensions is None:
        extensions = DEFAULT_EXTENSIONS
    
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
    
    tracked = None if all_files else git_tracked_files(directory)
    if tracked is not None:
        logging.info(f"Counting {len(tracked)} git-tracked files")
        for file_path in tracked:
            parts = os.path.relpath(file_path, directory).split(os.sep)
            if any(fnmatch.fnmatch(d, pat) for d in parts[:-1] for pat in exclude_dirs):
                continue
            if any(fnmatch.fnmatch(parts[-1], pat) for pat in exclude_files):
                continue
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext in extensions and os.path.isfile(file_path):
                line_count = count_lines_in_file(file_path)
                extension_counts[file_ext] += line_count
                file_counts[file_ext] += 1
                file_details[file_ext].append((file_path, line_count))
        return extension_counts, file_counts, file_details

    # Not a git repo (or --all-files): walk every file on disk
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
    parser.add_argument('directory', type=str, nargs='?', default=os.getcwd(), help='Directory to scan')
    parser.add_argument('--extensions', type=str, nargs='+', default=DEFAULT_EXTENSIONS,
                        help='File extensions to count (default: .py .html .md .ts)')
    parser.add_argument('--exclude-files', type=str, nargs='+', default=['yarn.lock', 'package-lock.json'],
                        help='File patterns to exclude (e.g., "test_*.py", "setup.py")')
    parser.add_argument('--exclude-dirs', type=str, nargs='+', default=IGNORE_DIRS,
                        help='Directory patterns to exclude (e.g., "venv", ".*_cache")')
    parser.add_argument('--log-level', type=str, default='WARNING',
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help='Set the logging level (default: INFO)')
    parser.add_argument('--detailed', action='store_true', default=False,
                        help='Show detailed information about each file')
    parser.add_argument('--all-files', action='store_true', default=False,
                        help='Count every file on disk, not just git-tracked ones')
    
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
        args.exclude_dirs,
        args.all_files
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

# Full example with exclusions, without --detailed
python count_lines.py /path/to/directory --extensions py js html --exclude-dirs node_modules --exclude-files "*.min.*" --log-level INFO

# simple way: put this file in directory you want to count lines
python3 lines_counter.py

'''
