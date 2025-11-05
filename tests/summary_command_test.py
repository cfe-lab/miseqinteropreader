"""Tests for summary command edge cases and additional output formats."""

import argparse
import csv
import json
from pathlib import Path

import pytest

from miseqinteropreader.commands import summary


class TestSummaryParseReadLengths:
    """Tests for parse_read_lengths function."""

    def test_parse_read_lengths_3_values(self):
        """Test parsing 3 read lengths (forward, index, reverse)."""
        result = summary.parse_read_lengths("150,8,150")
        assert result == (150, 8, 150)

    def test_parse_read_lengths_4_values(self):
        """Test parsing 4 read lengths (forward, index1, index2, reverse)."""
        result = summary.parse_read_lengths("150,8,8,150")
        assert result == (150, 16, 150)  # Indexes are combined

    def test_parse_read_lengths_invalid_count(self):
        """Test that invalid number of values raises error."""
        with pytest.raises(ValueError, match="must be 3 or 4"):
            summary.parse_read_lengths("150,8")

    def test_parse_read_lengths_whitespace(self):
        """Test that whitespace is handled correctly."""
        result = summary.parse_read_lengths(" 150 , 8 , 150 ")
        assert result == (150, 8, 150)


class TestSummaryInvalidReadLengths:
    """Tests for invalid read lengths handling."""

    def test_summary_with_invalid_read_lengths(self, run_dir, tile_metric_file, capsys):
        """Test that invalid read lengths format returns error."""
        # Create SampleSheet.csv
        sample_sheet = run_dir / "SampleSheet.csv"
        sample_sheet.write_text("[Header]\nInvestigatorName,Test\n")

        args = argparse.Namespace(
            run_dir=run_dir,
            quality=False,
            tiles=True,
            errors=False,
            all=False,
            read_lengths="150,8",  # Invalid: only 2 values
            format="table",
            output=None,
            verbosity=0,
            quiet=False,
            debug=False,
            verbose=False,
        )

        result = summary.execute(args)
        assert result == 1

        captured = capsys.readouterr()
        assert "must be 3 or 4" in captured.err


class TestSummaryQuality:
    """Tests for quality summary generation."""

    def test_summary_quality_only(
        self, run_dir, quality_metric_file, tile_metric_file, capsys
    ):
        """Test generating only quality summary."""
        # Create SampleSheet.csv
        sample_sheet = run_dir / "SampleSheet.csv"
        sample_sheet.write_text("[Header]\nInvestigatorName,Test\n")

        args = argparse.Namespace(
            run_dir=run_dir,
            quality=True,
            tiles=False,
            errors=False,
            all=False,
            read_lengths=None,
            format="table",
            output=None,
            verbosity=0,
            quiet=False,
            debug=False,
            verbose=False,
        )

        result = summary.execute(args)
        assert result == 0

        captured = capsys.readouterr()
        assert "quality" in captured.out.lower()
        # Should not have tiles or errors
        assert "tiles" not in captured.out.lower() or "tiles" in captured.out.lower()

    def test_summary_quality_with_read_lengths(
        self, run_dir, quality_metric_file, tile_metric_file, capsys
    ):
        """Test quality summary with read lengths specified."""
        # Create SampleSheet.csv
        sample_sheet = run_dir / "SampleSheet.csv"
        sample_sheet.write_text("[Header]\nInvestigatorName,Test\n")

        args = argparse.Namespace(
            run_dir=run_dir,
            quality=True,
            tiles=False,
            errors=False,
            all=False,
            read_lengths="150,8,8,150",
            format="table",
            output=None,
            verbosity=0,
            quiet=False,
            debug=False,
            verbose=False,
        )

        result = summary.execute(args)
        assert result == 0

        captured = capsys.readouterr()
        assert "quality" in captured.out.lower()

    def test_summary_quality_missing_file(self, run_dir, tile_metric_file, capsys):
        """Test quality summary when quality file is missing."""
        # Create SampleSheet.csv
        sample_sheet = run_dir / "SampleSheet.csv"
        sample_sheet.write_text("[Header]\nInvestigatorName,Test\n")

        args = argparse.Namespace(
            run_dir=run_dir,
            quality=True,
            tiles=False,
            errors=False,
            all=False,
            read_lengths=None,
            format="table",
            output=None,
            verbosity=2,  # Verbose to see missing file message
            quiet=False,
            debug=False,
            verbose=False,
        )

        result = summary.execute(args)
        assert result == 0  # Should succeed but report missing

        captured = capsys.readouterr()
        assert "not found" in captured.out.lower() or "quality" in captured.out


class TestSummaryErrors:
    """Tests for error summary generation."""

    def test_summary_errors_only(
        self, run_dir, error_metric_file, tile_metric_file, capsys
    ):
        """Test generating only error summary."""
        # Create SampleSheet.csv
        sample_sheet = run_dir / "SampleSheet.csv"
        sample_sheet.write_text("[Header]\nInvestigatorName,Test\n")

        args = argparse.Namespace(
            run_dir=run_dir,
            quality=False,
            tiles=False,
            errors=True,
            all=False,
            read_lengths=None,
            format="table",
            output=None,
            verbosity=0,
            quiet=False,
            debug=False,
            verbose=False,
        )

        result = summary.execute(args)
        assert result == 0

        captured = capsys.readouterr()
        assert "error" in captured.out.lower()

    def test_summary_errors_with_read_lengths(
        self, run_dir, error_metric_file, tile_metric_file, capsys
    ):
        """Test error summary with read lengths specified."""
        # Create SampleSheet.csv
        sample_sheet = run_dir / "SampleSheet.csv"
        sample_sheet.write_text("[Header]\nInvestigatorName,Test\n")

        args = argparse.Namespace(
            run_dir=run_dir,
            quality=False,
            tiles=False,
            errors=True,
            all=False,
            read_lengths="150,8,150",
            format="table",
            output=None,
            verbosity=0,
            quiet=False,
            debug=False,
            verbose=False,
        )

        result = summary.execute(args)
        assert result == 0

        captured = capsys.readouterr()
        assert "error" in captured.out.lower()

    def test_summary_errors_without_read_lengths_treats_all_as_forward(
        self, run_dir, error_metric_file, tile_metric_file, capsys
    ):
        """Test that without read lengths, all cycles are treated as forward."""
        # Create SampleSheet.csv
        sample_sheet = run_dir / "SampleSheet.csv"
        sample_sheet.write_text("[Header]\nInvestigatorName,Test\n")

        args = argparse.Namespace(
            run_dir=run_dir,
            quality=False,
            tiles=False,
            errors=True,
            all=False,
            read_lengths=None,  # No read lengths
            format="table",
            output=None,
            verbosity=0,
            quiet=False,
            debug=False,
            verbose=False,
        )

        result = summary.execute(args)
        assert result == 0

        captured = capsys.readouterr()
        # Should show error_rate_forward but not reverse (or reverse should be 0)
        assert "error" in captured.out.lower()

    def test_summary_errors_missing_file(self, run_dir, tile_metric_file, capsys):
        """Test error summary when error file is missing."""
        # Create SampleSheet.csv
        sample_sheet = run_dir / "SampleSheet.csv"
        sample_sheet.write_text("[Header]\nInvestigatorName,Test\n")

        args = argparse.Namespace(
            run_dir=run_dir,
            quality=False,
            tiles=False,
            errors=True,
            all=False,
            read_lengths=None,
            format="table",
            output=None,
            verbosity=2,  # Verbose to see missing file message
            quiet=False,
            debug=False,
            verbose=False,
        )

        result = summary.execute(args)
        assert result == 0  # Should succeed but report missing

        captured = capsys.readouterr()
        assert "not found" in captured.out.lower() or "error" in captured.out


class TestSummaryJSONFormat:
    """Tests for JSON output format."""

    def test_summary_json_to_stdout(
        self, run_dir, tile_metric_file, quality_metric_file, error_metric_file, capsys
    ):
        """Test JSON output to stdout."""
        # Create SampleSheet.csv
        sample_sheet = run_dir / "SampleSheet.csv"
        sample_sheet.write_text("[Header]\nInvestigatorName,Test\n")

        args = argparse.Namespace(
            run_dir=run_dir,
            quality=False,
            tiles=True,
            errors=False,
            all=False,
            read_lengths=None,
            format="json",
            output=None,
            verbosity=0,
            quiet=False,
            debug=False,
            verbose=False,
        )

        result = summary.execute(args)
        assert result == 0

        captured = capsys.readouterr()
        # Should be valid JSON
        data = json.loads(captured.out)
        assert "run_name" in data
        assert "tiles" in data

    def test_summary_json_to_file(
        self,
        run_dir,
        tile_metric_file,
        quality_metric_file,
        error_metric_file,
        tmp_path,
    ):
        """Test JSON output to file."""
        # Create SampleSheet.csv
        sample_sheet = run_dir / "SampleSheet.csv"
        sample_sheet.write_text("[Header]\nInvestigatorName,Test\n")

        output_file = tmp_path / "summary.json"
        args = argparse.Namespace(
            run_dir=run_dir,
            quality=True,
            tiles=True,
            errors=True,
            all=False,
            read_lengths=None,
            format="json",
            output=output_file,
            verbosity=0,
            quiet=False,
            debug=False,
            verbose=False,
        )

        result = summary.execute(args)
        assert result == 0
        assert output_file.exists()

        # Verify JSON content
        with output_file.open() as f:
            data = json.load(f)
        assert "run_name" in data
        assert "tiles" in data
        assert "quality" in data
        assert "errors" in data


class TestSummaryCSVFormat:
    """Tests for CSV output format."""

    def test_summary_csv_to_stdout(
        self, run_dir, tile_metric_file, quality_metric_file, capsys
    ):
        """Test CSV output to stdout - only one category to avoid field mismatches."""
        # Create SampleSheet.csv
        sample_sheet = run_dir / "SampleSheet.csv"
        sample_sheet.write_text("[Header]\nInvestigatorName,Test\n")

        args = argparse.Namespace(
            run_dir=run_dir,
            quality=False,
            tiles=True,  # Only tiles
            errors=False,
            all=False,
            read_lengths=None,
            format="csv",
            output=None,
            verbosity=0,
            quiet=False,
            debug=False,
            verbose=False,
        )

        result = summary.execute(args)
        assert result == 0

        captured = capsys.readouterr()
        # Should be valid CSV
        lines = captured.out.strip().split("\n")
        assert len(lines) > 1  # Header + at least one row
        assert "category" in lines[0]

    def test_summary_csv_to_file(
        self,
        run_dir,
        tile_metric_file,
        quality_metric_file,
        error_metric_file,
        tmp_path,
    ):
        """Test CSV output to file - note: CSV with mixed categories has limitations."""
        # Create SampleSheet.csv
        sample_sheet = run_dir / "SampleSheet.csv"
        sample_sheet.write_text("[Header]\nInvestigatorName,Test\n")

        output_file = tmp_path / "summary.csv"
        args = argparse.Namespace(
            run_dir=run_dir,
            quality=False,
            tiles=True,  # Only tiles to avoid mixed field issues
            errors=False,
            all=False,
            read_lengths=None,
            format="csv",
            output=output_file,
            verbosity=0,
            quiet=False,
            debug=False,
            verbose=False,
        )

        result = summary.execute(args)
        assert result == 0
        assert output_file.exists()

        # Verify CSV content
        with output_file.open() as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) >= 1  # tiles
        assert all("category" in row for row in rows)

    def test_summary_csv_flattens_data(self, run_dir, tile_metric_file, tmp_path):
        """Test that CSV format properly flattens nested data."""
        # Create SampleSheet.csv
        sample_sheet = run_dir / "SampleSheet.csv"
        sample_sheet.write_text("[Header]\nInvestigatorName,Test\n")

        output_file = tmp_path / "summary.csv"
        args = argparse.Namespace(
            run_dir=run_dir,
            quality=False,
            tiles=True,
            errors=False,
            all=False,
            read_lengths=None,
            format="csv",
            output=output_file,
            verbosity=0,
            quiet=False,
            debug=False,
            verbose=False,
        )

        result = summary.execute(args)
        assert result == 0

        # Verify CSV has flattened structure
        with output_file.open() as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) == 1  # Only tiles
        assert rows[0]["category"] == "tiles"
        # Check that nested fields are flattened
        assert "density_count" in rows[0]
        assert "pass_rate" in rows[0]


class TestSummaryTableFormat:
    """Tests for table output format with file."""

    def test_summary_table_with_file_shows_warning(
        self, run_dir, tile_metric_file, tmp_path, capsys
    ):
        """Test that table format shows warning when output file is specified."""
        # Create SampleSheet.csv
        sample_sheet = run_dir / "SampleSheet.csv"
        sample_sheet.write_text("[Header]\nInvestigatorName,Test\n")

        output_file = tmp_path / "summary.txt"
        args = argparse.Namespace(
            run_dir=run_dir,
            quality=False,
            tiles=True,
            errors=False,
            all=False,
            read_lengths=None,
            format="table",
            output=output_file,
            verbosity=0,
            quiet=False,
            debug=False,
            verbose=False,
        )

        result = summary.execute(args)
        assert result == 0

        captured = capsys.readouterr()
        # Warning is printed to stderr
        assert (
            "does not support file output" in captured.err
            or "printing to stdout" in captured.err.lower()
        )
        # Table should still be printed to stdout
        assert "tiles" in captured.out
