"""Command-line interface for miseq-interop."""

import argparse
import sys
from pathlib import Path

from .commands import extract, info, summary, validate


def create_parser() -> argparse.ArgumentParser:
    """Create the main argument parser."""
    parser = argparse.ArgumentParser(
        prog="miseq-interop",
        description="CLI tool for analyzing MiSeq InterOp metrics",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0",
    )

    # Create subparsers for commands
    subparsers = parser.add_subparsers(
        dest="command",
        help="Available commands",
        required=True,
    )

    # Validate command
    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate run directory structure and check available metrics",
    )
    validate.add_arguments(validate_parser)

    # Info command
    info_parser = subparsers.add_parser(
        "info",
        help="Display run information and quick statistics",
    )
    info.add_arguments(info_parser)

    # Summary command
    summary_parser = subparsers.add_parser(
        "summary",
        help="Generate summary statistics for quality, tiles, and errors",
    )
    summary.add_arguments(summary_parser)

    # Extract command
    extract_parser = subparsers.add_parser(
        "extract",
        help="Extract metrics to various output formats",
    )
    extract.add_arguments(extract_parser)

    return parser


def main() -> int:
    """Main entry point for the CLI."""
    parser = create_parser()
    args = parser.parse_args()

    try:
        # Route to appropriate command handler
        if args.command == "validate":
            return validate.execute(args)
        elif args.command == "info":
            return info.execute(args)
        elif args.command == "summary":
            return summary.execute(args)
        elif args.command == "extract":
            return extract.execute(args)
        else:
            parser.print_help()
            return 1
    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if hasattr(args, "verbose") and args.verbose:
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__": sys.exit(main())
