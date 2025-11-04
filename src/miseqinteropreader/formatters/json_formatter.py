"""JSON output formatter."""

import json
import sys
from pathlib import Path
from typing import Any


def format_output(data: Any, output_file: str | Path | None = None) -> None:
    """Format data as JSON and write to file or stdout.

    Args:
        data: Data to format (must be JSON-serializable)
        output_file: Output file path, or None for stdout
    """
    json_str = json.dumps(data, indent=2, default=str)

    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json_str)
    else:
        print(json_str)
