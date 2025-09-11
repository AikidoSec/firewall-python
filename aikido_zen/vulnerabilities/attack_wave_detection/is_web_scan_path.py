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
filenames = {name.lower() for name in file_names}
directories = {name.lower() for name in directory_names}


def is_web_scan_path(path: str) -> bool:
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

    # Check all directory names
    segments_without_filename = segments[:-1]
    for directory in segments_without_filename:
        if directory in directories:
            return True
    return False
