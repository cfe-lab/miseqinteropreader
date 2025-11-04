"""CSV output formatter."""

import csv
from pathlib import Path
from typing import Any


def format_output(
    data: list[dict[str, Any]], output_file: str | Path | None = None
) -> None:
    """Format data as CSV and write to file or stdout.

    Args:
        data: List of dictionaries to format as CSV rows
        output_file: Output file path, or None for stdout
    """
    if not data:
        return

    # Get all unique keys from all dictionaries
    fieldnames = list(data[0].keys())

    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
    else:
        import sys

        writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
