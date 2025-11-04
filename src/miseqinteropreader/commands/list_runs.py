"""List command - list available runs in a directory."""

import argparse
import re
from pathlib import Path

from ..interop_reader import InterOpReader


def add_arguments(parser: argparse.ArgumentParser) -> None:
    """Add arguments for the list command."""
    parser.add_argument(
        "runs_dir",
        type=Path,
        help="Path to the directory containing MiSeq runs",
    )
    parser.add_argument(
        "--needs-processing",
        action="store_true",
        help="Only show runs that need processing",
    )
    parser.add_argument(
        "--qc-uploaded",
        action="store_true",
        help="Only show runs with QC uploaded",
    )
    parser.add_argument(
        "--pattern",
        type=str,
        help="Filter runs by name pattern (regex)",
    )
    parser.add_argument(
        "--full-path",
        action="store_true",
        help="Show full paths instead of just run names",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output with status information",
    )


def is_valid_run_directory(path: Path) -> bool:
    """Check if a path looks like a valid MiSeq run directory.

    Args:
        path: Path to check

    Returns:
        True if it appears to be a valid run directory
    """
    if not path.is_dir():
        return False

    # Check for InterOp directory
    if not (path / "InterOp").exists():
        return False

    # Check for SampleSheet.csv
    if not (path / "SampleSheet.csv").exists():
        return False

    return True


def execute(args: argparse.Namespace) -> int:
    """Execute the list command."""
    runs_dir = args.runs_dir

    if not runs_dir.exists():
        print(f"Error: Directory does not exist: {runs_dir}")
        return 1

    if not runs_dir.is_dir():
        print(f"Error: Path is not a directory: {runs_dir}")
        return 1

    # Compile pattern if provided
    pattern = None
    if args.pattern:
        try:
            pattern = re.compile(args.pattern)
        except re.error as e:
            print(f"Error: Invalid regex pattern: {e}")
            return 1

    # Find all potential run directories
    found_runs = []
    
    for item in sorted(runs_dir.iterdir()):
        if not item.is_dir():
            continue

        # Skip if doesn't match pattern
        if pattern and not pattern.search(item.name):
            continue

        # Check if it's a valid run directory
        if not is_valid_run_directory(item):
            continue

        # Try to read the run
        try:
            reader = InterOpReader(item)
            
            # Apply filters
            if args.needs_processing and not reader.needsprocessing:
                continue
            if args.qc_uploaded and not reader.qc_uploaded:
                continue

            found_runs.append((item, reader))
        except Exception:
            # Skip runs that can't be read
            continue

    # Display results
    if not found_runs:
        print("No runs found matching criteria")
        return 0

    if args.verbose:
        # Verbose output with status
        print(f"Found {len(found_runs)} run(s):\n")
        for run_path, reader in found_runs:
            display_path = str(run_path) if args.full_path else run_path.name
            status_parts = []
            if reader.needsprocessing:
                status_parts.append("needs-processing")
            if reader.qc_uploaded:
                status_parts.append("qc-uploaded")
            status = ", ".join(status_parts) if status_parts else "no markers"
            print(f"{display_path}")
            print(f"  Status: {status}")
            print()
    else:
        # Simple list output
        for run_path, _ in found_runs:
            display_path = str(run_path) if args.full_path else run_path.name
            print(display_path)

    return 0
