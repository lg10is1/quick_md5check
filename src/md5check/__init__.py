"""md5check: Multi-threaded MD5 checksum generator and verifier."""

__version__ = "1.0.0"

from md5check.core import (
    compute_md5,
    generate_hashes,
    generate_directory,
    parse_md5_file,
    verify_directory,
    verify_hashes,
)

__all__ = [
    "compute_md5",
    "generate_hashes",
    "generate_directory",
    "parse_md5_file",
    "verify_directory",
    "verify_hashes",
]
