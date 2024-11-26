"""Exports get_binary_path"""

import platform
import os


def get_binary_path():
    """Returns an absolute path for Rust binary file"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    lib_path = os.path.join(current_dir, "../../lib", get_file_name())
    return lib_path


def get_file_name():
    """Gives you the file name for the binary based on platform info"""
    os_name = platform.system().lower()
    architecture = platform.architecture()[0].lower()
    file_name = "libzen_internals_"

    if "aarch64" in architecture:
        file_name += "aarch64-"
    elif "64" in architecture:
        file_name += "x86_64-"

    if os_name == "windows":
        file_name += "pc-windows-gnu.dll"  # Windows
    elif os_name == "darwin":
        file_name += "apple-darwin.dylib"  # macOS
    elif os_name in ["linux", "linux2"]:
        file_name += "unknown-linux-gnu.so"  # Linux

    return file_name
