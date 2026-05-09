# Quick_md5check

Multi-threaded MD5 checksum generator and verifier. Computes and verifies MD5 hashes for many files in parallel — significantly faster than single-threaded `md5sum` on multi-core systems.

## Features

- **Multi-threaded** — configurable thread count via `-j`/`--jobs`
- **Generate mode** — scan a directory and compute MD5 for every file
- **Check mode** — verify files against an `md5sum`-format file
- **Cross-platform** — Windows, Linux, macOS
- **Standard output format** — compatible with GNU `md5sum` and `md5sum -c`
- **Progress bar** — real-time feedback via `tqdm`
- **Recursive scan** — optionally disable with `--no-recursive`

## Installation

### pip
```bash
pip install quick_md5check
```

```

### From source
```bash
git clone https://github.com/lg10is1/quick_md5check.git
cd md5check
pip install -e .
```

## Usage

### Generate checksums
```bash
# Use all available CPU cores
md5check generate ./myfiles -o checksums.md5

# Use 8 worker threads
md5check generate ./myfiles -j 8 -o checksums.md5

# Non-recursive (top-level files only)
md5check generate ./myfiles --no-recursive -o checksums.md5

# Print to stdout
md5check generate ./myfiles
```

### Verify checksums
```bash
# Verify using checksum file, auto-detect base dir
md5check check checksums.md5

# Use 8 worker threads
md5check check checksums.md5 -j 8

# Specify base directory for relative paths
md5check check checksums.md5 -C ./myfiles
```

### Compatible with GNU md5sum
```bash
# Generate (GNU md5sum format)
md5sum myfiles/* > checksums.md5

# Verify with md5check
md5check check checksums.md5

# Generate with md5check, verify with GNU md5sum
md5check generate ./myfiles -o checksums.md5
md5sum -c checksums.md5
```

## Output format

Standard `md5sum` format — one entry per line:

```
d41d8cd98f00b204e9800998ecf8427e  path/to/empty.txt
900150983cd24fb0d6963f7d28e17f72  path/to/hello.txt
```

## Development

### Run from source
```bash
python -m md5check generate ./tests/data -j 4
```

### Build
```bash
# Install build dependencies
pip install build

# Build wheel and source distribution
python -m build
```

## License

MIT
