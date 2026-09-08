from aikido_zen.vulnerabilities.attack_wave_detection.paths import (
    file_names,
    directory_names,
)

file_extensions = {
    "env",
    "bak",
    "sql",
    "sqlite",
    "sqlite3",
    "db",
    "old",
    "save",
    "orig",
    "sqlitedb",
    "sqlite3db",
}

# Extensions that belong to other platforms (e.g. PHP, Java).
# A 200 response may mean the Python app is proxying to that backend,
# so we only count these as scan hits when the response is 404.
foreign_extensions = {
    "php",
    "php3",
    "php4",
    "php5",
    "phtml",
    "java",
    "jsp",
    "jspx",
}

filenames = {name.lower() for name in file_names}
directories = {name.lower() for name in directory_names}


def is_web_scan_path(path: str, status_code: int = 404) -> bool:
    """
    is_web_scan_path gets the current route and wants to determine whether it's a test by some web scanner.
    Checks filename if it exists (list of suspicious filenames & list of supsicious extensions)
    Checks all other segments for suspicious directories
    Foreign-platform extensions (php, jsp, etc.) are only counted when status_code is 404.
    """
    normalized = path.lower()
    segments = normalized.split("/")
    if not segments:
        return False

    filename = segments[-1]
    if filename:
        if filename in filenames:
            return True

        if "." in filename:
            ext = filename.split(".")[-1]
            if ext in file_extensions:
                return True
            if ext in foreign_extensions and status_code == 404:
                return True

    for directory in segments:
        if directory in directories:
            return True
    return False
