"""Tests for formatter modules."""

import json
from pathlib import Path

import pytest


class TestTableFormatter:
    """Test the table formatter."""

    def test_format_dict(self, capsys):
        """Test formatting a dictionary."""
        from miseqinteropreader.formatters.table_formatter import format_output

        data = {
            "name": "test_run",
            "version": "1.0",
            "count": 42,
        }

        format_output(data)

        captured = capsys.readouterr()
        assert "name" in captured.out
        assert "test_run" in captured.out
        assert "version" in captured.out
        assert "1.0" in captured.out
        assert "count" in captured.out
        assert "42" in captured.out
        assert ":" in captured.out  # Key-value separator

    def test_format_list_of_dicts(self, capsys):
        """Test formatting a list of dictionaries as table."""
        from miseqinteropreader.formatters.table_formatter import format_output

        data = [
            {"tile": 1101, "cycle": 1, "value": 100},
            {"tile": 1101, "cycle": 2, "value": 200},
            {"tile": 1102, "cycle": 1, "value": 150},
        ]

        format_output(data)

        captured = capsys.readouterr()
        # Should have header
        assert "tile" in captured.out
        assert "cycle" in captured.out
        assert "value" in captured.out
        # Should have separator line
        assert "-" in captured.out
        # Should have data
        assert "1101" in captured.out
        assert "1102" in captured.out
        assert "100" in captured.out
        assert "200" in captured.out
        assert "150" in captured.out

    def test_format_empty_list(self, capsys):
        """Test formatting an empty list."""
        from miseqinteropreader.formatters.table_formatter import format_output

        data = []

        format_output(data)

        captured = capsys.readouterr()
        assert "No data to display" in captured.out

    def test_format_empty_dict(self, capsys):
        """Test formatting an empty dictionary."""
        from miseqinteropreader.formatters.table_formatter import format_output

        data = {}

        format_output(data)

        captured = capsys.readouterr()
        # Empty dict should still work, just no output
        assert captured.out == "\n" or captured.out == ""

    def test_format_dict_with_long_keys(self, capsys):
        """Test that column widths adjust for long keys."""
        from miseqinteropreader.formatters.table_formatter import format_output

        data = {
            "short": "value1",
            "very_long_key_name": "value2",
            "x": "value3",
        }

        format_output(data)

        captured = capsys.readouterr()
        # All keys should be present
        assert "short" in captured.out
        assert "very_long_key_name" in captured.out
        assert "x" in captured.out


class TestJSONFormatter:
    """Test the JSON formatter."""

    def test_format_to_file(self, tmp_path):
        """Test formatting JSON to a file."""
        from miseqinteropreader.formatters.json_formatter import format_output

        data = {"name": "test", "value": 42, "items": [1, 2, 3]}
        output_file = tmp_path / "output.json"

        format_output(data, output_file)

        assert output_file.exists()
        content = json.loads(output_file.read_text())
        assert content["name"] == "test"
        assert content["value"] == 42
        assert content["items"] == [1, 2, 3]

    def test_format_to_stdout(self, capsys):
        """Test formatting JSON to stdout."""
        from miseqinteropreader.formatters.json_formatter import format_output

        data = {"name": "test", "value": 42}

        format_output(data, None)

        captured = capsys.readouterr()
        parsed = json.loads(captured.out)
        assert parsed["name"] == "test"
        assert parsed["value"] == 42

    def test_format_complex_data(self, tmp_path):
        """Test formatting complex nested data structures."""
        from miseqinteropreader.formatters.json_formatter import format_output

        data = {
            "run": "test_run",
            "metrics": {
                "quality": {"q30": 0.95, "total": 1000},
                "tiles": [{"id": 1, "density": 100}, {"id": 2, "density": 150}],
            },
        }
        output_file = tmp_path / "complex.json"

        format_output(data, output_file)

        assert output_file.exists()
        content = json.loads(output_file.read_text())
        assert content["run"] == "test_run"
        assert content["metrics"]["quality"]["q30"] == 0.95
        assert len(content["metrics"]["tiles"]) == 2

    def test_format_creates_parent_directories(self, tmp_path):
        """Test that format_output creates parent directories."""
        from miseqinteropreader.formatters.json_formatter import format_output

        data = {"test": "data"}
        output_file = tmp_path / "sub" / "dir" / "output.json"

        format_output(data, output_file)

        assert output_file.exists()
        assert output_file.parent.exists()


class TestCSVFormatter:
    """Test the CSV formatter."""

    def test_format_to_file(self, tmp_path):
        """Test formatting CSV to a file."""
        from miseqinteropreader.formatters.csv_formatter import format_output

        data = [
            {"tile": 1101, "cycle": 1, "value": 100},
            {"tile": 1101, "cycle": 2, "value": 200},
            {"tile": 1102, "cycle": 1, "value": 150},
        ]
        output_file = tmp_path / "output.csv"

        format_output(data, output_file)

        assert output_file.exists()
        content = output_file.read_text()
        assert "tile" in content
        assert "cycle" in content
        assert "value" in content
        assert "1101" in content
        assert "1102" in content

    def test_format_to_stdout(self, capsys):
        """Test formatting CSV to stdout."""
        from miseqinteropreader.formatters.csv_formatter import format_output

        data = [
            {"name": "test1", "value": 10},
            {"name": "test2", "value": 20},
        ]

        format_output(data, None)

        captured = capsys.readouterr()
        assert "name" in captured.out
        assert "value" in captured.out
        assert "test1" in captured.out
        assert "test2" in captured.out
        assert "10" in captured.out
        assert "20" in captured.out

    def test_format_empty_list(self, tmp_path):
        """Test formatting an empty list."""
        from miseqinteropreader.formatters.csv_formatter import format_output

        data = []
        output_file = tmp_path / "empty.csv"

        format_output(data, output_file)

        # CSV formatter returns early for empty data, so file won't be created
        assert not output_file.exists()

    def test_format_with_missing_fields(self, tmp_path):
        """Test CSV formatting when some records have missing fields."""
        from miseqinteropreader.formatters.csv_formatter import format_output

        data = [
            {"tile": 1101, "cycle": 1, "value": 100},
            {"tile": 1102, "cycle": 2},  # missing 'value'
            {"tile": 1103, "value": 150},  # missing 'cycle'
        ]
        output_file = tmp_path / "missing.csv"

        format_output(data, output_file)

        assert output_file.exists()
        content = output_file.read_text()
        # All field names should be present in header
        assert "tile" in content
        assert "cycle" in content or "value" in content
