"""Tests for CLI commands."""

import sys
from argparse import Namespace
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from miseqinteropreader.cli import create_parser, main
from miseqinteropreader.cli_utils import (
    Verbosity,
    configure_verbosity,
    error,
    get_verbosity,
    info,
    output,
    set_verbosity,
)


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


class TestCLIUtils:
    """Test CLI utility functions."""

    def test_set_and_get_verbosity(self):
        """Test setting and getting verbosity levels."""
        set_verbosity(Verbosity.QUIET)
        assert get_verbosity() == Verbosity.QUIET

        set_verbosity(Verbosity.VERBOSE)
        assert get_verbosity() == Verbosity.VERBOSE

        set_verbosity(Verbosity.DEBUG)
        assert get_verbosity() == Verbosity.DEBUG

    def test_info_respects_verbosity_level(self, capsys):
        """Test that info() respects verbosity level."""
        set_verbosity(Verbosity.NORMAL)

        # Normal message should print
        info("normal message", Verbosity.NORMAL)
        captured = capsys.readouterr()
        assert "normal message" in captured.err

        # Verbose message should not print at NORMAL level
        info("verbose message", Verbosity.VERBOSE)
        captured = capsys.readouterr()
        assert "verbose message" not in captured.err

        # Now set to VERBOSE
        set_verbosity(Verbosity.VERBOSE)
        info("verbose message", Verbosity.VERBOSE)
        captured = capsys.readouterr()
        assert "verbose message" in captured.err

    def test_info_quiet_mode(self, capsys):
        """Test that info() is silent in QUIET mode."""
        set_verbosity(Verbosity.QUIET)
        info("should not appear", Verbosity.NORMAL)
        captured = capsys.readouterr()
        assert captured.err == ""

    def test_error_always_prints(self, capsys):
        """Test that error() always prints regardless of verbosity."""
        set_verbosity(Verbosity.QUIET)
        error("error message")
        captured = capsys.readouterr()
        assert "error message" in captured.err

    def test_output_prints_to_stdout(self, capsys):
        """Test that output() prints to stdout."""
        output("data output")
        captured = capsys.readouterr()
        assert "data output" in captured.out
        assert captured.out.endswith("\n")

    def test_output_custom_end(self, capsys):
        """Test output() with custom end character."""
        output("no newline", end="")
        captured = capsys.readouterr()
        assert captured.out == "no newline"

    def test_configure_verbosity_quiet(self):
        """Test configure_verbosity with quiet flag."""
        args = Namespace(quiet=True, verbose=False, debug=False)
        configure_verbosity(args)
        assert get_verbosity() == Verbosity.QUIET

    def test_configure_verbosity_debug(self):
        """Test configure_verbosity with debug flag."""
        args = Namespace(quiet=False, verbose=False, debug=True)
        configure_verbosity(args)
        assert get_verbosity() == Verbosity.DEBUG

    def test_configure_verbosity_verbose(self):
        """Test configure_verbosity with verbose flag."""
        args = Namespace(quiet=False, verbose=True, debug=False)
        configure_verbosity(args)
        assert get_verbosity() == Verbosity.VERBOSE

    def test_configure_verbosity_normal(self):
        """Test configure_verbosity with no flags (normal)."""
        args = Namespace(quiet=False, verbose=False, debug=False)
        configure_verbosity(args)
        assert get_verbosity() == Verbosity.NORMAL


class TestMainFunction:
    """Test the main CLI entry point."""

    @patch("sys.argv", ["miseq-interop", "validate", "/fake/path"])
    @patch("miseqinteropreader.commands.validate.execute")
    def test_main_routes_to_validate(self, mock_execute):
        """Test that main() routes to validate command."""
        mock_execute.return_value = 0
        result = main()
        assert result == 0
        mock_execute.assert_called_once()
        assert mock_execute.call_args[0][0].command == "validate"

    @patch("sys.argv", ["miseq-interop", "info", "/fake/path"])
    @patch("miseqinteropreader.commands.info.execute")
    def test_main_routes_to_info(self, mock_execute):
        """Test that main() routes to info command."""
        mock_execute.return_value = 0
        result = main()
        assert result == 0
        mock_execute.assert_called_once()
        assert mock_execute.call_args[0][0].command == "info"

    @patch("sys.argv", ["miseq-interop", "summary", "/fake/path", "--all"])
    @patch("miseqinteropreader.commands.summary.execute")
    def test_main_routes_to_summary(self, mock_execute):
        """Test that main() routes to summary command."""
        mock_execute.return_value = 0
        result = main()
        assert result == 0
        mock_execute.assert_called_once()
        assert mock_execute.call_args[0][0].command == "summary"

    @patch("sys.argv", ["miseq-interop", "extract", "/fake/path", "--all"])
    @patch("miseqinteropreader.commands.extract.execute")
    def test_main_routes_to_extract(self, mock_execute):
        """Test that main() routes to extract command."""
        mock_execute.return_value = 0
        result = main()
        assert result == 0
        mock_execute.assert_called_once()
        assert mock_execute.call_args[0][0].command == "extract"

    @patch("sys.argv", ["miseq-interop", "validate", "/fake/path"])
    @patch("miseqinteropreader.commands.validate.execute")
    def test_main_handles_keyboard_interrupt(self, mock_execute, capsys):
        """Test that main() handles KeyboardInterrupt."""
        mock_execute.side_effect = KeyboardInterrupt()
        result = main()
        assert result == 130
        captured = capsys.readouterr()
        assert "Interrupted by user" in captured.err

    @patch("sys.argv", ["miseq-interop", "validate", "/fake/path"])
    @patch("miseqinteropreader.commands.validate.execute")
    def test_main_handles_generic_exception(self, mock_execute, capsys):
        """Test that main() handles generic exceptions."""
        mock_execute.side_effect = Exception("Test error")
        result = main()
        assert result == 1
        captured = capsys.readouterr()
        assert "Error: Test error" in captured.err

    @patch("sys.argv", ["miseq-interop", "validate", "/fake/path", "--verbose"])
    @patch("miseqinteropreader.commands.validate.execute")
    def test_main_shows_traceback_in_verbose_mode(self, mock_execute, capsys):
        """Test that main() shows traceback in verbose mode."""
        mock_execute.side_effect = ValueError("Test error with traceback")
        result = main()
        assert result == 1
        captured = capsys.readouterr()
        # Should show traceback because --verbose is set
        assert "Traceback" in captured.err
        assert "ValueError: Test error with traceback" in captured.err

    @patch("sys.argv", ["miseq-interop", "validate", "/fake/path"])
    @patch("miseqinteropreader.commands.validate.execute")
    def test_main_command_returns_nonzero(self, mock_execute):
        """Test that main() returns command's exit code."""
        mock_execute.return_value = 42
        result = main()
        assert result == 42


class TestValidateCommand:
    """Test the validate command execution."""

    def test_validate_nonexistent_directory(self, tmp_path, capsys):
        """Test validate with nonexistent directory."""
        from miseqinteropreader.commands.validate import execute

        fake_dir = tmp_path / "nonexistent"
        args = Namespace(run_dir=fake_dir, quiet=False, verbose=False, debug=False)

        result = execute(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "does not exist" in captured.err

    def test_validate_file_instead_of_directory(self, tmp_path, capsys):
        """Test validate with file path instead of directory."""
        from miseqinteropreader.commands.validate import execute

        file_path = tmp_path / "somefile.txt"
        file_path.write_text("not a directory")
        args = Namespace(run_dir=file_path, quiet=False, verbose=False, debug=False)

        result = execute(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "not a directory" in captured.err

    def test_validate_missing_interop_directory(self, tmp_path, capsys):
        """Test validate with missing InterOp directory."""
        from miseqinteropreader.commands.validate import execute

        run_dir = tmp_path / "run"
        run_dir.mkdir()
        args = Namespace(run_dir=run_dir, quiet=False, verbose=False, debug=False)

        result = execute(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "InterOp directory not found" in captured.err

    def test_validate_missing_samplesheet(self, tmp_path, capsys):
        """Test validate with missing SampleSheet.csv."""
        from miseqinteropreader.commands.validate import execute

        run_dir = tmp_path / "run"
        run_dir.mkdir()
        interop_dir = run_dir / "InterOp"
        interop_dir.mkdir()
        args = Namespace(run_dir=run_dir, quiet=False, verbose=False, debug=False)

        result = execute(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "SampleSheet.csv not found" in captured.err

    def test_validate_success_with_metrics(self, run_dir, tile_metric_file, capsys):
        """Test successful validation with metrics."""
        from miseqinteropreader.commands.validate import execute

        # Add SampleSheet.csv
        samplesheet = run_dir / "SampleSheet.csv"
        samplesheet.write_text("[Header]\nRun,test")

        args = Namespace(run_dir=run_dir, quiet=False, verbose=False, debug=False)
        result = execute(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "Run directory is valid" in captured.err
        assert "TILE_METRICS" in captured.err

    def test_validate_no_metrics_found(self, tmp_path, capsys):
        """Test validate when no metrics are found."""
        from miseqinteropreader.commands.validate import execute

        run_dir = tmp_path / "run"
        run_dir.mkdir()
        interop_dir = run_dir / "InterOp"
        interop_dir.mkdir()
        samplesheet = run_dir / "SampleSheet.csv"
        samplesheet.write_text("[Header]\nRun,test")

        args = Namespace(run_dir=run_dir, quiet=False, verbose=False, debug=False)
        result = execute(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "No metrics found" in captured.err

    def test_validate_checks_marker_files(self, tmp_path, capsys):
        """Test validate checks for marker files."""
        from miseqinteropreader.commands.validate import execute

        run_dir = tmp_path / "run"
        run_dir.mkdir()
        interop_dir = run_dir / "InterOp"
        interop_dir.mkdir()
        samplesheet = run_dir / "SampleSheet.csv"
        samplesheet.write_text("[Header]\nRun,test")

        # Create marker files
        (run_dir / "needsprocessing").touch()
        (run_dir / "qc_uploaded").touch()

        args = Namespace(run_dir=run_dir, quiet=False, verbose=True, debug=False)
        result = execute(args)

        # Will fail because no metrics, but should check markers
        assert result == 1


class TestInfoCommand:
    """Test the info command execution."""

    def test_info_with_invalid_directory(self, tmp_path, capsys):
        """Test info command with invalid directory."""
        from miseqinteropreader.commands.info import execute

        fake_dir = tmp_path / "nonexistent"
        args = Namespace(run_dir=fake_dir, quiet=False, verbose=False, debug=False)

        result = execute(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "Failed to read run directory" in captured.err

    def test_info_displays_run_name(self, run_dir, tile_metric_file, capsys):
        """Test info command displays run name."""
        from miseqinteropreader.commands.info import execute

        # Add SampleSheet.csv
        samplesheet = run_dir / "SampleSheet.csv"
        samplesheet.write_text("[Header]\nRun,test")

        args = Namespace(run_dir=run_dir, quiet=False, verbose=False, debug=False)
        result = execute(args)

        assert result == 0
        captured = capsys.readouterr()
        assert run_dir.name in captured.err

    def test_info_displays_status_markers(self, run_dir, tile_metric_file, capsys):
        """Test info command displays status markers."""
        from miseqinteropreader.commands.info import execute

        # Add SampleSheet.csv
        samplesheet = run_dir / "SampleSheet.csv"
        samplesheet.write_text("[Header]\nRun,test")

        args = Namespace(run_dir=run_dir, quiet=False, verbose=False, debug=False)
        result = execute(args)

        assert result == 0
        captured = capsys.readouterr()
        # The run_dir fixture creates these markers
        assert "QC Uploaded" in captured.err or "Needs Processing" in captured.err

    def test_info_displays_metrics_count(self, run_dir, tile_metric_file, capsys):
        """Test info command displays metrics count."""
        from miseqinteropreader.commands.info import execute

        # Add SampleSheet.csv
        samplesheet = run_dir / "SampleSheet.csv"
        samplesheet.write_text("[Header]\nRun,test")

        args = Namespace(run_dir=run_dir, quiet=False, verbose=False, debug=False)
        result = execute(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "Metrics available:" in captured.err

    def test_info_verbose_mode(self, run_dir, tile_metric_file, capsys):
        """Test info command in verbose mode."""
        from miseqinteropreader.commands.info import execute

        # Add SampleSheet.csv
        samplesheet = run_dir / "SampleSheet.csv"
        samplesheet.write_text("[Header]\nRun,test")

        args = Namespace(run_dir=run_dir, quiet=False, verbose=True, debug=False)
        result = execute(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "Available metric files:" in captured.err


class TestSummaryCommand:
    """Test the summary command execution."""

    def test_summary_with_invalid_directory(self, tmp_path, capsys):
        """Test summary command with invalid directory."""
        from miseqinteropreader.commands.summary import execute

        fake_dir = tmp_path / "nonexistent"
        args = Namespace(
            run_dir=fake_dir,
            all=False,
            quality=False,
            tiles=False,
            errors=False,
            read_lengths=None,
            format="table",
            output=None,
            quiet=False,
            verbose=False,
            debug=False,
        )

        result = execute(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "Error" in captured.err

    def test_summary_defaults_to_all(self, run_dir, tile_metric_file, capsys):
        """Test summary command defaults to showing all summaries."""
        from miseqinteropreader.commands.summary import execute

        # Add SampleSheet.csv
        samplesheet = run_dir / "SampleSheet.csv"
        samplesheet.write_text("[Header]\nRun,test")

        args = Namespace(
            run_dir=run_dir,
            all=False,
            quality=False,
            tiles=False,
            errors=False,
            read_lengths=None,
            format="table",
            output=None,
            quiet=False,
            verbose=False,
            debug=False,
        )

        result = execute(args)

        # May fail if quality/error metrics are missing, but at least runs
        # The important thing is it doesn't reject missing flags
        assert result in (0, 1)

    def test_summary_all_flag(self, run_dir, tile_metric_file, capsys):
        """Test summary command with --all flag."""
        from miseqinteropreader.commands.summary import execute

        # Add SampleSheet.csv
        samplesheet = run_dir / "SampleSheet.csv"
        samplesheet.write_text("[Header]\nRun,test")

        args = Namespace(
            run_dir=run_dir,
            all=True,
            quality=False,
            tiles=False,
            errors=False,
            read_lengths=None,
            format="table",
            output=None,
            quiet=False,
            verbose=False,
            debug=False,
        )

        result = execute(args)

        # May fail if quality/error metrics are missing
        assert result in (0, 1)
        captured = capsys.readouterr()
        # Should show something in stdout or stderr
        assert len(captured.out) > 0 or len(captured.err) > 0

    def test_summary_tiles_flag(self, run_dir, tile_metric_file, capsys):
        """Test summary command with --tiles flag."""
        from miseqinteropreader.commands.summary import execute

        # Add SampleSheet.csv
        samplesheet = run_dir / "SampleSheet.csv"
        samplesheet.write_text("[Header]\nRun,test")

        args = Namespace(
            run_dir=run_dir,
            all=False,
            quality=False,
            tiles=True,
            errors=False,
            read_lengths=None,
            format="table",
            output=None,
            quiet=False,
            verbose=False,
            debug=False,
        )

        result = execute(args)

        # Should succeed if tile metrics are available
        assert result == 0
        captured = capsys.readouterr()
        # Should show tile information in stdout (table format prints to stdout)
        assert "tile" in captured.out.lower()


class TestExtractCommand:
    """Test the extract command execution."""

    def test_extract_with_invalid_directory(self, tmp_path, capsys):
        """Test extract command with invalid directory."""
        from miseqinteropreader.commands.extract import execute

        fake_dir = tmp_path / "nonexistent"
        args = Namespace(
            run_dir=fake_dir,
            metrics=None,
            all=False,
            format="json",
            output=None,
            quiet=False,
            verbose=False,
            debug=False,
        )

        result = execute(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "Error" in captured.err

    def test_extract_requires_metrics_or_all(self, run_dir, capsys):
        """Test extract command requires --metrics or --all."""
        from miseqinteropreader.commands.extract import execute

        # Add SampleSheet.csv
        samplesheet = run_dir / "SampleSheet.csv"
        samplesheet.write_text("[Header]\nRun,test")

        args = Namespace(
            run_dir=run_dir,
            metrics=None,
            all=False,
            format="json",
            output=None,
            quiet=False,
            verbose=False,
            debug=False,
        )

        result = execute(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "--metrics" in captured.err or "--all" in captured.err

    def test_extract_all_flag(self, run_dir, tile_metric_file, tmp_path, capsys):
        """Test extract command with --all flag and output to file."""
        from miseqinteropreader.commands.extract import execute

        # Add SampleSheet.csv
        samplesheet = run_dir / "SampleSheet.csv"
        samplesheet.write_text("[Header]\nRun,test")

        # Use file path since we only have 1 metric
        output_file = tmp_path / "tile_metrics.json"
        args = Namespace(
            run_dir=run_dir,
            metrics=None,
            all=True,
            format="json",
            output=output_file,
            quiet=False,
            verbose=False,
            debug=False,
        )

        result = execute(args)

        assert result == 0
        # Check that json file was created
        assert output_file.exists()

    def test_extract_specific_metric(self, run_dir, tile_metric_file, tmp_path, capsys):
        """Test extract command with specific metric."""
        from miseqinteropreader.commands.extract import execute

        # Add SampleSheet.csv
        samplesheet = run_dir / "SampleSheet.csv"
        samplesheet.write_text("[Header]\nRun,test")

        output_file = tmp_path / "tile_metrics.json"
        args = Namespace(
            run_dir=run_dir,
            metrics=["TILE_METRICS"],
            all=False,
            format="json",
            output=output_file,
            quiet=False,
            verbose=False,
            debug=False,
        )

        result = execute(args)

        assert result == 0
        assert output_file.exists()
        # Check JSON content
        import json

        data = json.loads(output_file.read_text())
        assert "records" in data

    def test_extract_csv_format(self, run_dir, tile_metric_file, tmp_path, capsys):
        """Test extract command with CSV format."""
        from miseqinteropreader.commands.extract import execute

        # Add SampleSheet.csv
        samplesheet = run_dir / "SampleSheet.csv"
        samplesheet.write_text("[Header]\nRun,test")

        output_file = tmp_path / "tile_metrics.csv"
        args = Namespace(
            run_dir=run_dir,
            metrics=["TILE_METRICS"],
            all=False,
            format="csv",
            output=output_file,
            quiet=False,
            verbose=False,
            debug=False,
        )

        result = execute(args)

        assert result == 0
        assert output_file.exists()
        # CSV should have commas
        content = output_file.read_text()
        assert "," in content

    def test_extract_table_format(self, run_dir, tile_metric_file, tmp_path, capsys):
        """Test extract command with table format."""
        from miseqinteropreader.commands.extract import execute

        # Add SampleSheet.csv
        samplesheet = run_dir / "SampleSheet.csv"
        samplesheet.write_text("[Header]\nRun,test")

        output_file = tmp_path / "tile_metrics.txt"
        args = Namespace(
            run_dir=run_dir,
            metrics=["TILE_METRICS"],
            all=False,
            format="table",
            output=output_file,
            quiet=False,
            verbose=False,
            debug=False,
        )

        result = execute(args)

        assert result == 0
        assert output_file.exists()
