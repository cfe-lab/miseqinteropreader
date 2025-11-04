"""Validate command - check run directory structure and available metrics."""

import argparse
import sys
from pathlib import Path

from ..interop_reader import InterOpReader, MetricFile


def add_arguments(parser: argparse.ArgumentParser) -> None:
    """Add arguments for the validate command."""
    parser.add_argument(
        "run_dir",
        type=Path,
        help="Path to the MiSeq run directory",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )


def execute(args: argparse.Namespace) -> int:
    """Execute the validate command."""
    run_dir = args.run_dir
    verbose = args.verbose

    # Track if any errors occurred
    has_errors = False

    # Check if directory exists
    if not run_dir.exists():
        print(f"✗ Run directory does not exist: {run_dir}", file=sys.stderr)
        return 1

    if not run_dir.is_dir():
        print(f"✗ Path is not a directory: {run_dir}", file=sys.stderr)
        return 1

    print(f"✓ Run directory exists: {run_dir.name}")

    # Check for InterOp directory
    interop_dir = run_dir / "InterOp"
    if interop_dir.exists() and interop_dir.is_dir():
        print(f"✓ InterOp directory found")
    else:
        print(f"✗ InterOp directory not found", file=sys.stderr)
        has_errors = True

    # Check for SampleSheet.csv
    samplesheet_path = run_dir / "SampleSheet.csv"
    if samplesheet_path.exists():
        print(f"✓ SampleSheet.csv found")
    else:
        print(f"✗ SampleSheet.csv not found", file=sys.stderr)
        has_errors = True

    # Check for marker files
    needsprocessing_marker = run_dir / "needsprocessing"
    qc_uploaded_marker = run_dir / "qc_uploaded"

    if needsprocessing_marker.exists():
        print(f"✓ Marker: needsprocessing")
    else:
        print(f"  Marker: needsprocessing (not present)")

    if qc_uploaded_marker.exists():
        print(f"✓ Marker: qc_uploaded")
    else:
        print(f"  Marker: qc_uploaded (not present)")

    # If basic checks failed, stop here
    if has_errors:
        return 1

    # Try to initialize the InterOpReader
    try:
        reader = InterOpReader(run_dir)
    except Exception as e:
        print(f"\n✗ Failed to initialize InterOpReader: {e}", file=sys.stderr)
        if verbose:
            import traceback

            traceback.print_exc()
        return 1

    # Check available metric files
    print("\nAvailable metrics:")
    available_count = 0
    total_count = 0

    for metric in MetricFile:
        total_count += 1
        try:
            metric_file = metric.value.get_file(reader.interop_dir)
            print(f"✓ {metric.name}")
            available_count += 1
            if verbose:
                print(f"  -> {metric_file.name}")
        except FileNotFoundError:
            print(f"✗ {metric.name} (missing)")

    print(f"\nSummary: {available_count}/{total_count} metrics available")

    if available_count == 0:
        print("\n✗ No metrics found in InterOp directory", file=sys.stderr)
        return 1

    print(f"\n✓ Run directory is valid and ready for analysis")
    return 0
