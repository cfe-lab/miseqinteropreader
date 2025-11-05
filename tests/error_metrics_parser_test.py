"""Tests for error_metrics_parser module."""

import csv
from io import StringIO

import pytest

from miseqinteropreader.error_metrics_parser import write_phix_csv


class TestWritePhixCSV:
    """Test the write_phix_csv function."""

    def test_write_phix_csv_simple(self):
        """Test writing basic phix error rate data."""
        records = [
            {"tile": 1101, "cycle": 1, "error_rate": 0.5},
            {"tile": 1101, "cycle": 2, "error_rate": 0.6},
            {"tile": 1101, "cycle": 3, "error_rate": 0.7},
        ]

        out_file = StringIO()
        result = write_phix_csv(out_file, records)

        # Check output
        output = out_file.getvalue()
        assert "tile,cycle,errorrate" in output
        assert "1101,1,0.5" in output
        assert "1101,2,0.6" in output
        assert "1101,3,0.7" in output

        # Check summary
        assert result.error_sum_forward > 0
        assert result.error_count_forward == 3
        assert result.error_rate_forward > 0

    def test_write_phix_csv_with_read_lengths(self):
        """Test writing phix data with read length specification."""
        records = [
            {"tile": 1101, "cycle": 1, "error_rate": 0.5},
            {"tile": 1101, "cycle": 2, "error_rate": 0.6},
            {"tile": 1101, "cycle": 3, "error_rate": 0.7},
            {"tile": 1101, "cycle": 10, "error_rate": 0.8},  # index - should be skipped
            {"tile": 1101, "cycle": 11, "error_rate": 0.9},  # reverse read
        ]

        # read_lengths: (forward, index, reverse)
        read_lengths = (3, 8, 3)

        out_file = StringIO()
        result = write_phix_csv(out_file, records, read_lengths)

        # Check that forward reads are included
        output = out_file.getvalue()
        assert "1101,1,0.5" in output
        assert "1101,2,0.6" in output
        assert "1101,3,0.7" in output

        # Check summary has both forward and reverse
        assert result.error_sum_forward > 0
        assert result.error_count_forward == 3

    def test_write_phix_csv_missing_cycles(self):
        """Test that missing cycles get blank entries."""
        records = [
            {"tile": 1101, "cycle": 1, "error_rate": 0.5},
            # cycle 2 is missing
            {"tile": 1101, "cycle": 3, "error_rate": 0.7},
        ]

        read_lengths = (3, 0, 0)

        out_file = StringIO()
        result = write_phix_csv(out_file, records, read_lengths)

        output = out_file.getvalue()
        lines = output.strip().split('\n')

        # Should have header + 3 data lines (1, 2 blank, 3)
        assert len(lines) >= 4

        # Check that cycle 2 has blank error rate
        reader = csv.DictReader(StringIO(output))
        rows = list(reader)
        cycle_2_rows = [r for r in rows if r['cycle'] == '2']
        assert len(cycle_2_rows) > 0
        assert cycle_2_rows[0]['errorrate'] == ''

    def test_write_phix_csv_multiple_tiles(self):
        """Test with multiple tiles."""
        records = [
            {"tile": 1101, "cycle": 1, "error_rate": 0.5},
            {"tile": 1101, "cycle": 2, "error_rate": 0.6},
            {"tile": 1102, "cycle": 1, "error_rate": 0.3},
            {"tile": 1102, "cycle": 2, "error_rate": 0.4},
        ]

        out_file = StringIO()
        result = write_phix_csv(out_file, records)

        output = out_file.getvalue()
        assert "1101" in output
        assert "1102" in output

        # All cycles are forward
        assert result.error_count_forward == 4

    def test_write_phix_csv_reverse_reads(self):
        """Test handling of reverse reads with negative cycles."""
        records = [
            {"tile": 1101, "cycle": 1, "error_rate": 0.5},
            {"tile": 1101, "cycle": 2, "error_rate": 0.6},
            {"tile": 1101, "cycle": 11, "error_rate": 0.7},  # reverse read start
            {"tile": 1101, "cycle": 12, "error_rate": 0.8},
        ]

        # forward=2, index=8, reverse=2
        read_lengths = (2, 8, 2)

        out_file = StringIO()
        result = write_phix_csv(out_file, records, read_lengths)

        output = out_file.getvalue()

        # Check forward reads
        assert "1101,1,0.5" in output
        assert "1101,2,0.6" in output

        # Reverse reads should have negative cycles
        assert "-" in output  # Should have negative cycle numbers

        # Check summary
        assert result.error_count_forward == 2
        assert result.error_count_reverse == 2
        assert result.error_rate_reverse > 0

    def test_write_phix_csv_empty_records(self):
        """Test with empty records list."""
        records = []

        out_file = StringIO()
        result = write_phix_csv(out_file, records)

        output = out_file.getvalue()
        assert "tile,cycle,errorrate" in output

        # Summary should be zero
        assert result.error_sum_forward == 0
        assert result.error_count_forward == 0
        assert result.error_rate_forward == 0

    def test_write_phix_csv_rounding(self):
        """Test that error rates are properly rounded to 4 decimal places."""
        records = [
            {"tile": 1101, "cycle": 1, "error_rate": 0.123456789},
            {"tile": 1101, "cycle": 2, "error_rate": 0.987654321},
        ]

        out_file = StringIO()
        result = write_phix_csv(out_file, records)

        output = out_file.getvalue()

        # Check that values are rounded to 4 decimal places
        assert "0.1235" in output  # rounded from 0.123456789
        assert "0.9877" in output  # rounded from 0.987654321
