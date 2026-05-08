"""Command-line interface for md5check."""

import argparse
import os
import sys
from pathlib import Path
from typing import List, Optional

from md5check import __version__
from md5check.core import generate_directory, verify_directory


def _positive_int(value: str) -> int:
    """Argument type validator for positive integers."""
    try:
        n = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"invalid integer: {value!r}")
    if n < 1:
        raise argparse.ArgumentTypeError(f"must be >= 1, got {n}")
    return n


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    parser = argparse.ArgumentParser(
        prog="md5check",
        description="Multi-threaded MD5 checksum generator and verifier.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  md5check generate ./myfiles -j 4 -o checksums.md5\n"
            "  md5check check checksums.md5 -j 4\n"
        ),
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    # --- generate ---
    gen = sub.add_parser(
        "generate",
        aliases=["gen"],
        help="Generate MD5 checksums for all files in a directory",
        description=(
            "Scan a directory and compute MD5 checksums for every file "
            "using multiple threads."
        ),
    )
    gen.add_argument(
        "directory",
        type=Path,
        help="Directory to scan",
    )
    gen.add_argument(
        "-o", "--output",
        type=Path,
        help="Output file (default: stdout)",
    )
    gen.add_argument(
        "-j", "--jobs",
        type=_positive_int,
        default=os.cpu_count() or 1,
        help=(
            f"Number of worker threads (default: {os.cpu_count() or 1})"
        ),
    )
    gen.add_argument(
        "--no-recursive",
        action="store_true",
        help="Do not scan subdirectories",
    )

    # --- check ---
    chk = sub.add_parser(
        "check",
        help="Verify MD5 checksums from a file",
        description=(
            "Read an md5sum-format file and verify every file's "
            "checksum using multiple threads."
        ),
    )
    chk.add_argument(
        "md5file",
        type=Path,
        help="Path to the md5sum-format file",
    )
    chk.add_argument(
        "-j", "--jobs",
        type=_positive_int,
        default=os.cpu_count() or 1,
        help=(
            f"Number of worker threads (default: {os.cpu_count() or 1})"
        ),
    )
    chk.add_argument(
        "-C", "--directory",
        type=Path,
        default=None,
        help=(
            "Base directory for relative paths in the md5 file. "
            "Defaults to the md5 file's parent directory."
        ),
    )

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """Entry point for the ``md5check`` console script."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command in ("generate", "gen"):
        directory = args.directory.resolve()
        if not directory.is_dir():
            print(f"Error: {directory} is not a directory or does not exist.", file=sys.stderr)
            return 1
        generate_directory(
            directory=directory,
            num_threads=args.jobs,
            recursive=not args.no_recursive,
            output=args.output,
        )
        return 0

    elif args.command == "check":
        md5file = args.md5file.resolve()
        if not md5file.is_file():
            print(f"Error: {md5file} is not a file or does not exist.", file=sys.stderr)
            return 1
        base_dir = (
            args.directory.resolve()
            if args.directory is not None
            else md5file.parent.resolve()
        )
        verify_directory(
            md5_file=md5file,
            base_dir=base_dir,
            num_threads=args.jobs,
        )
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
