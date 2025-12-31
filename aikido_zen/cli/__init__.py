import sys
import subprocess
from typing import List

import aikido_zen


def run_command(args: List[str]) -> int:
    """
    Run the provided command as a subprocess.
    """
    if not args:
        print("Error: No command provided.", file=sys.stderr)
        return 1

    try:
        # Run the command as a subprocess
        result = subprocess.run(args, check=False)
        return result.returncode
    except KeyboardInterrupt:
        print("\nCommand interrupted by user.", file=sys.stderr)
        return 130  # SIGINT exit code
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

def main() -> int:
    """
    Entry point for aikido_zen cli tool.
    """
    if len(sys.argv) < 2:
        print("Usage: aikido_zen <command> [args...]", file=sys.stderr)
        return 1

    # Start background process
    aikido_zen.protect(mode="daemon_only")

    # The command to run is everything after `aikido_zen`
    command = sys.argv[1:]
    status = run_command(command)

    return status

if __name__ == "__main__":
    sys.exit(main())
