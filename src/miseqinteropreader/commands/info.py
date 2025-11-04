"""Info command - display run information and quick statistics."""

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
    """Add arguments for the info command."""
    parser.add_argument(
        "run_dir",
        type=Path,
        help="Path to the MiSeq run directory",
    )
    add_verbosity_arguments(parser)


def execute(args: argparse.Namespace) -> int:
    """Execute the info command."""
    configure_verbosity(args)
    run_dir = args.run_dir

    try:
        reader = InterOpReader(run_dir)
    except Exception as e:
        error(f"Error: Failed to read run directory: {e}")
        return 1

    # Display basic run information
    info(f"Run: {reader.run_name}")

    # Display status
    status_parts = []
    if reader.qc_uploaded:
        status_parts.append("QC Uploaded")
    if reader.needsprocessing:
        status_parts.append("Needs Processing")
    status = ", ".join(status_parts) if status_parts else "No status markers"
    info(f"Status: {status}")

    # Count available metrics
    available_metrics = []
    for metric in MetricFile:
        try:
            metric.value.get_file(reader.interop_dir)
            available_metrics.append(metric)
        except FileNotFoundError:
            pass

    info(f"Metrics available: {len(available_metrics)}/{len(MetricFile)}")

    # Get quick stats from available metrics
    total_records = 0
    lanes = set()
    tiles = set()
    cycles = set()

    for metric in available_metrics:
        if metric == MetricFile.SUMMARY_RUN:
            continue  # No read method for this one

        try:
            records = reader.read_file(metric)
            total_records += len(records)

            # Collect lane, tile, cycle info if available
            for record in records:
                if hasattr(record, "lane"):
                    lanes.add(record.lane)
                if hasattr(record, "tile"):
                    tiles.add(record.tile)
                if hasattr(record, "cycle"):
                    cycles.add(record.cycle)
        except Exception:
            # Skip metrics that fail to read
            continue

    info(f"Total records: {total_records:,}")

    if lanes:
        info(f"Lanes: {len(lanes)} (range: {min(lanes)}-{max(lanes)})")
    if tiles:
        info(f"Tiles: {len(tiles)}")
    if cycles:
        info(f"Cycles: {len(cycles)} (max: {max(cycles)})")

    # List available metric files
    info("\nAvailable metric files:", Verbosity.VERBOSE)
    for metric in available_metrics:
        try:
            metric_file = metric.value.get_file(reader.interop_dir)
            file_size = metric_file.stat().st_size
            info(
                f"  • {metric.name}: {metric_file.name} ({file_size:,} bytes)",
                Verbosity.VERBOSE,
            )
        except FileNotFoundError:
            pass

    return 0
