"""Core MD5 computation logic with multi-threading support."""

import hashlib
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, List, Optional, Tuple

from tqdm import tqdm

CHUNK_SIZE = 64 * 1024  # 64 KB


def compute_md5(file_path: Path) -> str:
    """Compute MD5 hex digest of a single file.

    Reads the file in 64 KB chunks to handle large files efficiently.
    """
    h = hashlib.md5()
    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(CHUNK_SIZE)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _collect_files(directory: Path, recursive: bool = True) -> List[Path]:
    """Recursively or non-recursively collect all regular files in a directory."""
    if not directory.is_dir():
        raise NotADirectoryError(f"{directory} is not a directory")

    if recursive:
        # sorted for deterministic output ordering
        files = sorted(
            p for p in directory.rglob("*") if p.is_file()
        )
    else:
        files = sorted(
            p for p in directory.iterdir() if p.is_file()
        )
    return files


@dataclass
class Md5Entry:
    """Represents a single line in an md5sum-format file."""
    expected_hash: str
    filepath: str          # relative path as stored in the md5 file
    full_path: Optional[Path] = None   # resolved after base dir is known

    def __post_init__(self):
        self.expected_hash = self.expected_hash.strip().lower()


@dataclass
class VerifyResult:
    """Result of verifying a single file's MD5."""
    filepath: str
    status: str            # "OK" | "FAILED" | "MISSING"
    expected: str
    actual: str = ""


def parse_md5_file(md5_path: Path, base_dir: Path) -> List[Md5Entry]:
    """Parse a standard md5sum file.

    Format per line:  <32-char-hex>  <filename>
    Lines starting with '#' are comments; blank lines are skipped.
    """
    entries: List[Md5Entry] = []
    with open(md5_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # md5sum format:  <hash>  <filename>
            parts = line.split(None, 1)
            if len(parts) != 2:
                continue
            hash_str, rel_path = parts
            if len(hash_str) != 32:
                continue
            full = (base_dir / rel_path).resolve()
            entries.append(Md5Entry(
                expected_hash=hash_str,
                filepath=rel_path,
                full_path=full,
            ))
    return entries


def generate_hashes(
    paths: List[Path],
    num_threads: int,
    *,
    desc: str = "Generating MD5",
    unit: str = "file",
) -> Iterator[Tuple[Path, str]]:
    """Compute MD5 for each file path using a thread pool.

    Yields ``(path, hex_digest)`` tuples as they complete.
    """
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        fut_to_path = {
            executor.submit(compute_md5, p): p
            for p in paths
        }
        with tqdm(total=len(fut_to_path), desc=desc, unit=unit) as pbar:
            for future in as_completed(fut_to_path):
                path = fut_to_path[future]
                try:
                    digest = future.result()
                except Exception as exc:
                    digest = f"ERROR: {exc}"
                yield path, digest
                pbar.update(1)


def generate_directory(
    directory: Path,
    num_threads: int,
    *,
    recursive: bool = True,
    output: Optional[Path] = None,
) -> None:
    """Generate MD5 hashes for all files in a directory.

    Writes to *output* if given, otherwise prints to stdout.
    The format is standard md5sum: ``<hash>  <relpath>``

    Results are sorted alphabetically by path before output so the
    result is deterministic regardless of thread scheduling.
    """
    files = _collect_files(directory, recursive=recursive)
    if not files:
        print("No files found.")
        return

    results: List[Tuple[Path, str]] = []
    for path, digest in generate_hashes(files, num_threads):
        results.append((path, digest))

    # sort by relative path for deterministic output
    results.sort(key=lambda x: x[0])

    lines: List[str] = []
    for path, digest in results:
        rel = path.relative_to(directory).as_posix()
        lines.append(f"{digest}  {rel}")

    output_lines = "\n".join(lines)
    if output:
        output.write_text(output_lines + "\n", encoding="utf-8")
        print(f"MD5 checksums written to {output}")
    else:
        print(output_lines)


def verify_hashes(
    entries: List[Md5Entry],
    num_threads: int,
    *,
    desc: str = "Verifying MD5",
    unit: str = "file",
) -> Iterator[VerifyResult]:
    """Verify each Md5Entry against its file on disk.

    Yields ``VerifyResult`` objects as each file completes.
    """
    def _verify_one(entry: Md5Entry) -> VerifyResult:
        if entry.full_path is None or not entry.full_path.is_file():
            return VerifyResult(
                filepath=entry.filepath,
                status="MISSING",
                expected=entry.expected_hash,
            )
        try:
            actual = compute_md5(entry.full_path)
        except Exception as exc:
            return VerifyResult(
                filepath=entry.filepath,
                status="FAILED",
                expected=entry.expected_hash,
                actual=str(exc),
            )
        status = "OK" if actual == entry.expected_hash else "FAILED"
        return VerifyResult(
            filepath=entry.filepath,
            status=status,
            expected=entry.expected_hash,
            actual=actual,
        )

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = {executor.submit(_verify_one, e): e for e in entries}
        with tqdm(total=len(futures), desc=desc, unit=unit) as pbar:
            for future in as_completed(futures):
                result = future.result()
                yield result
                pbar.update(1)


def verify_directory(
    md5_file: Path,
    base_dir: Path,
    num_threads: int,
) -> None:
    """Verify files listed in an md5sum file against their checksums.

    Base directory for relative paths is *base_dir* (usually the
    directory containing the md5 file).  Prints a summary: OK / FAILED
    / MISSING counts, and details for non-OK results.
    """
    entries = parse_md5_file(md5_file, base_dir)
    if not entries:
        print("No valid MD5 entries found in", md5_file)
        return

    ok_count = 0
    failed: List[VerifyResult] = []
    missing: List[VerifyResult] = []

    for result in verify_hashes(entries, num_threads):
        if result.status == "OK":
            ok_count += 1
        elif result.status == "FAILED":
            failed.append(result)
        else:
            missing.append(result)

    # Print summary
    total = len(entries)
    print(f"\n{'='*50}")
    print(f"Verification complete: {total} file(s)")
    print(f"  OK:      {ok_count}")
    print(f"  FAILED:  {len(failed)}")
    print(f"  MISSING: {len(missing)}")
    print(f"{'='*50}")

    if failed:
        print("\n--- FAILED ---")
        for r in failed:
            print(f"  {r.filepath}")
            print(f"    expected: {r.expected}")
            print(f"    actual:   {r.actual}")

    if missing:
        print("\n--- MISSING ---")
        for r in missing:
            print(f"  {r.filepath}")
