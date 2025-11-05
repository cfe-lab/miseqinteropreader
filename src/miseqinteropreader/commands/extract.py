"""Extract command - export metrics to various output formats."""

import argparse
from pathlib import Path

from ..cli_utils import (
    Verbosity,
    add_verbosity_arguments,
    configure_verbosity,
    error,
    info,
)
from ..formatters import csv_formatter, json_formatter
from ..interop_reader import InterOpReader, MetricFile


def add_arguments(parser: argparse.ArgumentParser) -> None:
    """Add arguments for the extract command."""
    parser.add_argument(
        "run_dir",
        type=Path,
        help="Path to the MiSeq run directory",
    )
    parser.add_argument(
        "--metrics",
        nargs="+",
        choices=[m.name for m in MetricFile],
        help="Specific metrics to extract (space-separated)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Extract all available metrics",
    )
    parser.add_argument(
        "--format",
        choices=["json", "csv", "parquet"],
        default="json",
        help="Output format (default: json)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output file/directory path (required for multiple metrics)",
    )
    add_verbosity_arguments(parser)


def execute(args: argparse.Namespace) -> int:
    """Execute the extract command."""
    configure_verbosity(args)
    run_dir = args.run_dir

    # Initialize reader
    try:
        reader = InterOpReader(run_dir)
    except Exception as e:
        error(f"Error: Failed to read run directory: {e}")
        return 1

    # Determine which metrics to extract
    metrics_to_extract = []

    if args.all:
        # Get all available metrics
        for metric in MetricFile:
            if metric == MetricFile.SUMMARY_RUN:
                continue  # Skip SUMMARY_RUN as it has no read method
            try:
                metric.value.get_file(reader.interop_dir)
                metrics_to_extract.append(metric)
            except FileNotFoundError:
                info(f"Skipping {metric.name} (not found)", Verbosity.VERBOSE)
    elif args.metrics:
        # Use specified metrics
        for metric_name in args.metrics:
            metric = MetricFile[metric_name]
            if metric == MetricFile.SUMMARY_RUN:
                info(f"Warning: Skipping {metric_name} (no read method available)")
                continue
            try:
                metric.value.get_file(reader.interop_dir)
                metrics_to_extract.append(metric)
            except FileNotFoundError:
                error(f"Error: {metric_name} file not found in {reader.interop_dir}")
                return 1
    else:
        error("Error: Must specify --metrics or --all")
        return 1

    if not metrics_to_extract:
        error("Error: No metrics to extract")
        return 1

    # Check if output is needed for multiple metrics
    if len(metrics_to_extract) > 1 and not args.output:
        error("Error: Output path required when extracting multiple metrics")
        return 1

    # Extract each metric
    for metric in metrics_to_extract:
        try:
            info(f"Extracting {metric.name}...", Verbosity.VERBOSE)

            # Read the metric data
            records = reader.read_file(metric)

            if not records:
                info(f"  Warning: No records found for {metric.name}", Verbosity.VERBOSE)
                continue

            # Convert to appropriate format
            if args.format == "parquet":
                df = reader.read_file_to_dataframe(metric)

                # Determine output path
                if len(metrics_to_extract) == 1 and args.output:
                    output_path = args.output
                else:
                    output_dir = args.output or Path(".")
                    output_dir.mkdir(parents=True, exist_ok=True)
                    output_path = output_dir / f"{metric.name.lower()}.parquet"

                df.to_parquet(output_path, index=False)
                info(f"  ✓ Saved to {output_path} ({len(records)} records)", Verbosity.VERBOSE)

            elif args.format == "csv":
                # Convert records to list of dicts
                csv_data = [record.model_dump() for record in records]

                # Determine output path
                if len(metrics_to_extract) == 1 and args.output:
                    output_path = args.output
                else:
                    output_dir = args.output or Path(".")
                    output_dir.mkdir(parents=True, exist_ok=True)
                    output_path = output_dir / f"{metric.name.lower()}.csv"

                csv_formatter.format_output(csv_data, output_path)
                info(f"  ✓ Saved to {output_path} ({len(records)} records)", Verbosity.VERBOSE)

            else:  # json
                # Convert records to dict with metadata
                json_data = {
                    "run_name": reader.run_name,
                    "metric": metric.name,
                    "record_count": len(records),
                    "records": [record.model_dump() for record in records],
                }

                # Determine output path
                if len(metrics_to_extract) == 1:
                    output_path = args.output
                else:
                    output_dir = args.output or Path(".")
                    output_dir.mkdir(parents=True, exist_ok=True)
                    output_path = output_dir / f"{metric.name.lower()}.json"

                json_formatter.format_output(json_data, output_path)
                info(f"  ✓ Saved to {output_path} ({len(records)} records)", Verbosity.VERBOSE)

        except Exception as e:
            error(f"Error extracting {metric.name}: {e}")
            import traceback

            info(traceback.format_exc(), Verbosity.DEBUG)
            return 1

    info(f"✓ Extracted {len(metrics_to_extract)} metric(s)")

    return 0
