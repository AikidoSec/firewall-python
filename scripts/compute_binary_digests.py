#!/usr/bin/env python3
"""
Script to download zen-internals binaries and compute their SHA256 digests.
This script should be run by a trusted maintainer when updating binary versions.

The script downloads binaries, computes their digests, and also downloads the
upstream .sha256sum files for comparison. The maintainer should independently
verify the binaries before committing the digests.
"""

import hashlib
import sys
import urllib.request
from pathlib import Path

BASE_URL = "https://github.com/AikidoSec/zen-internals/releases/download/v0.1.60"
BINARY_FILES = [
    "libzen_internals_aarch64-apple-darwin.dylib",
    "libzen_internals_aarch64-unknown-linux-gnu.so",
    "libzen_internals_x86_64-apple-darwin.dylib",
    "libzen_internals_x86_64-pc-windows-gnu.dll",
    "libzen_internals_x86_64-unknown-linux-gnu.so",
]


def compute_sha256(file_path):
    """Compute SHA256 digest of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def download_file(url, dest_path):
    """Download a file from URL to destination path."""
    print(f"Downloading {dest_path.name}...")
    try:
        urllib.request.urlretrieve(url, dest_path)
        return True
    except Exception as e:
        print(f"ERROR: Failed to download {url}: {e}", file=sys.stderr)
        return False


def main():
    # Create temporary directory for downloads
    temp_dir = Path(".cache/binaries_temp")
    temp_dir.mkdir(parents=True, exist_ok=True)

    print(f"Downloading binaries from {BASE_URL}")
    print("=" * 70)

    digests = []
    upstream_checksums = {}

    for binary_file in BINARY_FILES:
        # Download binary
        url = f"{BASE_URL}/{binary_file}"
        dest_path = temp_dir / binary_file

        if not download_file(url, dest_path):
            print("\nERROR: Failed to download all binaries", file=sys.stderr)
            sys.exit(1)

        # Compute digest
        digest = compute_sha256(dest_path)
        digests.append((digest, binary_file))
        print(f"  Computed SHA256: {digest}")

        # Try to download upstream checksum for comparison
        checksum_url = f"{BASE_URL}/{binary_file}.sha256sum"
        checksum_path = temp_dir / f"{binary_file}.sha256sum"
        if download_file(checksum_url, checksum_path):
            try:
                with open(checksum_path, "r", encoding="utf-8") as f:
                    upstream_checksum = f.read().strip().split()[0]
                    upstream_checksums[binary_file] = upstream_checksum
                    print(f"  Upstream SHA256:  {upstream_checksum}")
                    if digest == upstream_checksum:
                        print("  ✓ Checksums match")
                    else:
                        print("  ✗ WARNING: Checksums DO NOT match!")
            except Exception as e:
                print(f"  Warning: Could not read upstream checksum: {e}")
        print()

    print("=" * 70)
    print("Writing digests to binary_digests.txt")

    # Write digest file
    digest_file = Path("binary_digests.txt")
    with open(digest_file, "w", encoding="utf-8") as f:
        f.write("# Trusted SHA256 digests for zen-internals v0.1.60 binaries\n")
        f.write("# Format: <sha256> <filename>\n")
        f.write(
            "# These digests are independently verified and committed to the repository\n"
        )
        f.write("# Any mismatch will cause the build to fail\n")
        f.write("\n")
        f.write(
            "# When upgrading zen-internals version:\n"
            "# 1. Update BASE_URL in Makefile and this script to point to the new release\n"
            "# 2. Verify the release authenticity (GPG signature, release notes, security advisory)\n"
            "# 3. Run: python3 scripts/compute_binary_digests.py\n"
            "# 4. Review and commit the updated digests\n"
        )
        f.write("\n")

        for digest, filename in digests:
            f.write(f"{digest}  {filename}\n")

    print(f"\nDigests written to {digest_file}")
    print("\nIMPORTANT SECURITY VERIFICATION STEPS:")
    print("1. Review the digests above")
    print("2. Verify the upstream release is authentic:")
    print(
        f"   - Check release notes at: https://github.com/AikidoSec/zen-internals/releases/tag/v0.1.60"
    )
    print("   - Verify GPG signatures if available")
    print("   - Check for security advisories")
    print("3. If upstream checksums matched, this provides some assurance")
    print(
        "4. Consider additional verification methods (code review, reproducible builds)"
    )
    print("5. Commit the digest file with a clear audit trail")

    # Clean up
    import shutil

    shutil.rmtree(temp_dir)


if __name__ == "__main__":
    main()
