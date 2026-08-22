#!/usr/bin/env python3
"""Find and remove build/cache junk folders (.venv, node_modules, __pycache__, ...).

Default action is always a dry-run report sorted by size — the one number
that actually matters when deciding what to clean. Nothing is ever deleted
without --yes.

Examples:
    cleanup-script.py                    # report the standard targets
    cleanup-script.py --yes              # delete the standard targets
    cleanup-script.py dist .cache --yes  # delete these instead of the defaults
    cleanup-script.py --top              # what's actually big in this folder
    cleanup-script.py --top -C ~/Downloads  # drill into a subfolder and repeat
"""

import argparse
import shutil
import sys
from pathlib import Path

try:
    import readline
except ImportError:  # not in stdlib on Windows
    readline = None

STANDARD_TARGETS = {".venv", "node_modules", ".next", "__pycache__", "build"}


def human_size(num_bytes: float) -> str:
    for unit in ("B", "K", "M", "G", "T"):
        if num_bytes < 1024:
            return f"{num_bytes:.1f}{unit}"
        num_bytes /= 1024
    return f"{num_bytes:.1f}P"


def folder_size(path: Path) -> int:
    total = 0
    for entry in path.rglob("*"):
        if entry.is_file() and not entry.is_symlink():
            total += entry.stat().st_size
    return total


def render_bar(size: int, max_size: int, width: int = 30) -> str:
    if max_size <= 0:
        return "░" * width
    filled = round(width * size / max_size)
    return "█" * filled + "░" * (width - filled)


def top_level_breakdown(root: Path) -> tuple[list[tuple[Path, int]], bool]:
    """Size of every immediate file/subfolder under root — one level, not a
    flat recursive dump, so the result tells you where to look next rather
    than burying the one big folder in thousands of individual files."""
    entries = []
    truncated = False
    try:
        children = list(root.iterdir())
    except PermissionError:
        return entries, True
    for child in children:
        if child.is_symlink():
            continue
        try:
            if child.is_dir():
                size = folder_size(child)
            elif child.is_file():
                size = child.stat().st_size
            else:
                continue
        except (PermissionError, OSError):
            truncated = True
            continue
        entries.append((child, size))
    return entries, truncated


def show_top(root: Path, count: int) -> list[Path]:
    """Returns the shown paths (not just prints them) so callers — namely
    drill()'s tab-completion — can reuse them without re-walking the tree."""
    entries, truncated = top_level_breakdown(root)
    if not entries:
        print(f"Nothing under {root}")
        return []
    entries.sort(key=lambda pair: -pair[1])
    total = sum(size for _, size in entries)
    shown = entries[:count]
    max_size = shown[0][1] if shown else 0

    print(f"{root}  ({human_size(total)} total, {len(entries)} entries)\n")
    for path, size in shown:
        pct = (size / total * 100) if total else 0
        tag = "/" if path.is_dir() else ""
        hint = "  [cleanup target]" if path.name in STANDARD_TARGETS else ""
        print(f"{human_size(size):>8} {pct:5.1f}%  {render_bar(size, max_size)}  {path.name}{tag}{hint}")

    remaining = len(entries) - len(shown)
    if remaining > 0:
        print(f"\n... {remaining} more entries not shown (rerun with a larger --top N)")
    if truncated:
        print("(some entries skipped — permission denied)")
    return [p for p, _ in shown]


def find_targets(root: Path, names: set[str]) -> list[Path]:
    """One walk, matching all names at once, pruning into matches instead of
    descending through them — os.walk-style recursion by hand so we control
    which directories get skipped once found."""
    found = []
    stack = [root]
    while stack:
        current = stack.pop()
        try:
            children = list(current.iterdir())
        except PermissionError:
            continue
        for child in children:
            if not child.is_dir() or child.is_symlink():
                continue
            if child.name in names:
                found.append(child)  # don't descend further into a match
            else:
                stack.append(child)
    return found


def report_and_delete(root: Path, names: set[str], delete: bool) -> None:
    """Shared by both --yes (pre-decided) and the interactive picker (asks
    right before acting) — one code path, so the two entry points can never
    drift apart on what actually gets deleted."""
    matches = find_targets(root, names)
    if not matches:
        print(f"Nothing matching {sorted(names)} under {root}")
        return

    sized = sorted(((p, folder_size(p)) for p in matches), key=lambda pair: -pair[1])
    total = sum(size for _, size in sized)

    for path, size in sized:
        print(f"{human_size(size):>8}  {path}")
    print(f"{human_size(total):>8}  total ({len(sized)} folder(s))")

    if not delete:
        return

    freed = 0
    for path, size in sized:
        try:
            shutil.rmtree(path)
            freed += size
        except OSError as e:
            print(f"error deleting {path}: {e}", file=sys.stderr)
    print(f"\nFreed {human_size(freed)}.")


def _completer(names: list[str]):
    def complete(text: str, state: int):
        matches = [n for n in names if n.startswith(text)]
        return matches[state] if state < len(matches) else None
    return complete


def drill(start: Path) -> None:
    """The 't' branch of the picker: show top consumers, then let the user
    walk straight into one of the folders shown instead of quitting and
    retyping -C. Tab-completes against exactly the subfolders just listed —
    not an arbitrary filesystem path completer — so you can only tab into
    something that's actually there. Ends by printing the -C flag that
    reaches wherever they ended up, same "teach the shortcut" habit as the
    rest of the picker."""
    cur = start
    while True:
        shown = show_top(cur, 20)
        if readline is not None:
            dir_names = [p.name for p in shown if p.is_dir()]
            readline.set_completer_delims("")  # names can contain spaces etc.
            readline.set_completer(_completer(dir_names))
            readline.parse_and_bind("tab: complete")
        try:
            sub = input("\nDrill into a folder above (name), or Enter to go back: ").strip()
        finally:
            if readline is not None:
                readline.set_completer(None)
        if not sub:
            break
        candidate = cur / sub.rstrip("/")
        if candidate.is_dir():
            cur = candidate
        else:
            print(f"No such folder here: {sub}")
    if cur == start:
        print("\nNext time:  cleanup-script.py --top")
    else:
        print(f"\nNext time:  cleanup-script.py --top -C {cur}")


def interactive(root: Path) -> int:
    """Bare `cleanup-script.py`, no args — every capability reachable without
    memorizing a flag. Each branch calls the exact same functions the flags
    call, then prints the flag that does the same thing next time, so the
    picker teaches its own way out. Loops back to the menu after each action
    — quitting is a choice ('q'/Enter/Ctrl-D), never a side effect of finishing
    one thing."""
    while True:
        print(f"\ncleanup-script — {root}\n")
        print("  [t] top space consumers in this folder")
        print("  [c] clean junk folders (.venv, node_modules, __pycache__, ...)")
        print("  [f] find/clean folders by a name you choose")
        print("  [q] quit")
        try:
            choice = input("\n> ").strip().lower()
        except EOFError:
            print()
            return 0

        if choice in ("", "q"):
            return 0

        if choice == "t":
            drill(root)
            continue

        if choice in ("c", "f"):
            if choice == "f":
                name = input("Folder name: ").strip()
                if not name:
                    print("Nothing entered.")
                    continue
                names = {name}
                example = f"cleanup-script.py {name}"
            else:
                names = STANDARD_TARGETS
                example = "cleanup-script.py"

            report_and_delete(root, names, delete=False)
            confirm = input("\nDelete these? (yes/no): ").strip().lower()
            if confirm in ("yes", "y"):
                report_and_delete(root, names, delete=True)
                print(f"\nNext time:  {example} --yes")
            else:
                print(f"\nNext time (dry run):  {example}")
            continue

        print("Not a valid choice.")


def main() -> int:
    if len(sys.argv) == 1:
        return interactive(Path(".").resolve())

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("names", nargs="*", default=None,
                         help=f"folder names to target (default: {' '.join(sorted(STANDARD_TARGETS))})")
    parser.add_argument("-C", "--root", type=Path, default=Path("."),
                         help="directory to scan (default: current directory)")
    parser.add_argument("--yes", action="store_true",
                         help="actually delete; without this, only report")
    parser.add_argument("--top", nargs="?", const=20, type=int, default=None,
                         metavar="N",
                         help="show the N biggest files/folders directly under "
                              "--root (default 20) instead of hunting for junk names")
    args = parser.parse_args()

    root = args.root.resolve()
    if not root.exists():
        print(f"No such file or directory: {root}", file=sys.stderr)
        return 1

    if args.top is not None:
        show_top(root, args.top)
        print("\nDrill in with: cleanup-script.py --top -C <one of the folders above>")
        return 0

    names = set(args.names) if args.names else STANDARD_TARGETS
    report_and_delete(root, names, delete=args.yes)
    if not args.yes:
        print("\nDry run — rerun with --yes to delete these.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
