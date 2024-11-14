import pytest
from unittest.mock import patch
import aikido_zen.sinks.os_system
import aikido_zen.sinks.subprocess

kind = "shell_injection"
op = "os.system"


def test_osdotsystem_commands():
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        import os

        os.system("Test command")
        args = ("Test command",)
        mock_run_vulnerability_scan.assert_called_with(kind=kind, op=op, args=args)

        os.system("")
        args = ("",)
        mock_run_vulnerability_scan.assert_called_with(kind=kind, op=op, args=args)

        os.system("ls -la | grep 'test'")
        args = ("ls -la | grep 'test'",)
        mock_run_vulnerability_scan.assert_called_with(kind=kind, op=op, args=args)


def test_osdotsystem_invalid_input():
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        import os

        with pytest.raises(TypeError):
            os.system()
        mock_run_vulnerability_scan.assert_not_called()

        with pytest.raises(TypeError):
            os.system(123456789123456789)
        mock_run_vulnerability_scan.assert_not_called()  # Ensure it was not called

        with pytest.raises(TypeError):
            os.system(None)
        mock_run_vulnerability_scan.assert_not_called()  # Ensure it was not called

        with pytest.raises(TypeError):
            os.system(["list", "of", "commands"])
        mock_run_vulnerability_scan.assert_not_called()  # Ensure it was not called

        # Test dictionary command
        with pytest.raises(TypeError):
            os.system({"key": "value"})
        mock_run_vulnerability_scan.assert_not_called()  # Ensure it was not called

        # Test float command
        with pytest.raises(TypeError):
            os.system(3.14)
        mock_run_vulnerability_scan.assert_not_called()  # Ensure it was not called

        # Test boolean command
        with pytest.raises(TypeError):
            os.system(True)
        mock_run_vulnerability_scan.assert_not_called()  # Ensure it was not called

        # Test tuple command
        with pytest.raises(TypeError):
            os.system(("tuple", "command"))
        mock_run_vulnerability_scan.assert_not_called()  # Ensure it was not called


def test_osdotpopen_commands():
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        import os

        os.popen("Test command")

        args = ("Test command",)
        mock_run_vulnerability_scan.assert_any_call(
            kind=kind, op="subprocess.Popen", args=args
        )

        os.popen("ls -la | grep 'test'")
        args = ("ls -la | grep 'test'",)
        mock_run_vulnerability_scan.assert_any_call(
            kind=kind, op="subprocess.Popen", args=args
        )
