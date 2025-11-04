"""Validate command - check run directory structure and available metrics."""

import argparse
from pathlib import Path

from ..cli_utils import (
    Verbosity,
    add_verbosity_arguments,
    configure_verbosity,
    error,
    info,
)
from ..interop_reader import InterOpReader, MetricFile


def add_arguments(parser: argparse.ArgumentParser) -> None:
    """Add arguments for the validate command."""
    parser.add_argument(
        "run_dir",
        type=Path,
        help="Path to the MiSeq run directory",
    )
    add_verbosity_arguments(parser)


def execute(args: argparse.Namespace) -> int:
    """Execute the validate command."""
    configure_verbosity(args)
    run_dir = args.run_dir

    # Track if any errors occurred
    has_errors = False

    # Check if directory exists
    if not run_dir.exists():
        error(f"✗ Run directory does not exist: {run_dir}")
        return 1

    if not run_dir.is_dir():
        error(f"✗ Path is not a directory: {run_dir}")
        return 1

    info(f"✓ Run directory exists: {run_dir.name}")

    # Check for InterOp directory
    interop_dir = run_dir / "InterOp"
    if interop_dir.exists() and interop_dir.is_dir():
        info(f"✓ InterOp directory found")
    else:
        error(f"✗ InterOp directory not found")
        has_errors = True

    # Check for SampleSheet.csv
    samplesheet_path = run_dir / "SampleSheet.csv"
    if samplesheet_path.exists():
        info(f"✓ SampleSheet.csv found")
    else:
        error(f"✗ SampleSheet.csv not found")
        has_errors = True

    # Check for marker files
    needsprocessing_marker = run_dir / "needsprocessing"
    qc_uploaded_marker = run_dir / "qc_uploaded"

    if needsprocessing_marker.exists():
        info(f"✓ Marker: needsprocessing")
    else:
        info(f"  Marker: needsprocessing (not present)", Verbosity.VERBOSE)

    if qc_uploaded_marker.exists():
        info(f"✓ Marker: qc_uploaded")
    else:
        info(f"  Marker: qc_uploaded (not present)", Verbosity.VERBOSE)

    # If basic checks failed, stop here
    if has_errors:
        return 1

    # Try to initialize the InterOpReader
    try:
        reader = InterOpReader(run_dir)
    except Exception as e:
        error(f"\n✗ Failed to initialize InterOpReader: {e}")
        info("", Verbosity.DEBUG)  # Print traceback at debug level
        import traceback

        info(traceback.format_exc(), Verbosity.DEBUG)
        return 1

    # Check available metric files
    info("\nAvailable metrics:")
    available_count = 0
    total_count = 0

    for metric in MetricFile:
        total_count += 1
        try:
            metric_file = metric.value.get_file(reader.interop_dir)
            info(f"✓ {metric.name}")
            available_count += 1
            info(f"  -> {metric_file.name}", Verbosity.VERBOSE)
        except FileNotFoundError:
            info(f"✗ {metric.name} (missing)")

    info(f"\nSummary: {available_count}/{total_count} metrics available")

    if available_count == 0:
        error("\n✗ No metrics found in InterOp directory")
        return 1

    info(f"\n✓ Run directory is valid and ready for analysis")
    return 0
