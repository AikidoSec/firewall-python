import subprocess
import sys


def test_postfork_instruments_imported_functions_before_starting_daemon(monkeypatch):
    monkeypatch.delenv("AIKIDO_DISABLE", raising=False)
    script = """
import threading
from unittest.mock import patch

from aikido_zen.background_process import get_comms
from aikido_zen.decorators.uwsgi import postfork

calls = []
threads = threading.enumerate()

with patch("aikido_zen.start_background_process", side_effect=lambda: calls.append("daemon")):
    @postfork
    def start_aikido():
        calls.append("hook")

    from os import system

    assert calls == []
    assert get_comms() is None
    assert threading.enumerate() == threads

    start_aikido()
    assert calls == ["daemon", "hook"]

    with patch("aikido_zen.vulnerabilities.run_vulnerability_scan") as scan:
        system("exit 0")
        scan.assert_called_once_with(
            kind="shell_injection", op="os.system", args=("exit 0",)
        )
"""

    subprocess.run([sys.executable, "-c", script], check=True, timeout=30)
