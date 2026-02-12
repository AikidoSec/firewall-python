"""
Mainly exports `parse_as_file_url`
"""

from urllib.parse import urlparse, urlunparse
from pathlib import Path


def parse_as_file_url(path):
    """Convert a file path as a URL to a file path."""
    if path.startswith("file:"):
        parsed_url = urlparse(path)
        file_path = Path(parsed_url.path)
    else:
        if not path.startswith("/"):
            path = f"/{path}"
        file_path = Path(path)
        file_url = urlunparse(("file", "", str(file_path), "", "", ""))
        parsed_url = urlparse(file_url)

    normalized_path = Path(parsed_url.path).resolve()

    return str(normalized_path)
