import hashlib
import sys
from pathlib import Path

binary_dir = Path(sys.argv[1])
manifest = Path(sys.argv[2])
for line in manifest.read_text().splitlines():
    expected, filename = line.split()
    actual = hashlib.sha256((binary_dir / filename).read_bytes()).hexdigest()
    if actual != expected:
        raise SystemExit(f"Checksum mismatch: {filename}")
