import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PLACEHOLDER = "1.0-REPLACE-VERSION"
VERSION_PATTERN = re.compile(r"[0-9][0-9A-Za-z.-]*")


def version_from_tag(tag):
    if tag.startswith("dev-v"):
        version = tag[len("dev-v") :]
    elif tag.startswith("v"):
        version = tag[1:]
    else:
        version = tag
    if VERSION_PATTERN.fullmatch(version) is None:
        sys.exit(f"Error: invalid version '{version}'.")
    return version


def main():
    version = version_from_tag(os.environ.get("RELEASE_VERSION", ""))
    subprocess.run(["poetry", "version", version], cwd=ROOT, check=True)
    config_path = ROOT / "aikido_zen" / "config.py"
    config = config_path.read_text()
    if PLACEHOLDER not in config:
        sys.exit(f"Error: {PLACEHOLDER} not found in {config_path}.")
    config_path.write_text(config.replace(PLACEHOLDER, version))


if __name__ == "__main__":
    main()
