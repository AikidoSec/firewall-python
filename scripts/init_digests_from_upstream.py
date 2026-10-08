#!/usr/bin/env python3
"""
Script to initialize binary_digests.txt using upstream .sha256sum files.

This script downloads the .sha256sum files published by the zen-internals release
and uses them to populate binary_digests.txt. While these checksums come from the
same release (and thus don't provide independent assurance against a compromised
publisher), they establish a baseline for verification and are better than no
verification at all.

IMPORTANT: These digests should be independently verified when possible through:
- Reproducible builds
- Multiple independent sources
- Code review of zen-internals
- GPG signature verification
"""

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


def download_checksum(binary_file):
    """Download the .sha256sum file for a binary."""
    url = f"{BASE_URL}/{binary_file}.sha256sum"
    try:
        with urllib.request.urlopen(url) as response:
            content = response.read().decode("utf-8").strip()
            # Format is typically: "<hash>  <filename>" or "<hash> <filename>"
            parts = content.split()
            if len(parts) >= 1:
                return parts[0]  # Return just the hash
            return None
    except Exception as e:
        print(
            f"ERROR: Failed to download checksum for {binary_file}: {e}",
            file=sys.stderr,
        )
        return None


def main():
    print(f"Downloading upstream checksums from {BASE_URL}")
    print("=" * 70)

    digests = []
    failed = []

    for binary_file in BINARY_FILES:
        print(f"Fetching checksum for {binary_file}...")
        digest = download_checksum(binary_file)
        if digest:
            digests.append((digest, binary_file))
            print(f"  SHA256: {digest}")
        else:
            failed.append(binary_file)
            print(f"  FAILED")

    if failed:
        print("\n" + "=" * 70)
        print("ERROR: Failed to download checksums for:")
        for binary_file in failed:
            print(f"  - {binary_file}")
        print("\nCannot initialize binary_digests.txt")
        sys.exit(1)

    print("\n" + "=" * 70)
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
            "# IMPORTANT: These digests were initialized from upstream .sha256sum files.\n"
            "# While this provides a baseline for verification, these checksums come from\n"
            "# the same release and do not provide independent assurance against a\n"
            "# compromised release publisher.\n"
            "#\n"
            "# For stronger assurance, consider:\n"
            "# - Verifying through reproducible builds\n"
            "# - Comparing with digests from multiple independent sources\n"
            "# - Reviewing zen-internals source code\n"
            "# - Verifying GPG signatures if available\n"
        )
        f.write("\n")
        f.write(
            "# When upgrading zen-internals version:\n"
            "# 1. Update BASE_URL in Makefile and scripts/compute_binary_digests.py\n"
            "# 2. Verify the release authenticity (GPG signature, release notes, security advisory)\n"
            "# 3. Run: python3 scripts/compute_binary_digests.py\n"
            "# 4. Review and commit the updated digests\n"
        )
        f.write("\n")

        for digest, filename in digests:
            f.write(f"{digest}  {filename}\n")

    print(f"\nDigests written to {digest_file}")
    print("\nIMPORTANT:")
    print("- These digests were sourced from upstream .sha256sum files")
    print(
        "- They provide a baseline but should be independently verified when possible"
    )
    print("- Review the digests before committing")
    print(
        f"- Check release notes: https://github.com/AikidoSec/zen-internals/releases/tag/v0.1.60"
    )


if __name__ == "__main__":
    main()
