import os
import platform


def get_binary_path():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.normpath(os.path.join(current_dir, "../libs", get_file_name()))


def get_file_name():
    os_name = platform.system().lower()
    machine = platform.machine().lower()
    file_name = "libzen_internals_"

    if "arm64" in machine or "aarch64" in machine:
        file_name += "aarch64-"
    elif "x86_64" in machine or "amd64" in machine:
        file_name += "x86_64-"

    if os_name == "windows":
        file_name += "pc-windows-gnu.dll"
    elif os_name == "darwin":
        file_name += "apple-darwin.dylib"
    elif os_name in ["linux", "linux2"]:
        file_name += "unknown-linux-gnu.so"

    return file_name
