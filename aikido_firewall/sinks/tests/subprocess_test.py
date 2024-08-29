import pytest
from unittest.mock import patch
import aikido_firewall.sinks.subprocess

kind = "shell_injection"


def test_subprocess_call():
    with patch(
        "aikido_firewall.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        import subprocess

        op = "subprocess.call"

        subprocess.call(["ls", "-la"], shell=True)
        args = ("ls -la",)
        mock_run_vulnerability_scan.assert_called_with(kind=kind, op=op, args=args)

        subprocess.call(["cfsknflks"], shell=True)
        args = ("cfsknflks",)
        mock_run_vulnerability_scan.assert_called_with(kind=kind, op=op, args=args)


def test_subprocess_run():
    with patch(
        "aikido_firewall.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        import subprocess

        op = "subprocess.run"

        subprocess.run(["ls", "-la"], shell=True)
        args = ("ls -la",)
        mock_run_vulnerability_scan.assert_called_with(kind=kind, op=op, args=args)

        subprocess.run(["cfsknflks"], shell=True)
        args = ("cfsknflks",)
        mock_run_vulnerability_scan.assert_called_with(kind=kind, op=op, args=args)


def test_subprocess_check_call():
    with patch(
        "aikido_firewall.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        import subprocess

        op = "subprocess.check_call"

        subprocess.check_call(["ls", "-la"], shell=True)
        args = ("ls -la",)
        mock_run_vulnerability_scan.assert_called_with(kind=kind, op=op, args=args)

        with pytest.raises(subprocess.CalledProcessError):
            subprocess.check_call(["cfsknflks"], shell=True)
        args = ("cfsknflks",)
        mock_run_vulnerability_scan.assert_called_with(kind=kind, op=op, args=args)


def test_subprocess_popen():
    with patch(
        "aikido_firewall.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        import subprocess

        op = "subprocess.Popen"

        subprocess.Popen(["ls", "-la"], shell=True)
        args = ("ls -la",)
        mock_run_vulnerability_scan.assert_called_with(kind=kind, op=op, args=args)

        subprocess.Popen(["cfsknflks"], shell=True)
        args = ("cfsknflks",)
        mock_run_vulnerability_scan.assert_called_with(kind=kind, op=op, args=args)


def test_subprocess_check_output():
    with patch(
        "aikido_firewall.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        import subprocess

        op = "subprocess.check_output"

        subprocess.check_output(["ls", "-la"], shell=True)
        args = ("ls -la",)
        mock_run_vulnerability_scan.assert_called_with(kind=kind, op=op, args=args)

        with pytest.raises(subprocess.CalledProcessError):
            subprocess.check_output(["cfsknflks"], shell=True)
        args = ("cfsknflks",)
        mock_run_vulnerability_scan.assert_called_with(kind=kind, op=op, args=args)

        with pytest.raises(subprocess.CalledProcessError):
            subprocess.check_output(("tuple", "command"), shell=True)
        args = ("tuple command",)
        mock_run_vulnerability_scan.assert_called_with(kind=kind, op=op, args=args)

        with pytest.raises(subprocess.CalledProcessError):
            subprocess.check_output({"key": "value"}, shell=True)
        args = ("key",)
        mock_run_vulnerability_scan.assert_called_with(kind=kind, op=op, args=args)

        with pytest.raises(subprocess.CalledProcessError):
            subprocess.check_output({"ke": "value", "key2": "value2"}, shell=True)
        args = ("ke key2",)
        mock_run_vulnerability_scan.assert_called_with(kind=kind, op=op, args=args)


def test_subprocess_invalid_input():
    with patch(
        "aikido_firewall.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        import subprocess

        op = "subprocess.call"
        with pytest.raises(TypeError):
            subprocess.call(shell=True)
        mock_run_vulnerability_scan.assert_not_called()

        with pytest.raises(TypeError):
            subprocess.call(123456789123456789, shell=True)
        mock_run_vulnerability_scan.assert_not_called()  # Ensure it was not called

        with pytest.raises(TypeError):
            subprocess.call(None, shell=True)
        mock_run_vulnerability_scan.assert_not_called()  # Ensure it was not called

        # Test float command
        with pytest.raises(TypeError):
            subprocess.call(3.14, shell=True)
        mock_run_vulnerability_scan.assert_not_called()  # Ensure it was not called

        # Test boolean command
        with pytest.raises(TypeError):
            subprocess.call(True, shell=True)
        mock_run_vulnerability_scan.assert_not_called()  # Ensure it was not called
