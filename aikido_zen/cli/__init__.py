import os
import shutil
import sys
import subprocess
from typing import List

import aikido_zen


def add_preload_directory(preload_directory: str):
    """
    Idea here is to load in the code stored in the preload_directory first, Inspired by ddtrace-run:
    https://github.com/DataDog/dd-trace-py/blob/3ad335edd4a032ea53680fefbcc10f8fca0690a0/ddtrace/commands/ddtrace_run.py#L41
    """
    python_path = os.environ.get("PYTHONPATH", "")

    if python_path:
        new_path = "%s%s%s" % (preload_directory, os.path.pathsep, os.environ["PYTHONPATH"])
        os.environ["PYTHONPATH"] = new_path
    else:
        os.environ["PYTHONPATH"] = preload_directory

    print(os.environ["PYTHONPATH"])


def get_executable(command):
    if os.path.isfile(command):
        return command
    return shutil.which(command)

def main() -> int:
    """
    Entry point for aikido_zen cli tool.
    """
    if len(sys.argv) < 2:
        print("Usage: aikido_zen <command> [args...]", file=sys.stderr)
        return 1

    root_dir = os.path.dirname(aikido_zen.__file__)
    preload_directory = os.path.join(root_dir, "cli/preload")
    add_preload_directory(preload_directory)

    # The command to run is everything after `aikido_zen`
    executable = get_executable(sys.argv[1])
    try:
        os.execl(executable, executable, *sys.argv[2:])
    except PermissionError:
        print("aikido_zen: permission error while launching '%s'" % executable)
        return 1
    except Exception:
        print("ddtrace-run: error launching '%s'" % executable)
        raise


if __name__ == "__main__":
    sys.exit(main())
