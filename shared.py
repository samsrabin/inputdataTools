"""
Things shared between rimport and relink
"""

import logging
from argparse import ArgumentParser

DEFAULT_INPUTDATA_ROOT = "/glade/campaign/cesm/cesmdata/cseg/inputdata/"
DEFAULT_STAGING_ROOT = (
    "/glade/campaign/collections/gdex/data/d651077/cesmdata/inputdata/"
)


def get_log_level(quiet: bool = False, verbose: bool = False) -> int:
    """Determine logging level based on quiet and verbose flags.

    Args:
        quiet: If True, show only warnings and errors (WARNING level).
        verbose: If True, show debug messages (DEBUG level).

    Returns:
        int: Logging level (DEBUG, INFO, or WARNING).

    Note:
        If both quiet and verbose are True, quiet takes precedence.
    """
    if quiet:
        return logging.WARNING
    if verbose:
        return logging.DEBUG
    return logging.INFO


def add_parser_verbosity_group(parser: ArgumentParser):
    """Add mutually exclusive verbosity options to an argument parser.

    Adds -v/--verbose and -q/--quiet flags as a mutually exclusive group.

    Args:
        parser: ArgumentParser instance to add the verbosity group to.

    Returns:
        The mutually exclusive argument group that was created.
    """
    verbosity_group = parser.add_mutually_exclusive_group()
    verbosity_group.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose output (DEBUG level)"
    )
    verbosity_group.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Quiet mode (show only warnings and errors)",
    )
    return verbosity_group
