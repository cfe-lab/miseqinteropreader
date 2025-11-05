# Miseq Binary Parser

![coverage report](https://codecov.io/gh/cfe-lab/miseqinteropreader/graph/badge.svg?token=IFVA5WNVXF)

This module is built to replace the [Illuminate](https://github.com/nthmost/illuminate) package, which has not seen an update in over 7 years.

The foundation of this code is based on the [MiCall](https://github.com/cfe-lab/MiCall) project's [Error Metrics Parser](https://github.com/cfe-lab/MiCall/blob/master/micall/monitor/error_metrics_parser.py), [Quality Metrics Parser](https://github.com/cfe-lab/MiCall/blob/master/micall/monitor/quality_metrics_parser.py), and [Tile Metrics Parser](https://github.com/cfe-lab/MiCall/blob/master/micall/monitor/tile_metrics_parser.py).

For an indepth breakdown of binary formats used, see the [Illumina binary formats](https://illumina.github.io/interop/binary_formats.html) page.

## Installation

```bash
pip install miseqinteropreader
```

Or with uv:

```bash
uv add miseqinteropreader
```

For development, clone the repository and install with dev dependencies:

```bash
git clone <repository-url>
cd miseqinteropreader
uv sync --all-extras
```

## Command-Line Interface

The package includes a powerful CLI tool called `miseq-interop` for analyzing MiSeq InterOp metrics without writing code.

### Available Commands

#### `validate` - Validate Run Directory

Check if a run directory is valid and see which metrics are available:

```bash
miseq-interop validate /path/to/run

# Example output:
# ✓ Run directory exists: 240101_M12345_0001_000000000-ABCDE
# ✓ InterOp directory found
# ✓ SampleSheet.csv found
# ✓ Marker: needsprocessing
# ✓ Marker: qc_uploaded
#
# Available metrics:
# ✓ ERROR_METRICS
# ✓ QUALITY_METRICS
# ✓ TILE_METRICS
# ✗ COLLAPSED_Q_METRICS (missing)
```

#### `info` - Display Run Information

Show quick statistics and metadata about a run:

```bash
miseq-interop info /path/to/run

# Example output:
# Run: 240101_M12345_0001_000000000-ABCDE
# Status: QC Uploaded, Needs Processing
# Metrics available: 8/11
# Total records: 45,232
# Lanes: 1 (range: 1-1)
# Tiles: 19
# Cycles: 301 (max: 301)
```

Add `-v` for verbose output with file sizes:

```bash
miseq-interop info /path/to/run -v
```

#### `summary` - Generate Quality Summaries

Generate summary statistics for quality, tiles, and error metrics:

```bash
# Get quality summary (Q30 scores)
miseq-interop summary /path/to/run --quality

# Get tile summary (cluster density, pass rate)
miseq-interop summary /path/to/run --tiles

# Get error rate summary (phiX)
miseq-interop summary /path/to/run --errors

# Get all summaries
miseq-interop summary /path/to/run --all

# Specify read lengths for proper forward/reverse separation
miseq-interop summary /path/to/run --all --read-lengths 150,8,8,150

# Export to JSON
miseq-interop summary /path/to/run --all --format json -o summary.json

# Export to CSV
miseq-interop summary /path/to/run --all --format csv -o summary.csv
```

#### `extract` - Extract Metrics to Files

Export raw metric data to various formats:

```bash
# Extract specific metrics to JSON
miseq-interop extract /path/to/run --metrics ERROR_METRICS QUALITY_METRICS --format json -o output_dir/

# Extract all available metrics to CSV
miseq-interop extract /path/to/run --all --format csv -o metrics/

# Extract to Parquet format (requires pandas)
miseq-interop extract /path/to/run --metrics QUALITY_METRICS --format parquet -o quality.parquet

# Extract single metric to stdout
miseq-interop extract /path/to/run --metrics ERROR_METRICS --format json
```

Available metrics:
- `ERROR_METRICS` - PhiX error rates by cycle
- `QUALITY_METRICS` - Q-score distributions
- `TILE_METRICS` - Cluster density and counts
- `EXTENDED_TILE_METRICS` - Extended tile information
- `EXTRACTION_METRICS` - Focus and intensity metrics
- `IMAGE_METRICS` - Image contrast metrics
- `PHASING_METRICS` - Phasing/prephasing weights
- `CORRECTED_INTENSITY_METRICS` - Corrected intensities
- `COLLAPSED_Q_METRICS` - Collapsed quality bins (Q20/Q30)
- `INDEX_METRICS` - Index read information

### Example Workflows

**QC Pipeline Integration:**
```bash
# Validate run before processing
miseq-interop validate /path/to/run && \
  miseq-interop summary /path/to/run --all --format json -o qc_metrics.json
```

**Quick QC Check:**
```bash
# Get key metrics for a run
miseq-interop info /path/to/run
miseq-interop summary /path/to/run --quality --tiles
```

## Python API

You can also use the package programmatically in Python:

```python
from pathlib import Path
from miseqinteropreader import InterOpReader, MetricFile

# Initialize reader
reader = InterOpReader("/path/to/run")

# Check available files
reader.check_files_present([MetricFile.ERROR_METRICS, MetricFile.QUALITY_METRICS])

# Read metric data
error_records = reader.read_file(MetricFile.ERROR_METRICS)
quality_records = reader.read_file(MetricFile.QUALITY_METRICS)

# Get as pandas DataFrame
error_df = reader.read_file_to_dataframe(MetricFile.ERROR_METRICS)

# Generate summaries
quality_summary = reader.summarize_quality_records(
    quality_records,
    read_lengths=(150, 16, 150)  # forward, indexes, reverse
)

print(f"Q30 Forward: {quality_summary.q30_forward:.2%}")
print(f"Q30 Reverse: {quality_summary.q30_reverse:.2%}")

tile_records = reader.read_file(MetricFile.TILE_METRICS)
tile_summary = reader.summarize_tile_records(tile_records)

print(f"Cluster Density: {tile_summary.cluster_density:.2f} K/mm²")
print(f"Pass Rate: {tile_summary.pass_rate:.2%}")
```

## Development

Run tests:
```bash
uv run pytest
```

Run with coverage:
```bash
uv run pytest --cov=src/miseqinteropreader
```

Run type checking:
```bash
uv run mypy .
```

Run linting:
```bash
uv run ruff check .
```

## License

See LICENSE file for details.
