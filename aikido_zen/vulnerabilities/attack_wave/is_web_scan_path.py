from aikido_zen.vulnerabilities.attack_wave.suspicious_paths import (
    suspicious_file_names,
    suspicious_directory_names,
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
filenames = {name.lower() for name in suspicious_file_names}
directories = {name.lower() for name in suspicious_directory_names}


def is_web_scan_path(path: str) -> bool:
    """
    is_web_scan_path gets the current route and wants to determine whether it's a test by some web scanner.
    Checks filename if it exists (list of suspicious filenames & list of supsicious extensions)
    Checks all other segments for suspicious directories
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

    segments_without_filename = segments[:-1]
    for directory in segments_without_filename:
        if directory in directories:
            return True
    return False
