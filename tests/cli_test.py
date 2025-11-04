"""Tests for CLI commands."""

from pathlib import Path

import pytest

from miseqinteropreader.cli import create_parser


class TestCLIParser:
    """Test the CLI argument parser."""

    def test_parser_creation(self):
        """Test that the parser can be created."""
        parser = create_parser()
        assert parser is not None
        assert parser.prog == "miseq-interop"

    def test_validate_command(self):
        """Test validate command parsing."""
        parser = create_parser()
        args = parser.parse_args(["validate", "/path/to/run"])
        assert args.command == "validate"
        assert args.run_dir == Path("/path/to/run")

    def test_info_command(self):
        """Test info command parsing."""
        parser = create_parser()
        args = parser.parse_args(["info", "/path/to/run"])
        assert args.command == "info"
        assert args.run_dir == Path("/path/to/run")

    def test_summary_command(self):
        """Test summary command parsing."""
        parser = create_parser()
        args = parser.parse_args(["summary", "/path/to/run", "--all"])
        assert args.command == "summary"
        assert args.run_dir == Path("/path/to/run")
        assert args.all is True

    def test_summary_quality_flag(self):
        """Test summary command with quality flag."""
        parser = create_parser()
        args = parser.parse_args(["summary", "/path/to/run", "--quality"])
        assert args.quality is True

    def test_summary_with_read_lengths(self):
        """Test summary command with read lengths."""
        parser = create_parser()
        args = parser.parse_args(
            ["summary", "/path/to/run", "--read-lengths", "150,8,8,150"]
        )
        assert args.read_lengths == "150,8,8,150"

    def test_extract_command(self):
        """Test extract command parsing."""
        parser = create_parser()
        args = parser.parse_args(
            ["extract", "/path/to/run", "--metrics", "ERROR_METRICS", "QUALITY_METRICS"]
        )
        assert args.command == "extract"
        assert args.run_dir == Path("/path/to/run")
        assert args.metrics == ["ERROR_METRICS", "QUALITY_METRICS"]

    def test_extract_all_flag(self):
        """Test extract command with --all flag."""
        parser = create_parser()
        args = parser.parse_args(["extract", "/path/to/run", "--all"])
        assert args.all is True

    def test_extract_format_option(self):
        """Test extract command with format option."""
        parser = create_parser()
        args = parser.parse_args(
            ["extract", "/path/to/run", "--all", "--format", "csv"]
        )
        assert args.format == "csv"

    def test_list_command(self):
        """Test list command parsing."""
        parser = create_parser()
        args = parser.parse_args(["list", "/path/to/runs"])
        assert args.command == "list"
        assert args.runs_dir == Path("/path/to/runs")

    def test_list_with_filters(self):
        """Test list command with filters."""
        parser = create_parser()
        args = parser.parse_args(
            ["list", "/path/to/runs", "--needs-processing", "--verbose"]
        )
        assert args.needs_processing is True
        assert args.verbose is True

    def test_list_with_pattern(self):
        """Test list command with pattern."""
        parser = create_parser()
        args = parser.parse_args(["list", "/path/to/runs", "--pattern", "2024.*"])
        assert args.pattern == "2024.*"

    def test_no_command_raises_error(self):
        """Test that no command raises an error."""
        parser = create_parser()
        with pytest.raises(SystemExit):
            parser.parse_args([])


class TestValidateCommandModule:
    """Test the validate command module."""

    def test_import_validate_module(self):
        """Test that validate module can be imported."""
        from miseqinteropreader.commands import validate

        assert hasattr(validate, "add_arguments")
        assert hasattr(validate, "execute")


class TestInfoCommandModule:
    """Test the info command module."""

    def test_import_info_module(self):
        """Test that info module can be imported."""
        from miseqinteropreader.commands import info

        assert hasattr(info, "add_arguments")
        assert hasattr(info, "execute")


class TestSummaryCommandModule:
    """Test the summary command module."""

    def test_import_summary_module(self):
        """Test that summary module can be imported."""
        from miseqinteropreader.commands import summary

        assert hasattr(summary, "add_arguments")
        assert hasattr(summary, "execute")

    def test_parse_read_lengths_3_values(self):
        """Test parsing read lengths with 3 values."""
        from miseqinteropreader.commands.summary import parse_read_lengths

        result = parse_read_lengths("150,8,150")
        assert result == (150, 8, 150)

    def test_parse_read_lengths_4_values(self):
        """Test parsing read lengths with 4 values."""
        from miseqinteropreader.commands.summary import parse_read_lengths

        result = parse_read_lengths("150,8,8,150")
        assert result == (150, 16, 150)

    def test_parse_read_lengths_invalid(self):
        """Test parsing invalid read lengths."""
        from miseqinteropreader.commands.summary import parse_read_lengths

        with pytest.raises(ValueError):
            parse_read_lengths("150,8")


class TestExtractCommandModule:
    """Test the extract command module."""

    def test_import_extract_module(self):
        """Test that extract module can be imported."""
        from miseqinteropreader.commands import extract

        assert hasattr(extract, "add_arguments")
        assert hasattr(extract, "execute")


class TestListCommandModule:
    """Test the list command module."""

    def test_import_list_module(self):
        """Test that list module can be imported."""
        from miseqinteropreader.commands import list_runs

        assert hasattr(list_runs, "add_arguments")
        assert hasattr(list_runs, "execute")


class TestFormatters:
    """Test the formatter modules."""

    def test_import_json_formatter(self):
        """Test that json formatter can be imported."""
        from miseqinteropreader.formatters import json_formatter

        assert hasattr(json_formatter, "format_output")

    def test_import_csv_formatter(self):
        """Test that csv formatter can be imported."""
        from miseqinteropreader.formatters import csv_formatter

        assert hasattr(csv_formatter, "format_output")

    def test_import_table_formatter(self):
        """Test that table formatter can be imported."""
        from miseqinteropreader.formatters import table_formatter

        assert hasattr(table_formatter, "format_output")
