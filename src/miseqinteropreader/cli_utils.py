"""CLI utility functions for consistent output handling."""

import sys
from enum import IntEnum
from typing import Optional


class Verbosity(IntEnum):
    """Verbosity levels for CLI output."""

    QUIET = 0
    NORMAL = 1
    VERBOSE = 2
    DEBUG = 3


# Global verbosity level
_verbosity = Verbosity.NORMAL


def set_verbosity(level: Verbosity) -> None:
    """Set the global verbosity level."""
    global _verbosity
    _verbosity = level


def get_verbosity() -> Verbosity:
    """Get the current verbosity level."""
    return _verbosity


def info(message: str, level: Verbosity = Verbosity.NORMAL, end: str = "\n") -> None:
    """Print an informational message to stderr if verbosity allows.

    Args:
        message: The message to print
        level: Minimum verbosity level required to print this message
        end: String appended after the message (default: newline)
    """
    if _verbosity >= level:
        print(message, file=sys.stderr, end=end)


def error(message: str) -> None:
    """Print an error message to stderr (always shown).

    Args:
        message: The error message to print
    """
    print(message, file=sys.stderr)


def output(message: str, end: str = "\n") -> None:
    """Print data output to stdout.

    This is for actual data output (not user messages).

    Args:
        message: The data to print
        end: String appended after the message (default: newline)
    """
    print(message, end=end)


def add_verbosity_arguments(parser) -> None:
    """Add standard verbosity arguments to an argument parser.

    Args:
        parser: The argparse.ArgumentParser to add arguments to
    """
    verbosity_group = parser.add_mutually_exclusive_group()
    verbosity_group.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Minimize output verbosity (errors only)",
    )
    verbosity_group.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Increase output verbosity",
    )
    verbosity_group.add_argument(
        "--no-verbose",
        action="store_true",
        help="Disable verbose output",
        default=True,
    )
    verbosity_group.add_argument(
        "--debug",
        action="store_true",
        help="Maximum output verbosity (debug mode)",
    )


def configure_verbosity(args) -> None:
    """Configure verbosity based on parsed arguments.

    Args:
        args: Namespace from argparse with quiet/verbose/debug flags
    """
    if args.quiet:
        set_verbosity(Verbosity.QUIET)
    elif args.debug:
        set_verbosity(Verbosity.DEBUG)
    elif args.verbose:
        set_verbosity(Verbosity.VERBOSE)
    else:
        set_verbosity(Verbosity.NORMAL)
