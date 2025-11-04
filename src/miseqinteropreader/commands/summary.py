"""Summary command - generate summary statistics for quality, tiles, and errors."""

import argparse
from pathlib import Path
from typing import Any

from ..cli_utils import (
    Verbosity,
    add_verbosity_arguments,
    configure_verbosity,
    error,
    info,
)
from ..formatters import csv_formatter, json_formatter, table_formatter
from ..interop_reader import InterOpReader, MetricFile
from ..models import ErrorRecord, QualityRecord, TileMetricRecord


def add_arguments(parser: argparse.ArgumentParser) -> None:
    """Add arguments for the summary command."""
    parser.add_argument(
        "run_dir",
        type=Path,
        help="Path to the MiSeq run directory",
    )
    parser.add_argument(
        "--quality",
        action="store_true",
        help="Generate quality summary (Q30 scores)",
    )
    parser.add_argument(
        "--tiles",
        action="store_true",
        help="Generate tile summary (cluster density, pass rate)",
    )
    parser.add_argument(
        "--errors",
        action="store_true",
        help="Generate error rate summary (phiX)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Generate all available summaries",
    )
    parser.add_argument(
        "--read-lengths",
        type=str,
        help="Read lengths as comma-separated values (e.g., '150,8,8,150')",
    )
    parser.add_argument(
        "--format",
        choices=["json", "csv", "table"],
        default="table",
        help="Output format (default: table)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output file path (if not specified, prints to stdout)",
    )
    add_verbosity_arguments(parser)


def parse_read_lengths(read_lengths_str: str) -> tuple[int, int, int]:
    """Parse read lengths string into tuple.

    Args:
        read_lengths_str: Comma-separated read lengths (e.g., '150,8,8,150')

    Returns:
        Tuple of (forward_length, index_length, reverse_length)
    """
    parts = [int(x.strip()) for x in read_lengths_str.split(",")]
    if len(parts) == 3:
        return (parts[0], parts[1], parts[2])
    elif len(parts) == 4:
        # Format: forward, index1, index2, reverse
        return (parts[0], parts[1] + parts[2], parts[3])
    else:
        raise ValueError(
            "Read lengths must be 3 or 4 comma-separated integers (e.g., '150,8,8,150')"
        )


def execute(args: argparse.Namespace) -> int:
    """Execute the summary command."""
    configure_verbosity(args)
    run_dir = args.run_dir

    # Parse read lengths if provided
    read_lengths = None
    if args.read_lengths:
        try:
            read_lengths = parse_read_lengths(args.read_lengths)
        except ValueError as e:
            error(f"Error: {e}")
            return 1

    # Initialize reader
    try:
        reader = InterOpReader(run_dir)
    except Exception as e:
        error(f"Error: Failed to read run directory: {e}")
        return 1

    # Determine which summaries to generate
    generate_quality = args.quality or args.all
    generate_tiles = args.tiles or args.all
    generate_errors = args.errors or args.all

    # If no specific summary requested, show all
    if not (generate_quality or generate_tiles or generate_errors):
        generate_quality = True
        generate_tiles = True
        generate_errors = True

    summary_data: dict[str, Any] = {
        "run_name": reader.run_name,
    }

    # Generate quality summary
    if generate_quality:
        try:
            records: list[QualityRecord] = reader.read_file(MetricFile.QUALITY_METRICS)  # type: ignore
            quality_summary = reader.summarize_quality_records(records, read_lengths)
            summary_data["quality"] = {
                "total_count": quality_summary.total_count,
                "total_reverse": quality_summary.total_reverse,
                "good_count": quality_summary.good_count,
                "good_reverse": quality_summary.good_reverse,
                "q30_forward": round(quality_summary.q30_forward, 4),
                "q30_reverse": round(quality_summary.q30_reverse, 4),
            }
            info(f"✓ Quality summary generated ({len(records)} records)", Verbosity.VERBOSE)
        except FileNotFoundError:
            info("✗ Quality metrics file not found", Verbosity.VERBOSE)
            summary_data["quality"] = None
        except Exception as e:
            error(f"Error generating quality summary: {e}")
            import traceback

            info(traceback.format_exc(), Verbosity.DEBUG)
            summary_data["quality"] = None

    # Generate tile summary
    if generate_tiles:
        try:
            tile_records: list[TileMetricRecord] = reader.read_file(MetricFile.TILE_METRICS)  # type: ignore
            tile_summary = reader.summarize_tile_records(tile_records)
            summary_data["tiles"] = {
                "density_count": tile_summary.density_count,
                "density_sum": round(tile_summary.density_sum, 2),
                "total_clusters": tile_summary.total_clusters,
                "passing_clusters": tile_summary.passing_clusters,
                "cluster_density": round(tile_summary.cluster_density, 2),
                "pass_rate": round(tile_summary.pass_rate, 4),
            }
            info(f"✓ Tile summary generated ({len(tile_records)} records)", Verbosity.VERBOSE)
        except FileNotFoundError:
            info("✗ Tile metrics file not found", Verbosity.VERBOSE)
            summary_data["tiles"] = None
        except Exception as e:
            error(f"Error generating tile summary: {e}")
            import traceback

            info(traceback.format_exc(), Verbosity.DEBUG)
            summary_data["tiles"] = None

    # Generate error summary
    if generate_errors:
        try:
            error_records: list[ErrorRecord] = reader.read_file(MetricFile.ERROR_METRICS)  # type: ignore

            # Calculate error summary manually
            error_sum_forward = 0.0
            error_count_forward = 0
            error_sum_reverse = 0.0
            error_count_reverse = 0

            if read_lengths:
                last_forward_cycle = read_lengths[0]
                first_reverse_cycle = sum(read_lengths[:-1]) + 1

                for record in error_records:
                    if record.cycle <= last_forward_cycle:
                        error_sum_forward += record.error_rate
                        error_count_forward += 1
                    elif record.cycle >= first_reverse_cycle:
                        error_sum_reverse += record.error_rate
                        error_count_reverse += 1
            else:
                # Without read lengths, treat all as forward
                for record in error_records:
                    error_sum_forward += record.error_rate
                    error_count_forward += 1

            error_rate_forward = (
                error_sum_forward / error_count_forward if error_count_forward else 0
            )
            error_rate_reverse = (
                error_sum_reverse / error_count_reverse if error_count_reverse else 0
            )

            summary_data["errors"] = {
                "error_sum_forward": round(error_sum_forward, 4),
                "error_count_forward": error_count_forward,
                "error_sum_reverse": round(error_sum_reverse, 4),
                "error_count_reverse": error_count_reverse,
                "error_rate_forward": round(error_rate_forward, 4),
                "error_rate_reverse": round(error_rate_reverse, 4),
            }
            info(f"✓ Error summary generated ({len(error_records)} records)", Verbosity.VERBOSE)
        except FileNotFoundError:
            info("✗ Error metrics file not found", Verbosity.VERBOSE)
            summary_data["errors"] = None
        except Exception as e:
            error(f"Error generating error summary: {e}")
            import traceback

            info(traceback.format_exc(), Verbosity.DEBUG)
            summary_data["errors"] = None

    # Format and output the summary
    try:
        if args.format == "json":
            json_formatter.format_output(summary_data, args.output)
        elif args.format == "csv":
            # Flatten the summary data for CSV
            csv_data = []
            for category, values in summary_data.items():
                if category == "run_name":
                    continue
                if values is not None:
                    row = {"category": category}
                    row.update(values)
                    csv_data.append(row)
            csv_formatter.format_output(csv_data, args.output)
        else:  # table
            if args.output:
                info(f"Warning: Table format does not support file output, printing to stdout")
            table_formatter.format_output(summary_data)
    except Exception as e:
        error(f"Error formatting output: {e}")
        return 1

    return 0
