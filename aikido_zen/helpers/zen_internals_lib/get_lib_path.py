"""Exports get_binary_path"""

import platform
import os


def get_binary_path():
    """Returns an absolute path for Rust binary file"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    lib_path = os.path.join(current_dir, "../../libs", get_file_name())
    return lib_path


def get_file_name():
    """Gives you the file name for the binary based on platform info"""
    os_name = platform.system().lower()
    machine = platform.machine().lower()
    file_name = "libzen_internals_"

    # On macOS, platform.machine() returns "arm64" for Apple Silicon
    # On Linux, platform.machine() returns "aarch64" for ARM64
    if "arm64" in machine or "aarch64" in machine:
        file_name += "aarch64-"
    # On macOS, platform.machine() returns "x86_64" for Intel
    # On Linux, platform.machine() returns "x86_64" for AMD64
    elif "x86_64" in machine or "amd64" in machine:
        file_name += "x86_64-"  # x86_64 or AMD64

    if os_name == "windows":
        file_name += "pc-windows-gnu.dll"  # Windows
    elif os_name == "darwin":
        file_name += "apple-darwin.dylib"  # macOS
    elif os_name in ["linux", "linux2"]:
        file_name += "unknown-linux-gnu.so"  # Linux

    return file_name
