"""Tests for extract command edge cases and additional formats."""

import argparse
import json
from pathlib import Path

import pandas as pd

from miseqinteropreader.commands import extract


class TestExtractParquetFormat:
    """Tests for parquet format extraction."""

    def test_extract_single_metric_parquet(
        self, run_dir, tile_metric_file, tmp_path, capsys
    ):
        """Test extracting a single metric in parquet format."""
        # Create SampleSheet.csv
        sample_sheet = run_dir / "SampleSheet.csv"
        sample_sheet.write_text("[Header]\nInvestigatorName,Test\n")

        output_file = tmp_path / "tile_metrics.parquet"
        args = argparse.Namespace(
            run_dir=run_dir,
            metrics=["TILE_METRICS"],
            all=False,
            format="parquet",
            output=output_file,
            verbosity=0,
            quiet=False,
            debug=False,
            verbose=False,
        )

        result = extract.execute(args)
        assert result == 0
        assert output_file.exists()

        # Verify parquet file
        df = pd.read_parquet(output_file)
        assert len(df) > 0
        assert "lane" in df.columns
        assert "tile" in df.columns

    def test_extract_multiple_metrics_parquet(
        self,
        run_dir,
        tile_metric_file,
        error_metric_file,
        quality_metric_file,
        tmp_path,
        capsys,
    ):
        """Test extracting multiple metrics in parquet format to a directory."""
        # Create SampleSheet.csv
        sample_sheet = run_dir / "SampleSheet.csv"
        sample_sheet.write_text("[Header]\nInvestigatorName,Test\n")

        output_dir = tmp_path / "parquet_output"
        args = argparse.Namespace(
            run_dir=run_dir,
            metrics=["TILE_METRICS", "ERROR_METRICS"],
            all=False,
            format="parquet",
            output=output_dir,
            verbosity=0,
            quiet=False,
            debug=False,
            verbose=False,
        )

        result = extract.execute(args)
        assert result == 0

        # Check that both files were created
        tile_file = output_dir / "tile_metrics.parquet"
        error_file = output_dir / "error_metrics.parquet"
        assert tile_file.exists()
        assert error_file.exists()

        # Verify parquet files
        tile_df = pd.read_parquet(tile_file)
        error_df = pd.read_parquet(error_file)
        assert len(tile_df) > 0
        assert len(error_df) > 0


class TestExtractMultipleMetrics:
    """Tests for extracting multiple metrics to files/directories."""

    def test_extract_multiple_metrics_csv_to_directory(
        self, run_dir, tile_metric_file, error_metric_file, tmp_path, capsys
    ):
        """Test extracting multiple metrics in CSV format to a directory."""
        # Create SampleSheet.csv
        sample_sheet = run_dir / "SampleSheet.csv"
        sample_sheet.write_text("[Header]\nInvestigatorName,Test\n")

        output_dir = tmp_path / "csv_output"
        args = argparse.Namespace(
            run_dir=run_dir,
            metrics=["TILE_METRICS", "ERROR_METRICS"],
            all=False,
            format="csv",
            output=output_dir,
            verbosity=0,
            quiet=False,
            debug=False,
            verbose=False,
        )

        result = extract.execute(args)
        assert result == 0

        # Check that both files were created
        tile_file = output_dir / "tile_metrics.csv"
        error_file = output_dir / "error_metrics.csv"
        assert tile_file.exists()
        assert error_file.exists()

        # Verify CSV content
        tile_content = tile_file.read_text()
        assert "lane" in tile_content
        assert "tile" in tile_content

    def test_extract_multiple_metrics_json_to_directory(
        self, run_dir, tile_metric_file, error_metric_file, tmp_path, capsys
    ):
        """Test extracting multiple metrics in JSON format to a directory."""
        # Create SampleSheet.csv
        sample_sheet = run_dir / "SampleSheet.csv"
        sample_sheet.write_text("[Header]\nInvestigatorName,Test\n")

        output_dir = tmp_path / "json_output"
        args = argparse.Namespace(
            run_dir=run_dir,
            metrics=["TILE_METRICS", "ERROR_METRICS"],
            all=False,
            format="json",
            output=output_dir,
            verbosity=0,
            quiet=False,
            debug=False,
            verbose=False,
        )

        result = extract.execute(args)
        assert result == 0

        # Check that both files were created
        tile_file = output_dir / "tile_metrics.json"
        error_file = output_dir / "error_metrics.json"
        assert tile_file.exists()
        assert error_file.exists()

        # Verify JSON content
        with tile_file.open() as f:
            tile_data = json.load(f)
        assert "records" in tile_data
        assert len(tile_data["records"]) > 0

    def test_extract_multiple_metrics_without_output_requires_output(
        self, run_dir, tile_metric_file, error_metric_file, capsys
    ):
        """Test that extracting multiple metrics without output path fails."""
        # Create SampleSheet.csv
        sample_sheet = run_dir / "SampleSheet.csv"
        sample_sheet.write_text("[Header]\nInvestigatorName,Test\n")

        args = argparse.Namespace(
            run_dir=run_dir,
            metrics=["TILE_METRICS", "ERROR_METRICS"],
            all=False,
            format="json",
            output=None,
            verbosity=0,
            quiet=False,
            debug=False,
            verbose=False,
        )

        result = extract.execute(args)
        assert result == 1

        captured = capsys.readouterr()
        assert "Output path required" in captured.err

    def test_extract_all_with_empty_records_skips_file(
        self, run_dir, tmp_path, capsys, monkeypatch
    ):
        """Test that metrics with no records are skipped."""
        # Create SampleSheet.csv
        sample_sheet = run_dir / "SampleSheet.csv"
        sample_sheet.write_text("[Header]\nInvestigatorName,Test\n")

        # Create an empty TileMetricsOut.bin file (header only, no records)
        interop_dir = run_dir / "InterOp"
        tile_file = interop_dir / "TileMetricsOut.bin"
        # Write a valid header but no records
        with tile_file.open("wb") as f:
            f.write(b"\x02")  # Version
            f.write(b"\x0a")  # Record size

        output_dir = tmp_path / "output"
        args = argparse.Namespace(
            run_dir=run_dir,
            metrics=None,
            all=True,
            format="json",
            output=output_dir,
            verbosity=2,  # Verbose to see skip messages
            quiet=False,
            debug=False,
            verbose=False,
        )

        result = extract.execute(args)
        # Should succeed but not create files for empty metrics
        assert result == 0


class TestExtractEdgeCases:
    """Tests for edge cases in extract command."""

    def test_extract_metric_not_found_with_all_flag_skips(
        self, run_dir, tile_metric_file, tmp_path, capsys
    ):
        """Test that --all flag skips metrics that aren't found."""
        # Create SampleSheet.csv
        sample_sheet = run_dir / "SampleSheet.csv"
        sample_sheet.write_text("[Header]\nInvestigatorName,Test\n")

        output_file = tmp_path / "output.json"
        args = argparse.Namespace(
            run_dir=run_dir,
            metrics=None,
            all=True,
            format="json",
            output=output_file,
            verbosity=2,  # Verbose mode
            quiet=False,
            debug=False,
            verbose=True,  # Enable verbose to see skipping messages
        )

        result = extract.execute(args)
        assert result == 0

        captured = capsys.readouterr()
        # Should show skipping messages for missing metrics in stderr
        assert "Skipping" in captured.err or "not found" in captured.err.lower()

    def test_extract_specified_metric_not_found_fails(
        self, run_dir, tmp_path, capsys
    ):
        """Test that specifying a missing metric returns error."""
        # Create SampleSheet.csv
        sample_sheet = run_dir / "SampleSheet.csv"
        sample_sheet.write_text("[Header]\nInvestigatorName,Test\n")

        output_file = tmp_path / "output.json"
        args = argparse.Namespace(
            run_dir=run_dir,
            metrics=["QUALITY_METRICS"],  # File doesn't exist
            all=False,
            format="json",
            output=output_file,
            verbosity=0,
            quiet=False,
            debug=False,
            verbose=False,
        )

        result = extract.execute(args)
        assert result == 1

        captured = capsys.readouterr()
        assert "not found" in captured.err

    def test_extract_no_metrics_to_extract_fails(self, run_dir, tmp_path, capsys):
        """Test that having no metrics to extract returns error."""
        # Create SampleSheet.csv but no metric files
        sample_sheet = run_dir / "SampleSheet.csv"
        sample_sheet.write_text("[Header]\nInvestigatorName,Test\n")

        output_file = tmp_path / "output.json"
        args = argparse.Namespace(
            run_dir=run_dir,
            metrics=None,
            all=True,
            format="json",
            output=output_file,
            verbosity=0,
            quiet=False,
            debug=False,
            verbose=False,
        )

        result = extract.execute(args)
        assert result == 1

        captured = capsys.readouterr()
        assert "No metrics to extract" in captured.err
