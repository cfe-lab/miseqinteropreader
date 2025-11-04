"""Table output formatter for terminal display."""

from typing import Any


def format_output(data: dict[str, Any] | list[dict[str, Any]]) -> None:
    """Format data as a simple table for terminal display.

    Args:
        data: Dictionary or list of dictionaries to format
    """
    if isinstance(data, dict):
        # Single dictionary - format as key-value pairs
        max_key_len = max(len(str(k)) for k in data.keys()) if data else 0
        for key, value in data.items():
            print(f"{str(key).ljust(max_key_len)} : {value}")
    elif isinstance(data, list) and data:
        # List of dictionaries - format as table
        fieldnames = list(data[0].keys())
        
        # Calculate column widths
        col_widths = {
            field: max(len(str(field)), max(len(str(row.get(field, ""))) for row in data))
            for field in fieldnames
        }
        
        # Print header
        header = " | ".join(str(field).ljust(col_widths[field]) for field in fieldnames)
        print(header)
        print("-" * len(header))
        
        # Print rows
        for row in data:
            print(" | ".join(str(row.get(field, "")).ljust(col_widths[field]) for field in fieldnames))
    else:
        print("No data to display")
